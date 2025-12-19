# ADR 0001: Python Linting and Code Quality Standards

## Status
Accepted

## Date
2025-12-19

## Context
During the development sprint for issues #29-#34, all 5 pull requests failed CI/CD checks due to linting errors. The most common issues were:

1. **Black formatting violations**: Code not formatted according to PEP 8 standards
2. **Ruff B904 violations**: Missing exception chaining in exception handlers
3. **Ruff F823 violations**: Duplicate imports causing variable shadowing
4. **Import sorting issues**: Inconsistent import organization

These issues caused significant delays in merging feature branches and highlighted the need for standardized linting practices.

## Decision
We will enforce strict Python code quality standards using Black and Ruff, with the following mandatory practices:

### 1. Black Code Formatting
- **All Python code must be formatted with Black** before committing
- Black configuration: Default settings (88 character line length)
- CI will reject any code that fails `black --check`

### 2. Ruff Linting Rules
We enforce the following critical Ruff rules:

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

### 3. Pre-Commit Workflow
Before committing any Python code, developers MUST run:

```bash
# From project root
cd infrastructure
docker compose -f docker-compose.dev.yml run --rm backend black /app
docker compose -f docker-compose.dev.yml run --rm backend ruff check /app --fix
```

Or from backend directory:
```bash
black .
ruff check . --fix
```

### 4. Import Organization
- Ruff automatically organizes imports (I001 rule)
- Use `ruff check --fix` to auto-sort imports
- Standard order: stdlib → third-party → first-party → local
- Add `# noqa: I001` only when absolutely necessary

## Consequences

### Positive
- **Consistent code style** across the entire codebase
- **Better debugging**: Exception chaining preserves full stack traces
- **Fewer CI failures**: Linting issues caught before push
- **Automatic fixes**: Ruff can auto-fix most import and formatting issues
- **Code review efficiency**: Reviewers focus on logic, not style

### Negative
- **Learning curve**: Developers must understand exception chaining patterns
- **Pre-commit overhead**: Extra step before committing (mitigated by automation)
- **Occasional false positives**: May require `# noqa` comments in rare cases

### Neutral
- **CI enforcement**: Builds will fail on linting errors (by design)
- **Git history**: Formatting fixes may create large diffs (one-time cost)

## Implementation Notes

### CI/CD Configuration
The GitHub Actions workflow includes:
```yaml
- name: Check formatting with Black
  run: docker compose run --rm backend black --check /app

- name: Lint with Ruff
  run: docker compose run --rm backend ruff check /app
```

### Common Patterns

**FastAPI HTTPException Handling:**
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

**SQLAlchemy Import Pattern:**
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

## References
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Rules: B904](https://docs.astral.sh/ruff/rules/raise-without-from-inside-except/)
- [Ruff Rules: F823](https://docs.astral.sh/ruff/rules/undefined-local/)
- [PEP 3134: Exception Chaining](https://peps.python.org/pep-3134/)
- Sprint issues: #29, #30, #31, #32, #34 (all had linting issues)

## Revision History
- 2025-12-19: Initial version based on lessons from PR #35-#39 linting failures
