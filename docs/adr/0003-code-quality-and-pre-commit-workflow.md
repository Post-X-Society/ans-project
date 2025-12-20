# ADR 0003: Code Quality and Pre-Commit Workflow

## Status
Accepted

## Date
2025-12-19 (initial), 2025-12-20 (expanded)

## Context

During development sprints for issues #29-#34, all 5 pull requests failed CI/CD checks due to code quality issues:

1. **Black formatting violations**: Code not formatted according to PEP 8 standards
2. **Ruff B904 violations**: Missing exception chaining in exception handlers
3. **Ruff F823 violations**: Duplicate imports causing variable shadowing
4. **Import sorting issues**: Inconsistent import organization
5. **Mypy type errors**: Missing type parameters, incompatible types
6. **Coverage files**: Accidentally committed to git

**Key Problem**: Developers (both human and AI agents) were not running the full linting suite before committing, leading to CI failures that could have been prevented locally. These issues caused significant delays in merging feature branches.

## Decision

We will enforce strict Python code quality standards using Black, Ruff, and mypy, with mandatory pre-commit checks.

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

## Code Quality Standards

### 1. Black Code Formatting

- **All Python code must be formatted with Black** before committing
- Black configuration: Default settings (88 character line length)
- CI will reject any code that fails `black --check`

### 2. Ruff Linting Rules

#### B904: Exception Chaining Required

All exceptions raised within `except` blocks must use proper exception chaining:

**✅ CORRECT:**
```python
try:
    response = await api_call()
except httpx.HTTPStatusError as e:
    raise HTTPException(
        status_code=e.response.status_code,
        detail=f"API error: {e.response.text}",
    ) from e  # ← 'from e' preserves exception context
```

**❌ INCORRECT:**
```python
try:
    response = await api_call()
except httpx.HTTPStatusError as e:
    raise HTTPException(
        status_code=e.response.status_code,
        detail=f"API error: {e.response.text}",
    )  # ← Missing 'from e'
```

**Exception:** Use `from None` to explicitly suppress exception chaining:
```python
except ValueError as e:
    raise HTTPException(
        status_code=400,
        detail="Invalid input"
    ) from None  # Intentionally hide original exception
```

**Bare raise:** When re-raising the same exception, use bare `raise`:
```python
except Exception as e:
    if "specific_error" in str(e):
        raise HTTPException(status_code=400, detail="Handled") from e
    raise  # ← Bare raise preserves original exception
```

#### F823: No Duplicate Imports

Avoid importing the same name multiple times, especially in nested scopes:

**✅ CORRECT:**
```python
# Top of file
from sqlalchemy import func, select

# Later in function
stmt = select(User).where(...)  # Uses module-level import
```

**❌ INCORRECT:**
```python
# Top of file
from sqlalchemy import func, select

# Inside a function
async def my_function():
    from sqlalchemy import select  # ← Duplicate import shadows module-level
    stmt = select(User).where(...)
```

#### I001: Import Organization

- Ruff automatically organizes imports
- Use `ruff check --fix` to auto-sort imports
- Standard order: stdlib → third-party → first-party → local
- Add `# noqa: I001` only when absolutely necessary

### 3. Mypy Type Checking Standards

#### Missing Type Parameters

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

#### TypeDecorator Missing Type Parameters

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

#### Untyped Library Imports

For libraries without type stubs:

```python
from jose import jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]
```

#### Generator Type Parameters

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

#### Test Function Type Annotations

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

#### When to Use `Any`

Use `Any` sparingly, only when:
1. Working with complex third-party libraries without stubs
2. Dynamic data structures from external APIs
3. Test fixtures with complex types
4. Type is truly dynamic and cannot be narrowed

**DO NOT use `Any` to bypass type checking for laziness!**

### 4. Git Ignore Rules

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

## Common Patterns

### FastAPI HTTPException Handling

```python
from fastapi import HTTPException
import httpx

async def fetch_data():
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"External API error: {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Connection failed: {str(e)}"
        ) from e
```

### SQLAlchemy Import Pattern

```python
# Single import at module level
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

# No imports inside functions - use module-level imports
async def get_user(db: AsyncSession, user_id: UUID):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
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

## CI Environment Considerations

### Critical Lesson: Avoid Docker-Specific Hardcoded Paths

Code that works locally in Docker may fail in GitHub Actions CI due to different environments:

**❌ WRONG - Hardcoded Docker path:**
```python
MEDIA_DIR = Path("/app/media/spotlight_videos")  # Fails in CI - no /app directory!
```

**✅ CORRECT - Environment variable with fallback:**
```python
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "/app/media/spotlight_videos"))
```

**Why this matters:**
- **Docker environment**: Code runs at `/app` inside container, has proper permissions
- **GitHub Actions CI**: Code runs in `/home/runner/work/...`, no `/app` directory exists
- **Permission errors**: CI runner cannot create directories in root filesystem

### Required GitHub Actions Environment Variables

Update `.github/workflows/backend-tests.yml` with all necessary environment variables:

```yaml
- name: Run tests with coverage
  working-directory: ./backend
  env:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/ans_test
    RAPIDAPI_KEY: test-key-for-ci
    MEDIA_DIR: /tmp/spotlight_videos  # Use /tmp for CI environment
  run: |
    pytest --cov=app --cov-report=xml --cov-report=term-missing --cov-fail-under=0
```

### Environment Variable Checklist

Before writing code that uses paths or external services:

1. ✅ **Use environment variables** for all configurable paths
2. ✅ **Provide sensible defaults** that work in Docker
3. ✅ **Document required env vars** in README and workflow files
4. ✅ **Test in CI-like environment** - paths work outside Docker
5. ✅ **Use `/tmp`** for CI temporary files (always writable)

### Common CI Environment Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Permission denied: '/app'` | Hardcoded Docker path | Use env var with `/tmp` default for CI |
| `psycopg2 is not async` | Wrong database driver | Use `postgresql+asyncpg://` not `postgresql://` |
| `Environment variable not set` | Missing in workflow | Add to workflow `env:` section |
| `Directory not found` | Assumes Docker structure | Create directories with `mkdir -p` or `exist_ok=True` |

### Testing for CI Compatibility

Run these checks before pushing:

```bash
# 1. Test without Docker environment variables
unset MEDIA_DIR
cd backend
pytest  # Should still work with default values

# 2. Test with /tmp paths (CI-like environment)
export MEDIA_DIR=/tmp/test_media
pytest

# 3. Check for hardcoded paths
grep -r '"/app' backend/app/  # Should only appear in defaults, not hardcoded
```

**Golden Rule**: If it assumes Docker's `/app` directory structure, it will fail in GitHub Actions CI.

## CI/CD Configuration

The GitHub Actions workflow includes:
```yaml
- name: Check formatting with Black
  run: docker compose run --rm backend black --check /app

- name: Lint with Ruff
  run: docker compose run --rm backend ruff check /app

- name: Type check with mypy
  run: docker compose run --rm backend mypy /app/app/

- name: Run tests
  run: docker compose run --rm backend pytest /app/app/tests/
```

## Consequences

### Positive
- **Consistent code style** across the entire codebase
- **Better debugging**: Exception chaining preserves full stack traces
- **Fewer CI failures**: Issues caught locally before pushing
- **Faster development**: No waiting for CI to fail, then fix, then wait again
- **Type safety**: Mypy catches type errors before runtime
- **Code review efficiency**: Reviewers focus on logic, not style
- **Clear process**: Developers know exactly what to run before committing

### Negative
- **Learning curve**: Developers must understand exception chaining and type annotation patterns
- **Longer local dev time**: Running all checks takes 2-3 minutes
- **Tool complexity**: Multiple tools to learn (Black, Ruff, mypy, pytest)
- **Potential friction**: Developers might skip checks if in a hurry (mitigated by CI)

### Neutral
- **CI still required**: Local checks don't eliminate need for CI verification
- **Git history**: Formatting fixes may create large diffs (one-time cost)
- **Learning curve**: New developers need to learn the workflow

## Future Improvements

Consider implementing:
1. **Pre-commit hooks**: Automatically run checks on `git commit`
2. **Makefile shortcuts**: `make lint`, `make test`, `make all`
3. **Git hooks**: Prevent commits if checks fail
4. **IDE Integration**: Configure VS Code/PyCharm to run checks on save

## References
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Rules: B904](https://docs.astral.sh/ruff/rules/raise-without-from-inside-except/)
- [Ruff Rules: F823](https://docs.astral.sh/ruff/rules/undefined-local/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 3134: Exception Chaining](https://peps.python.org/pep-3134/)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/learn-github-actions/best-practices-for-workflows)

## Related ADRs
- [ADR 0001: Docker Development Environment](./0001-docker-development-environment.md)

## Revision History
- 2025-12-19: Initial version based on lessons from PR #35-#39 linting failures
- 2025-12-20: Added mypy type checking standards and pre-commit workflow
- 2025-12-20: Merged with development workflow ADR (previously ADR 0002)
- 2025-12-20: Added CI environment considerations section addressing hardcoded paths issue
