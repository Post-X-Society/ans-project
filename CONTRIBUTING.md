# Contributing to Ans

Thank you for your interest in contributing to Ans! This document provides guidelines and workflows for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Agent-Based Development](#agent-based-development)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment
- Follow professional communication standards

## Getting Started

### Prerequisites

- Docker Desktop 4.25+
- Git 2.40+
- Familiarity with Python (FastAPI) or TypeScript/Svelte
- Understanding of Test-Driven Development (TDD)

### Setup Your Development Environment

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/ans-project.git
cd ans-project

# 2. Set up environment variables
make setup
# Edit .env with your configuration

# 3. Build and start services
make docker-build
make docker-up

# 4. Run migrations
make db-migrate

# 5. Verify everything works
make test-backend
make test-frontend
```

## Development Workflow

### 1. Branch Strategy

We use a simplified Git Flow:

- **`main`**: Production-ready code
- **`feature/*`**: New features (e.g., `feature/user-authentication`)
- **`fix/*`**: Bug fixes (e.g., `fix/login-validation`)
- **`docs/*`**: Documentation updates (e.g., `docs/api-endpoints`)

### 2. Branch Naming Convention

```
<type>/<short-description>

Examples:
feature/email-notifications
fix/submission-validation
docs/deployment-guide
```

### 3. Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add JWT token refresh endpoint

Implements automatic token refresh to improve UX by reducing
login prompts. Tokens expire after 15 minutes but can be
refreshed for up to 7 days.

Closes #123
```

```
fix(submissions): validate email format before saving

Added email validation regex to prevent invalid submissions.

Fixes #456
```

## Testing Requirements

### Test-Driven Development (TDD)

**We follow TDD strictly. All code must have tests written FIRST.**

#### TDD Workflow

1. **Write a failing test** (RED)
2. **Write minimal code to pass** (GREEN)
3. **Refactor while keeping tests passing**
4. **Repeat**

### Backend Testing (Python/pytest)

```bash
# Run all tests
make test-backend

# Run specific test file
docker exec ans-backend pytest app/tests/api/test_submissions.py

# Run with coverage
docker exec ans-backend pytest --cov=app --cov-report=html
```

**Coverage Requirements:**
- Minimum 80% code coverage
- All new endpoints must have tests
- Test happy paths AND error cases

**Test Structure:**
```python
async def test_create_submission_success(client: AsyncClient):
    """Test successful submission creation"""
    # Arrange
    payload = {...}

    # Act
    response = await client.post("/api/v1/submissions", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json()["content"] == payload["content"]
```

### Frontend Testing (Vitest + Testing Library)

```bash
# Run all tests
make test-frontend

# Run in watch mode
docker exec ans-frontend npm test

# Run with UI
docker exec ans-frontend npm run test:ui
```

**Test Structure:**
```typescript
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';

describe('SubmissionCard', () => {
  it('displays submission content', () => {
    const submission = { content: 'Test claim' };
    render(SubmissionCard, { props: { submission } });

    expect(screen.getByText('Test claim')).toBeInTheDocument();
  });
});
```

## Code Style

### Backend (Python)

We use:
- **Black**: Code formatting
- **Ruff**: Linting
- **MyPy**: Type checking

```bash
# Format code
docker exec ans-backend black app/

# Lint code
docker exec ans-backend ruff check app/

# Type check
docker exec ans-backend mypy app/
```

**Pre-commit hooks** automatically run these checks. Install them:

```bash
cd backend
pre-commit install
```

**Style Guidelines:**
- Use type hints for all function parameters and return values
- Write docstrings for all public functions
- Keep functions small and focused (< 20 lines ideal)
- Use async/await for I/O operations

### Frontend (TypeScript/Svelte)

We use:
- **ESLint**: Linting
- **TypeScript**: Type safety
- **Svelte 5 Runes**: `$state`, `$derived`, `$props`

```bash
# Lint code
docker exec ans-frontend npm run lint

# Type check
docker exec ans-frontend npm run check
```

**Style Guidelines:**
- Use TypeScript strict mode
- Prefer Svelte 5 runes over legacy syntax
- Use Tailwind CSS for styling
- Keep components under 200 lines (split if larger)
- Use `$lib` path aliases for imports

## Pull Request Process

### Before Creating a PR

1. ✅ **All tests pass** (`make test-backend` and `make test-frontend`)
2. ✅ **Code is formatted** (Black for Python, ESLint for TypeScript)
3. ✅ **Type checking passes** (MyPy for Python, TypeScript for frontend)
4. ✅ **Coverage ≥ 80%**
5. ✅ **No merge conflicts** with `main`
6. ✅ **Commits follow convention**

### Creating a Pull Request

1. **Push your branch** to your fork
2. **Open a PR** on GitHub with:
   - Clear title following convention
   - Description of what changed and why
   - Link to related issue (e.g., `Closes #123`)
   - Screenshots (if UI changes)
   - Test results

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added with ≥80% coverage
- [ ] Manual testing completed

## Screenshots (if applicable)
![Before](url)
![After](url)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No console errors/warnings
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least 1 approval** required
3. **All feedback addressed**
4. **Squash and merge** (maintainers will merge)

## Agent-Based Development

This project uses specialized AI agent definitions for different development roles. See [AGENT_COORDINATION.md](docs/AGENT_COORDINATION.md) for details.

### Available Agents

- **System Architect**: Architecture decisions, ADRs
- **Database Architect**: Schema design, migrations
- **Backend Developer**: FastAPI endpoints, services
- **Frontend Developer**: Svelte components, UI/UX
- **AI/ML Engineer**: OpenAI integration
- **Integration Developer**: External APIs
- **DevOps/QA**: CI/CD, testing champion

### Using Agents

When working on a feature:
1. Identify the appropriate agent role
2. Read the agent definition in `docs/agents/`
3. Follow the agent's workflow and best practices
4. Switch agents when crossing domain boundaries

## Issue Reporting

### Bug Reports

Use the bug report template and include:
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment** (OS, browser, Docker version)
- **Logs** (if applicable)

### Feature Requests

Use the feature request template and include:
- **User story**: "As a [role], I want [feature] so that [benefit]"
- **Acceptance criteria**
- **Mockups/wireframes** (if applicable)
- **Priority** (P0-Critical, P1-High, P2-Medium, P3-Low)

### Labels

- `bug`: Something isn't working
- `enhancement`: New feature
- `documentation`: Documentation improvement
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `p0-critical`: Blocking issue
- `p1-high`: High priority
- `p2-medium`: Medium priority
- `p3-low`: Low priority

## Development Tips

### Running Individual Services

```bash
# Backend only
docker-compose -f infrastructure/docker-compose.dev.yml up backend postgres redis

# Frontend only
docker-compose -f infrastructure/docker-compose.dev.yml up frontend

# Database migrations
docker exec ans-backend alembic upgrade head

# Create new migration
docker exec ans-backend alembic revision --autogenerate -m "description"
```

### Debugging

#### Backend Debugging
```bash
# View logs
docker logs ans-backend -f

# Interactive shell
docker exec -it ans-backend bash

# Python shell
docker exec -it ans-backend python
```

#### Frontend Debugging
```bash
# View logs
docker logs ans-frontend -f

# Interactive shell
docker exec -it ans-frontend sh

# Install dependencies
docker exec ans-frontend npm install
```

### Common Issues

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for solutions to common problems.

## Documentation

### Where to Document

- **Code comments**: Complex logic, non-obvious decisions
- **Docstrings**: All public functions, classes, modules
- **ADRs**: Architecture decisions (`docs/adr/`)
- **Guides**: User-facing documentation (`docs/`)
- **README**: High-level overview, quick start

### Documentation Standards

- Use Markdown for all documentation
- Keep examples up-to-date with code
- Include code snippets in documentation
- Add diagrams for complex flows (Mermaid format)

## Questions?

- Check [LOCAL_DEVELOPMENT_GUIDE.md](docs/LOCAL_DEVELOPMENT_GUIDE.md)
- Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Check existing [Issues](https://github.com/Post-X-Society/ans-project/issues)
- Ask in [Discussions](https://github.com/Post-X-Society/ans-project/discussions)

## License

By contributing to Ans, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Ans!** 🎉
