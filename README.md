# Ans - Snapchat Fact-Checking for Amsterdam Youth

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![Svelte 5](https://img.shields.io/badge/Svelte-5-FF3E00.svg)](https://svelte.dev/)

> A modern, AI-powered fact-checking service integrated with Snapchat, designed specifically for Amsterdam youth to combat misinformation.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Available Commands](#available-commands)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

**Ans** is a fact-checking platform that allows Amsterdam youth to submit claims via Snapchat or a web interface. The system uses AI (OpenAI GPT-4) and integrates with the BENEDMO fact-checking API to verify claims and provide evidence-based responses.

### Key Technologies

- **Backend**: FastAPI (Python 3.11+) with async/await
- **Frontend**: Svelte 5 (SPA mode) with TailwindCSS
- **Database**: PostgreSQL 15 with pgvector extension for embeddings
- **Cache/Queue**: Redis 7
- **AI Integration**: OpenAI API for natural language processing
- **Development**: Docker Compose for local environment
- **Testing**: pytest (backend), Vitest (frontend), TDD approach

## Features

### Core Functionality
- **Multi-Channel Submissions**: Accept claims via Snapchat API and web interface
- **AI-Powered Fact-Checking**: Leverage GPT-4 for claim analysis
- **Vector Search**: Use pgvector for semantic similarity matching
- **Real-time Processing**: Async processing with Redis job queues and Celery
- **Modern UI**: Responsive Svelte 5 application with TailwindCSS
- **Comprehensive Testing**: 808+ tests passing with 80%+ coverage (TDD methodology)
- **Developer-Friendly**: Hot reload, Docker Compose, extensive documentation

### EFCSN Compliance Features ✅
- **Workflow State Machine**: 15-state workflow for fact-check lifecycle management
- **Multi-Tier Peer Review**: Consensus-based review system with deliberation
- **Rating System**: 6 standardized ratings (TRUE, PARTLY_FALSE, FALSE, MISSING_CONTEXT, ALTERED, SATIRE)
- **Source Management**: Evidence tracking with credibility ratings and URL archiving (Wayback Machine)
- **Corrections & Complaints**: Public correction request system with SLA tracking
- **Transparency Reporting**: Automated monthly transparency reports with versioning
- **Analytics Dashboard**: Real-time EFCSN compliance monitoring
- **GDPR Compliance**: Data retention policies, right-to-be-forgotten, cookie consent
- **Email Notifications**: Multilingual (EN/NL) automated workflow notifications
- **Role-Based Access Control**: Submitter, Reviewer, Admin, Super Admin roles
- **Quality Metrics**: Time-to-publication, correction rates, source quality tracking

## Quick Start

Get the project running in under 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/Post-X-Society/ans-project.git
cd ans-project

# 2. Set up environment variables
make setup
# Edit .env with your API keys (OPENAI_API_KEY is required)

# 3. Build and start all services
make docker-build
make docker-up

# 4. Verify everything is running
make status

# Access the application:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

That's it! You now have a fully functional development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Docker Desktop**: 4.25+ ([Download](https://www.docker.com/products/docker-desktop/))
  - Docker Engine 24.0+
  - Docker Compose v2.0+
- **Git**: 2.40+ ([Download](https://git-scm.com/downloads))
- **OpenAI API Key**: Sign up at [OpenAI Platform](https://platform.openai.com/)

### Optional (for local development without Docker)

- **Python**: 3.11+ ([Download](https://www.python.org/downloads/))
- **Node.js**: 18+ with npm ([Download](https://nodejs.org/))
- **PostgreSQL**: 15+ with pgvector extension
- **Redis**: 7+

### System Requirements

- **OS**: macOS, Linux, or Windows with WSL2
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space

## Installation

### Option 1: Docker (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Post-X-Society/ans-project.git
cd ans-project

# Copy environment template and configure
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENAI_API_KEY
# Optional: BENEDMO_API_KEY (for external fact-checking)
nano .env  # or use your preferred editor

# Build Docker images (first time only, or after dependency changes)
make docker-build

# Start all services
make docker-up

# Verify services are healthy
make status
```

### Option 2: Local Development (Advanced)

For development without Docker:

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Create database
createdb ans_dev
psql ans_dev -c "CREATE EXTENSION vector;"

# Run migrations
alembic upgrade head

# Start backend (in one terminal)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
ans-project/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints and routes
│   │   │   └── v1/         # API version 1
│   │   │       └── endpoints/
│   │   ├── core/           # Core functionality (config, database)
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic schemas for validation
│   │   ├── services/       # Business logic layer
│   │   └── tests/          # pytest test suite
│   ├── alembic/            # Database migrations
│   ├── Dockerfile          # Backend container definition
│   ├── pyproject.toml      # Python dependencies and config
│   └── requirements.txt    # Frozen dependencies
│
├── frontend/                # Svelte 5 frontend application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/        # API client and HTTP utilities
│   │   │   └── components/ # Reusable Svelte components
│   │   ├── routes/         # SvelteKit routes (SPA mode)
│   │   └── __tests__/      # Vitest test suite
│   ├── static/             # Static assets
│   ├── Dockerfile          # Frontend container definition
│   ├── package.json        # Node dependencies
│   ├── svelte.config.js    # Svelte configuration
│   ├── tailwind.config.js  # TailwindCSS configuration
│   └── vite.config.js      # Vite build configuration
│
├── infrastructure/          # Docker and deployment configs
│   ├── docker-compose.dev.yml  # Development environment
│   └── init-db.sql         # PostgreSQL initialization script
│
├── docs/                    # Project documentation
│   ├── AGENT_COORDINATION.md       # Multi-agent development guide
│   ├── POST_MORTEM_SSR_MIGRATION.md # Lessons learned
│   └── INFRASTRUCTURE_TESTING.md   # Testing checklist
│
├── scripts/                 # Utility scripts
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
├── Makefile                # Development commands
└── README.md               # This file
```

### Key Directories Explained

- **backend/app/api**: RESTful API endpoints organized by version
- **backend/app/models**: Database models with SQLAlchemy (PostgreSQL + pgvector)
- **backend/app/services**: Business logic separated from API layer
- **frontend/src/routes**: File-based routing with SvelteKit (SPA mode)
- **frontend/src/lib/api**: Axios client for backend communication
- **infrastructure**: Docker Compose setup for local development

## Development

### Starting the Development Environment

```bash
# Start all services in detached mode
make docker-up
# Or simply:
make dev

# View logs from all services
make docker-logs

# View logs from specific service
make docker-logs-backend
make docker-logs-frontend
```

### Hot Reload

Both backend and frontend support hot reload:

- **Backend**: Uvicorn watches for Python file changes and reloads automatically
- **Frontend**: Vite HMR (Hot Module Replacement) updates browser without refresh

### Accessing Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Svelte application |
| Backend API | http://localhost:8000 | FastAPI REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API documentation |
| PostgreSQL | localhost:5432 | Database (user: postgres, password: postgres) |
| Redis | localhost:6379 | Cache and job queue |

### Working with the Database

```bash
# Open PostgreSQL shell
make db-shell

# Run migrations (apply latest schema changes)
make db-migrate

# Rollback last migration
make db-rollback

# Example: Check submissions table
docker compose -f infrastructure/docker-compose.dev.yml exec postgres psql -U postgres -d ans_dev -c "SELECT * FROM submissions LIMIT 5;"
```

### Working with Redis

```bash
# Open Redis CLI
make redis-shell

# Example commands in Redis CLI:
# PING
# KEYS *
# GET some_key
# MONITOR  (watch all commands in real-time)
```

### Shell Access

```bash
# Backend container shell
make backend-shell

# Inside container, you can run:
# python -m pytest
# alembic revision --autogenerate -m "Add new table"
# python manage.py <custom commands>
```

## Testing

We follow Test-Driven Development (TDD) - **write tests BEFORE implementation**.

### Backend Testing

```bash
# Run all backend tests
make test-backend

# Run with verbose output
docker compose -f infrastructure/docker-compose.dev.yml exec backend pytest -v

# Run specific test file
docker compose -f infrastructure/docker-compose.dev.yml exec backend pytest app/tests/test_health.py

# Run with coverage report
docker compose -f infrastructure/docker-compose.dev.yml exec backend pytest --cov=app --cov-report=term-missing

# Coverage requirement: 80% minimum
```

### Frontend Testing

```bash
# Run all frontend tests
make test-frontend

# Run in watch mode (during development)
cd frontend && npm test -- --watch

# Run with UI
cd frontend && npm run test:ui
```

### Full Test Suite

```bash
# Run all tests (backend + frontend)
make test
```

### Test Structure

```
backend/app/tests/
├── conftest.py              # Shared fixtures
├── test_health.py           # Health endpoint tests
├── test_submissions.py      # Submission API tests
└── test_fact_checking.py    # AI fact-checking tests

frontend/src/__tests__/
├── SubmissionForm.test.ts   # Form component tests
└── api/client.test.ts       # API client tests
```

## Available Commands

All commands are available via the Makefile for convenience:

### Development Commands

```bash
make help              # Show all available commands
make setup             # Initial project setup (copy .env.example)
make dev               # Start development environment
make docker-build      # Build Docker images
make docker-up         # Start all services
make docker-down       # Stop all services
make status            # Show status of all services
```

### Testing Commands

```bash
make test              # Run all tests (backend + frontend)
make test-backend      # Run backend tests only
make test-frontend     # Run frontend tests only
make lint              # Run linters (black, ruff, eslint)
```

### Database Commands

```bash
make db-migrate        # Apply database migrations
make db-rollback       # Rollback last migration
make db-shell          # Open PostgreSQL shell
```

### Utility Commands

```bash
make docker-logs           # View logs from all services
make docker-logs-backend   # View backend logs
make docker-logs-frontend  # View frontend logs
make redis-shell           # Open Redis CLI
make backend-shell         # Open backend container shell
make clean                 # Clean up containers and volumes
```

### NPM Scripts (Frontend)

```bash
cd frontend

npm run dev            # Start dev server
npm run build          # Build for production
npm run preview        # Preview production build
npm test               # Run tests
npm run test:ui        # Run tests with UI
npm run lint           # Run ESLint
npm run check          # Type-check with svelte-check
```

### Python Commands (Backend)

```bash
cd backend

pytest                 # Run tests
pytest -v              # Verbose output
pytest --cov=app       # With coverage
black app/             # Format code
ruff app/              # Lint code
mypy app/              # Type checking
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Getting Started
- **[README.md](README.md)**: This file - project overview and quick start
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: How to contribute, development workflow, PR process
- **[LOCAL_DEVELOPMENT_GUIDE.md](docs/LOCAL_DEVELOPMENT_GUIDE.md)**: Detailed local setup and manual testing guide
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**: Solutions to common problems

### API & Development
- **[API.md](docs/API.md)**: Complete API documentation with examples
- **API Documentation (Interactive)**: http://localhost:8000/docs (Swagger UI - when running)
- **API Documentation (Clean)**: http://localhost:8000/redoc (ReDoc - when running)
- **[AGENT_COORDINATION.md](docs/AGENT_COORDINATION.md)**: Multi-agent development workflow, TDD process

### Architecture & Decisions
- **[ADR Directory](docs/adr/)**: Architecture Decision Records
  - [0001: Docker Development Environment](docs/adr/0001-docker-development-environment.md)
  - [0002: GitHub SSH Authentication](docs/adr/0002-github-ssh-authentication.md)
  - [0003: Code Quality & Pre-commit Workflow](docs/adr/0003-code-quality-and-pre-commit-workflow.md)
  - [0004: Multilingual Text Files](docs/adr/0004-multilingual-text-files.md)
  - [0005: EFCSN Compliance Architecture](docs/adr/0005-efcsn-compliance-architecture.md)
  - [0006: Collaborative Workflow UI/UX](docs/adr/0006-collaborative-workflow-ui-ux.md)

### Agent Definitions
- **[Agent Directory](docs/agents/)**: Specialized development roles
  - [01: System Architect](docs/agents/01-system-architect.md)
  - [02: Database Architect](docs/agents/02-database-architect.md)
  - [03: Backend Developer](docs/agents/03-backend-developer.md)
  - [04: Frontend Developer](docs/agents/04-frontend-developer.md)
  - [05: AI/ML Engineer](docs/agents/05-ai-ml-engineer.md)
  - [06: Integration Developer](docs/agents/06-integration-developer.md)
  - [07: DevOps/QA Engineer](docs/agents/07-devops-qa-engineer.md)

### Project Management
- **[SPRINT_PLANNING_COMPLETE.md](docs/SPRINT_PLANNING_COMPLETE.md)**: Complete sprint breakdown and EFCSN feature roadmap
- **[INFRASTRUCTURE_TESTING.md](docs/INFRASTRUCTURE_TESTING.md)**: Testing checklist for Docker environment
- **[POST_MORTEM_SSR_MIGRATION.md](docs/POST_MORTEM_SSR_MIGRATION.md)**: Lessons learned from SSR to SPA migration

## Contributing

We welcome contributions from all agents! This project follows a multi-agent collaboration model.

### Development Workflow

1. **Pick an Issue**: Choose from the GitHub project board (filter by agent role)
2. **Create Branch**: `git checkout -b feature/agent-name/task-description`
3. **Write Tests First**: Follow TDD - tests before implementation
4. **Implement Feature**: Write minimal code to make tests pass
5. **Run Tests**: Ensure 80%+ coverage
6. **Create PR**: Use template and tag relevant agents for review
7. **Address Feedback**: Respond to code review comments
8. **Merge**: Auto-merge after approval and passing CI/CD

### Branch Naming Convention

```
feature/agent-name/short-description
fix/agent-name/bug-description
docs/agent-name/doc-update
```

Examples:
- `feature/backend/health-check-endpoint`
- `feature/frontend/submission-form`
- `fix/devops/docker-compose-warning`

### Commit Message Format

```
type(scope): brief description

Longer explanation if needed.

Closes #issue_number
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Example:
```
feat(backend): add health check endpoint

- Implement GET /api/v1/health endpoint
- Return service status and database connectivity
- Tests written first (TDD approach)
- Coverage: 100%

Closes #7
```

### Code Quality Requirements

- **Test Coverage**: Minimum 80% (enforced by CI/CD)
- **Linting**: No errors from black, ruff (backend) or ESLint (frontend)
- **Type Checking**: Pass mypy (backend) and TypeScript checks (frontend)
- **Documentation**: All public functions must have docstrings
- **Tests First**: TDD is mandatory - tests before implementation

### Pull Request Template

```markdown
## Summary
Brief description of changes

## Changes
- Bullet points of what changed
- Why it changed

## Testing
- Tests added/modified
- Coverage percentage
- Manual testing performed

## Related Issues
Closes #issue_number

## Review Checklist
- [ ] Tests written before implementation (TDD)
- [ ] All tests passing
- [ ] Coverage ≥ 80%
- [ ] No linting errors
- [ ] Documentation updated

## Agent Tags
@agent:role Ready for review
```

### Agent Coordination

This project uses specialized agent roles. See [AGENT_COORDINATION.md](docs/AGENT_COORDINATION.md) for:

- How to load agent definitions
- Multi-agent workflow
- Coordination patterns
- Example tasks with full TDD process

### Getting Help

- **Unclear Requirements**: Tag `@product-owner` in issue
- **Technical Questions**: Tag appropriate agent (e.g., `@agent:backend`)
- **Architectural Decisions**: Tag `@agent:architect`
- **CI/CD Issues**: Tag `@agent:devops`

## Troubleshooting

### Common Issues

#### Ports Already in Use

If you get port conflict errors:

```bash
# Check what's using the ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill the process or change ports in docker-compose.dev.yml
```

#### Services Won't Start

```bash
# Check Docker is running
docker info

# View detailed logs
make docker-logs

# Clean and rebuild
make clean
make docker-build
make docker-up
```

#### Database Connection Errors

```bash
# Verify PostgreSQL is healthy
docker compose -f infrastructure/docker-compose.dev.yml ps

# Check if database exists
docker exec ans-postgres psql -U postgres -l

# Restart PostgreSQL
docker compose -f infrastructure/docker-compose.dev.yml restart postgres
```

#### Frontend Can't Reach Backend

**Symptom**: Network errors or CORS errors in browser console

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/v1/health`
2. Check `VITE_API_URL` is NOT set in docker-compose.dev.yml (should use default)
3. Clear Vite cache:
   ```bash
   docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit
   ```
4. Perform hard browser refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)

**Why This Happens**: Vite bakes environment variables at build time. See [POST_MORTEM_SSR_MIGRATION.md](docs/POST_MORTEM_SSR_MIGRATION.md) for full explanation.

#### Hot Reload Not Working

**Backend**:
```bash
# Verify volume mounts
docker inspect ans-backend | grep -A 20 Mounts

# Restart container
docker compose -f infrastructure/docker-compose.dev.yml restart backend
```

**Frontend**:
```bash
# Clear cache and rebuild
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend
```

#### Tests Failing

```bash
# Backend: Check test database
docker exec ans-backend pytest app/tests/test_health.py -v

# Frontend: Clear cache
cd frontend
rm -rf node_modules/.vite
npm test

# If coverage fails, run with report to see missing lines
docker exec ans-backend pytest --cov=app --cov-report=term-missing
```

#### "Permission Denied" Errors

On Linux, Docker volumes may have permission issues:

```bash
# Fix backend permissions
sudo chown -R $USER:$USER backend/

# Fix frontend permissions
sudo chown -R $USER:$USER frontend/
```

#### "Module Not Found" Errors

**Backend**:
```bash
# Reinstall dependencies in container
docker compose -f infrastructure/docker-compose.dev.yml exec backend pip install -e ".[dev]"
```

**Frontend**:
```bash
# Reinstall dependencies in container
docker compose -f infrastructure/docker-compose.dev.yml exec frontend npm install
```

### Getting More Help

1. **Search Documentation**: Check [docs/POST_MORTEM_SSR_MIGRATION.md](docs/POST_MORTEM_SSR_MIGRATION.md) for lessons learned
2. **Check Logs**: `make docker-logs` often reveals the issue
3. **Infrastructure Testing**: Follow checklist in [docs/INFRASTRUCTURE_TESTING.md](docs/INFRASTRUCTURE_TESTING.md)
4. **Create Issue**: If problem persists, create GitHub issue with:
   - Error message
   - Steps to reproduce
   - System info (`docker --version`, OS)
   - Relevant logs

### Clean Slate

If everything is broken, start fresh:

```bash
# Stop and remove everything
make clean

# Remove Docker volumes (WARNING: deletes database data)
docker volume rm ans-project_postgres_data ans-project_redis_data

# Rebuild from scratch
make docker-build
make docker-up
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Post-X Society

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Contact

- **Organization**: Post-X Society
- **Project**: Ans - Snapchat Fact-Checking for Amsterdam Youth
- **Repository**: https://github.com/Post-X-Society/ans-project
- **Issues**: https://github.com/Post-X-Society/ans-project/issues

---

**Built with love by the Post-X Society team using multi-agent collaboration**

For questions about the development process, see [AGENT_COORDINATION.md](docs/AGENT_COORDINATION.md)
