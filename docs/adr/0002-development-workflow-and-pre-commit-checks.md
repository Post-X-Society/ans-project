# ADR 0002: Development Workflow and Pre-Commit Checks

## Status
Accepted

## Date
2025-12-20

## Context

During development sprints, we encountered repeated CI failures due to:
1. Code not being formatted with Black before committing
2. Ruff linting errors not caught locally
3. Mypy type errors introduced during development
4. Coverage reports (.cover files) accidentally committed to git

These issues caused PR #35-#39 to fail CI checks multiple times, wasting time and resources despite all tests passing locally.

**Key Problem**: Developers (both human and AI agents) were not running the full linting suite before committing, leading to CI failures that could have been prevented locally.

## Decision

### Mandatory Pre-Commit Workflow

**BEFORE EVERY COMMIT**, developers MUST run the following commands in order:

```bash
cd infrastructure

# 1. Format code with Black
docker compose -f docker-compose.dev.yml run --rm backend black /app

# 2. Fix auto-fixable Ruff issues
docker compose -f docker-compose.dev.yml run --rm backend ruff check /app --fix

# 3. Check for remaining Ruff issues
docker compose -f docker-compose.dev.yml run --rm backend ruff check /app

# 4. Run mypy type checking
docker compose -f docker-compose.dev.yml run --rm backend mypy /app/app/

# 5. Run tests
docker compose -f docker-compose.dev.yml run --rm backend pytest /app/app/tests/
```

**All checks MUST pass** before committing and pushing code.

### Git Ignore Rules

The following files MUST be in `.gitignore`:
```
*.cover
*.pyc
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
coverage.xml
htmlcov/
.coverage
```

## Mypy Type Checking Standards

### Common Type Errors and Fixes

#### 1. Missing Type Parameters

**❌ WRONG:**
```python
from typing import Dict

# Missing type parameters
data: dict = {}
metadata: Dict = {}
```

**✅ CORRECT:**
```python
from typing import Any

# Use Python 3.9+ built-in generics with type parameters
data: dict[str, Any] = {}
metadata: dict[str, int] = {}
```

#### 2. Incompatible Types in Collections

**❌ WRONG:**
```python
# Type error: returning List[User] where List[Claim] expected
users: Sequence[User] = await get_users()
return list(users)  # ← Error if function returns List[Claim]
```

**✅ CORRECT:**
```python
# Ensure the query returns the correct type
claims: Sequence[Claim] = await get_claims()
return list(claims)
```

#### 3. TypeDecorator Missing Type Parameters

**❌ WRONG:**
```python
from sqlalchemy.types import TypeDecorator

class StringList(TypeDecorator):  # ← Missing type parameter
    impl = String
```

**✅ CORRECT:**
```python
from sqlalchemy.types import TypeDecorator

class StringList(TypeDecorator[list[str]]):
    impl = String

    def process_bind_param(
        self, value: list[str] | None, dialect: Any
    ) -> str | None:
        ...
```

#### 4. Untyped Library Imports

For libraries without type stubs (like `python-jose`, `passlib`):

**✅ CORRECT:**
```python
from jose import jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]
```

#### 5. Generator Type Parameters

**❌ WRONG:**
```python
from typing import Generator

@pytest.fixture
def session() -> Generator:  # ← Missing type parameters
    ...
```

**✅ CORRECT:**
```python
from typing import Generator, Any

@pytest.fixture
def session() -> Generator[AsyncSession, None, None]:
    # YieldType, SendType, ReturnType
    ...
```

#### 6. Test Function Type Annotations

**✅ CORRECT:**
```python
from typing import Any

@pytest.mark.asyncio
async def test_something(
    client: TestClient,
    db_session: Any,  # Use Any for complex fixtures
) -> None:  # Always return None for tests
    ...
```

### When to Use `Any`

Use `Any` sparingly, only when:
1. Working with complex third-party libraries without stubs
2. Dynamic data structures from external APIs
3. Test fixtures with complex types
4. Type is truly dynamic and cannot be narrowed

**DO NOT use `Any` to bypass type checking for laziness!**

## Development Commands Reference

### Running Individual Checks

```bash
# Black only
docker compose -f docker-compose.dev.yml run --rm backend black /app

# Ruff only
docker compose -f docker-compose.dev.yml run --rm backend ruff check /app

# Mypy only
docker compose -f docker-compose.dev.yml run --rm backend mypy /app/app/

# Tests only
docker compose -f docker-compose.dev.yml run --rm backend pytest /app/app/tests/
```

### Running All Checks (Simulates CI)

```bash
docker compose -f docker-compose.dev.yml run --rm backend sh -c "
  black --check /app && \
  ruff check /app && \
  mypy /app/app/ && \
  pytest /app/app/tests/
"
```

## Why GitHub CI Still Matters

Even though all tests pass locally, GitHub CI is important because:

1. **Clean Environment**: CI runs in a fresh environment without local caching or state
2. **Exact Python Version**: CI uses the exact Python version specified in workflow
3. **Fresh Dependencies**: CI installs dependencies from scratch, catching version issues
4. **Matrix Testing**: CI can test multiple Python versions/OS combinations
5. **Required Checks**: CI acts as a gatekeeper preventing broken code from merging
6. **Team Synchronization**: CI ensures all team members' code passes the same standards

**Bottom Line**: Local checks are for fast feedback, CI is for final verification before merge.

## Consequences

### Positive
- **Fewer CI Failures**: Issues caught locally before pushing
- **Faster Development**: No waiting for CI to fail, then fix, then wait again
- **Better Code Quality**: Type safety and formatting enforced consistently
- **Clear Process**: Developers know exactly what to run before committing

### Negative
- **Longer Local Dev Time**: Running all checks takes 2-3 minutes
- **Potential Friction**: Developers might skip checks if in a hurry (mitigated by CI)
- **Tool Complexity**: Multiple tools to learn (Black, Ruff, mypy, pytest)

### Neutral
- **CI Still Required**: Local checks don't eliminate need for CI verification
- **Learning Curve**: New developers need to learn the workflow

## Future Improvements

Consider implementing:
1. **Pre-commit hooks**: Automatically run checks on `git commit`
2. **Makefile shortcuts**: `make lint`, `make test`, `make all`
3. **Git hooks**: Prevent commits if checks fail
4. **IDE Integration**: Configure VS Code/PyCharm to run checks on save

## Related ADRs
- [ADR 0001: Python Linting Standards](./0001-python-linting-standards.md)

## References
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/learn-github-actions/best-practices-for-workflows)
