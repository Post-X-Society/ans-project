# Agent Coordination Guide

This guide explains how to use Claude Code with multiple specialized agent definitions to collaboratively build the Ans project using Test-Driven Development.

## Table of Contents
1. [How to Use Agent Definitions](#how-to-use-agent-definitions)
2. [Multi-Agent Workflow](#multi-agent-workflow)
3. [Coordination Patterns](#coordination-patterns)
4. [Example: First Agent Task](#example-first-agent-task)

---

## How to Use Agent Definitions

### Loading an Agent Context

Each agent has a detailed definition file in `docs/agents/`. To assume an agent role in Claude Code:

1. **Open the agent definition file** in VS Code
2. **Read the entire file** to understand the role, responsibilities, and workflows
3. **Reference the file** in your conversation with Claude Code

**Example prompt:**
```
I want to work as the Backend Developer agent. Please read the agent definition in docs/agents/03-backend-developer.md and assume that role for this session.

My task is to implement the health check endpoint following TDD.
```

### Available Agent Definitions

- **[01-system-architect.md](agents/01-system-architect.md)** - Architecture decisions, ADRs, coordination
- **[02-database-architect.md](agents/02-database-architect.md)** - Schema design, migrations, pgvector
- **[03-backend-developer.md](agents/03-backend-developer.md)** - FastAPI endpoints, business logic
- **[04-frontend-developer.md](agents/04-frontend-developer.md)** - Svelte components, UI/UX
- **[05-ai-ml-engineer.md](agents/05-ai-ml-engineer.md)** - OpenAI integration, embeddings
- **[06-integration-developer.md](agents/06-integration-developer.md)** - External APIs, webhooks
- **[07-devops-qa-engineer.md](agents/07-devops-qa-engineer.md)** - CI/CD, testing champion

### When to Switch Agents

Switch agents when:
- You finish your current task
- You need expertise from another domain (ask them to review)
- You're blocked and need input from another agent
- You're starting a new epic or user story

**Example:**
```
I've completed the backend endpoint. Now I need to switch to the Frontend Developer agent to build the UI that consumes this API.

Please load docs/agents/04-frontend-developer.md and help me create the submission form component.
```

---

## Multi-Agent Workflow

### 1. Pick an Issue from the Project Board

**Steps:**
1. Go to the [Ans Development Project](https://github.com/orgs/Post-X-Society/projects)
2. Filter by your agent role (use "Agent" field)
3. Find an issue in the "Ready" column
4. Assign yourself and move to "In Progress"

**Example:**
```
Issue #7: [TASK] Implement health check endpoint
- Epic: #1 Project Infrastructure Setup
- Agent: Backend Developer
- Effort: Small
- Sprint: Sprint 1
```

### 2. Create a Feature Branch

**Naming convention:** `feature/agent-name/task-description`

**Example:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/backend/health-check-endpoint
```

### 3. Write Tests First (TDD)

**This is MANDATORY** - Tests must be written BEFORE implementation.

**Example for Backend:**
```python
# backend/app/tests/test_health.py
import pytest
from fastapi.testclient import TestClient

def test_health_check_returns_200(client: TestClient):
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_check_returns_status(client: TestClient):
    """Test that health endpoint returns status"""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
```

**Run the test (it should fail):**
```bash
pytest backend/app/tests/test_health.py
# Expected: FAILED (endpoint doesn't exist)
```

### 4. Implement Feature

Now implement the minimal code to make the test pass.

**Example:**
```python
# backend/app/api/v1/endpoints/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

**Run the test again:**
```bash
pytest backend/app/tests/test_health.py
# Expected: PASSED ✓
```

### 5. Create a Pull Request

**PR Naming:** `[AGENT] Brief description`

**Example:**
```bash
git add .
git commit -m "feat(backend): add health check endpoint

- Add GET /health endpoint
- Returns service status
- Tests written first (TDD)
- Coverage: 100%

Closes #7"

git push origin feature/backend/health-check-endpoint
```

**Create PR via GitHub CLI:**
```bash
gh pr create \
  --title "[Backend] Add health check endpoint" \
  --body "## Summary
- Implemented GET /health endpoint
- Follows TDD approach (tests written first)
- Returns service status and database connectivity

## Testing
- Added unit tests for health endpoint
- All tests passing ✓
- Coverage: 100%

## Related Issues
Closes #7

## Checklist
- [x] Tests written before implementation
- [x] All tests passing
- [x] Coverage ≥ 80%
- [x] No linting errors
- [x] Documentation updated

@agent:devops Ready for review" \
  --base develop
```

### 6. Get PR Reviewed and Merged

**Review process:**
1. CI/CD automatically runs tests
2. Request review from at least one other agent
3. Address review comments
4. Once approved + tests pass → auto-merge

**Tagging agents in PR comments:**
```markdown
@agent:architect Can you review the API structure? Is this aligned with our REST conventions?

@agent:devops The build is failing. Can you help debug the CI pipeline?
```

---

## Coordination Patterns

### Daily Sync Updates

Post daily updates in the current sprint issue (e.g., #6 for Sprint 1):

**Format:**
```markdown
**Backend Developer - 2025-12-13**
- ✅ Completed: Health check endpoint (#7), submission model tests
- 🚧 In Progress: POST /api/v1/submissions endpoint (#8)
- 🚫 Blockers: Waiting for database schema approval from @agent:database (#2)
- 📋 Next: Complete submission endpoint tests, implement service layer
```

### Cross-Agent Dependencies

Use "Blocked by" in issue descriptions:

**Example:**
```markdown
# Issue #8: Implement POST /api/v1/submissions

## Dependencies
**Blocked by:** #2 (Database schema for submissions must be approved)

@agent:database Please review the schema in PR #10 so I can proceed with this endpoint.
```

### When to Escalate to System Architect

Escalate when:
- You need to make an architectural decision (new pattern, library, approach)
- Multiple agents disagree on implementation approach
- You're considering a major refactoring
- Performance/security concerns arise

**Example:**
```markdown
@agent:architect

I'm implementing the submission endpoint and considering two approaches:

1. **Service Layer Pattern**: Create a SubmissionService class
2. **Direct Repository Pattern**: Call database directly from endpoint

Which aligns better with our architecture? Should I create an ADR for this?
```

### When to Ask Product Owner

Ask the Product Owner (human) when:
- Requirements are unclear or ambiguous
- You need to prioritize between competing features
- You discover a scope change or new requirement
- You need to make a business decision (not technical)

**Example:**
```markdown
@product-owner

In the submission form, should we allow anonymous submissions or require authentication?
This affects the database schema and API design.
```

### When to Use Claude Browser Plugin for Debugging

For complex browser-side debugging issues that can't be easily diagnosed from server logs:

**When to ask user to invoke Claude browser plugin:**
- Frontend JavaScript errors that don't make sense from the stack trace
- Caching issues where code changes aren't reflecting in the browser
- Framework version incompatibility issues (e.g., Svelte 5 + library mismatches)
- Complex DOM/rendering issues
- Network request debugging (failed requests, CORS, etc.)
- Browser-specific bugs
- Service Worker or Cache API issues

**Example prompt for user:**
```markdown
The error suggests a framework compatibility issue, but I need to see what's actually executing in the browser.

Could you please use the Claude browser plugin to analyze:
1. Open DevTools Console and capture the full error with stack trace
2. Check the Network tab for the specific file being served
3. Look at the Sources tab to see the actual compiled code
4. Check Application tab for any Service Workers or cached content

Ask Claude browser plugin to help identify the root cause of the version mismatch.
```

**Lesson learned (2025-12-27):**
- **Issue**: Svelte 5 + TanStack Query v5 incompatibility
- **Symptom**: "queryKey needs to be an Array" error despite code having arrays
- **Root Cause**: TanStack Query v5 used Svelte 4 stores, incompatible with Svelte 5 runes
- **Solution**: Upgrade to TanStack Query v6 + remove `$` store prefixes
- **Detection**: Claude browser plugin analyzed compiled JS and found store-based code was executing
- **Takeaway**: Framework major version changes require checking ALL dependency compatibility

---

## Example: First Agent Task

Let's walk through a complete example of the **Backend Developer** implementing the health check endpoint.

### Step 1: Pick the Issue

1. Go to GitHub Project → "Ready" column
2. Find issue #7: `[TASK] Implement health check endpoint`
3. Assign to yourself, move to "In Progress"

### Step 2: Load Agent Context

**Prompt to Claude Code:**
```
I'm working on issue #7: Implement health check endpoint.

Please read docs/agents/03-backend-developer.md and assume the Backend Developer role.

I need to:
1. Create a health check endpoint at GET /health
2. Follow TDD (write tests first)
3. Ensure 80% coverage

Let's start by writing the tests.
```

### Step 3: Create Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/backend/health-check-endpoint
```

### Step 4: Write Tests First

**Claude Code generates:**
```python
# backend/app/tests/test_health.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Provide a test client"""
    return TestClient(app)

def test_health_check_returns_200(client):
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_check_returns_json(client):
    """Test that health endpoint returns JSON"""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"

def test_health_check_contains_status(client):
    """Test that health response contains status field"""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

def test_health_check_includes_database_status(client):
    """Test that health response includes database connectivity"""
    response = client.get("/health")
    data = response.json()
    assert "database" in data
    assert data["database"] in ["healthy", "unhealthy"]
```

### Step 5: Run Tests (Should Fail)

```bash
cd backend
pytest app/tests/test_health.py -v

# Output:
# FAILED test_health.py::test_health_check_returns_200
# (endpoint doesn't exist yet)
```

✅ **This is expected!** Tests should fail before implementation.

### Step 6: Implement Endpoint

**Claude Code implements:**

```python
# backend/app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint

    Returns:
        JSON with service status and dependency health
    """
    health_status = {
        "status": "healthy",
        "database": "unknown"
    }

    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status
```

```python
# backend/app/main.py
from fastapi import FastAPI
from app.api.v1.endpoints.health import router as health_router

app = FastAPI(title="Ans API", version="0.1.0")

app.include_router(health_router, tags=["health"])
```

### Step 7: Run Tests Again (Should Pass)

```bash
pytest app/tests/test_health.py -v --cov=app --cov-report=term-missing

# Output:
# test_health.py::test_health_check_returns_200 PASSED
# test_health.py::test_health_check_returns_json PASSED
# test_health.py::test_health_check_contains_status PASSED
# test_health.py::test_health_check_includes_database_status PASSED
#
# Coverage: 100%
```

✅ **All tests passing! Coverage 100%!**

### Step 8: Commit and Push

```bash
git add .
git commit -m "feat(backend): add health check endpoint

- Implement GET /health endpoint
- Check database connectivity
- Return service status
- Tests written first (TDD)
- Coverage: 100%

Closes #7"

git push origin feature/backend/health-check-endpoint
```

### Step 9: Create Pull Request

```bash
gh pr create \
  --title "[Backend] Add health check endpoint" \
  --body "## Summary
✅ Implemented GET /health endpoint following TDD

## Changes
- Created health check endpoint at GET /health
- Returns service status and database connectivity
- Tests written BEFORE implementation (TDD)

## Testing
- 4 tests added in app/tests/test_health.py
- All tests passing ✓
- Coverage: 100%

## Related Issues
Closes #7

## Review Checklist
- [x] Tests written before implementation
- [x] All tests passing
- [x] Coverage ≥ 80% (100%)
- [x] No linting errors
- [x] Documentation (docstring) included

## Agent Tags
@agent:devops Ready for CI/CD review
@agent:architect Please verify this aligns with health check standards" \
  --base develop
```

### Step 10: Monitor PR and Respond to Reviews

**CI/CD runs automatically:**
- ✅ Tests pass
- ✅ Coverage: 100%
- ✅ Linting: No errors
- ✅ Security scan: No vulnerabilities

**Other agents review:**

```markdown
DevOps/QA Engineer comment:
"✅ All tests passing
✅ Coverage excellent
✅ Build successful
Approved!"
```

```markdown
System Architect comment:
"Good work! Consider adding a version field to the response.
Otherwise LGTM!"
```

**You respond:**
```bash
# Add version to response
git add .
git commit -m "feat: add version to health check response"
git push origin feature/backend/health-check-endpoint
```

### Step 11: Auto-Merge

Once approved + tests pass → PR auto-merges to `develop`

### Step 12: Update Daily Sync

Post in issue #6 (Sprint 1 Daily Sync):

```markdown
**Backend Developer - 2025-12-13**
- ✅ Completed: Health check endpoint (#7) - merged to develop
- 🚧 In Progress: Setting up submission API endpoint (#8)
- 🚫 Blockers: Waiting for database schema from @agent:database
- 📋 Next: Write tests for POST /api/v1/submissions
```

### Step 13: Move Issue to Done

Move #7 from "In Review" → "Done" on the project board.

---

## Tips for Effective Agent Collaboration

### 1. **Always Tag Agents**
Use `@agent:name` to get another agent's attention:
```markdown
@agent:frontend Can you create the UI for this endpoint?
@agent:database Can you review this migration?
```

### 2. **Be Specific in PRs**
Include:
- What changed
- Why it changed
- How you tested it
- What agents should review

### 3. **Ask Questions Early**
Don't wait until you're blocked. Ask questions proactively:
```markdown
@agent:architect I'm about to implement caching. Should I use Redis or in-memory?
```

### 4. **Document Decisions**
If you make an architectural choice, document it:
```markdown
@agent:architect Should I create an ADR for this service layer pattern?
```

### 5. **Celebrate Wins**
When a major feature merges, celebrate in the daily sync:
```markdown
**Backend Developer - 2025-12-15**
- ✅ Completed: Entire submissions API! 🎉
  - POST, GET, LIST endpoints all working
  - 95% test coverage
  - All tests passing in CI
```

### 6. **Help Others**
If you see another agent blocked, offer help:
```markdown
@agent:frontend I saw you're blocked on the API contract.
I can provide the OpenAPI spec right now if that helps!
```

---

## Common Workflows

### Workflow: Creating a New API Endpoint

1. **Backend Developer**: Write API endpoint tests
2. **Backend Developer**: Implement endpoint
3. **Backend Developer**: Create PR, tag @agent:devops
4. **DevOps/QA**: Review tests and coverage
5. **Backend Developer**: Merge after approval
6. **Frontend Developer**: Write component tests
7. **Frontend Developer**: Build UI component
8. **Frontend Developer**: Integrate with API
9. **DevOps/QA**: Write E2E test for full flow

### Workflow: Database Schema Change

1. **Backend Developer**: Identify need for schema change
2. **Backend Developer**: Tag @agent:database in issue
3. **Database Architect**: Review requirements
4. **Database Architect**: Create migration (with tests)
5. **Database Architect**: Create PR, tag @agent:backend
6. **Backend Developer**: Verify migration works locally
7. **DevOps/QA**: Test migration in staging
8. **Database Architect**: Merge after approvals

### Workflow: Architectural Decision

1. **Any Agent**: Identify need for decision
2. **Any Agent**: Tag @agent:architect with question
3. **System Architect**: Research options
4. **System Architect**: Create ADR with recommendation
5. **System Architect**: Request feedback from affected agents
6. **System Architect**: Finalize ADR
7. **All Agents**: Implement according to ADR

---

## Sprint Cadence

### Week 1 (Sprint 1)
- **Monday**: Sprint planning, pick issues
- **Daily**: Post updates in daily sync issue
- **Friday**: Sprint review, demo working features
- **Friday**: Sprint retrospective, plan next sprint

### Daily Routine
1. Check daily sync issue for updates
2. Post your own update
3. Pick next issue from "Ready" column
4. Write tests first
5. Implement feature
6. Create PR
7. Review other agents' PRs
8. Repeat

---

## FAQ

### Q: What if I disagree with another agent's approach?

Discuss in the PR or issue thread:
```markdown
@agent:backend I see you're using synchronous calls here.
Have you considered async for better performance?
Let's discuss the tradeoffs.
```

Escalate to @agent:architect if you can't agree.

### Q: What if tests are failing in CI but passing locally?

Tag @agent:devops:
```markdown
@agent:devops Tests are green locally but failing in CI.
Can you help debug the pipeline?
```

### Q: What if I finish all my issues early?

1. Pick issues from other agents (with their permission)
2. Write additional tests to improve coverage
3. Refactor code for better quality
4. Help review PRs from other agents

### Q: What if I'm blocked and can't proceed?

1. Document the blocker clearly
2. Tag the agent who can unblock you
3. Pick a different issue in the meantime
4. Update the daily sync with your blocker

---

## Summary

**Remember:**
- ✅ Load agent definition before starting work
- ✅ Always write tests FIRST (TDD)
- ✅ Tag other agents for questions/reviews
- ✅ Post daily updates in sprint sync issue
- ✅ Minimum 80% test coverage
- ✅ Document decisions in ADRs
- ✅ Celebrate wins and help others

**Let's build amazing software together! 🚀**
