#!/usr/bin/env python3
"""
Ans Project Setup Script
Automates repository setup for multi-agent development workflow

Run this script with Claude Code in VS Code after completing steps 1-5:
1. Repository created on GitHub
2. Repository cloned locally
3. Branch protection will be set up
4. Basic structure exists
5. You're in the repository root directory

This script handles:
- Step 6: GitHub Labels
- Step 7: Milestones
- Step 8: GitHub Wiki initialization
- Step 9: CI/CD Workflows
- Step 10: Docker Infrastructure
- Step 11: Agent Role Definitions
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_step(step: str):
    """Print a step header"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{step}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Color.GREEN}✓ {message}{Color.END}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Color.YELLOW}⚠ {message}{Color.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Color.RED}✗ {message}{Color.END}")


def run_command(cmd: List[str], cwd: str = None, capture_output: bool = False) -> Tuple[bool, str]:
    """Run a shell command and return success status and output"""
    try:
        if capture_output:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            return True, result.stdout
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)


def check_prerequisites() -> bool:
    """Check if required tools are installed"""
    print_step("Checking Prerequisites")
    
    required_tools = {
        'git': ['git', '--version'],
        'gh (GitHub CLI)': ['gh', '--version'],
    }
    
    all_present = True
    for tool, cmd in required_tools.items():
        success, output = run_command(cmd, capture_output=True)
        if success:
            print_success(f"{tool} is installed")
        else:
            print_error(f"{tool} is NOT installed - please install it first")
            all_present = False
    
    # Check if we're in a git repository
    success, _ = run_command(['git', 'rev-parse', '--git-dir'], capture_output=True)
    if success:
        print_success("Current directory is a git repository")
    else:
        print_error("Current directory is NOT a git repository")
        print_error("Please run this script from the root of your ans-project repository")
        all_present = False
    
    # Check if gh is authenticated
    success, _ = run_command(['gh', 'auth', 'status'], capture_output=True)
    if success:
        print_success("GitHub CLI is authenticated")
    else:
        print_error("GitHub CLI is NOT authenticated")
        print_warning("Run: gh auth login")
        all_present = False
    
    return all_present


def create_github_labels():
    """Create all GitHub labels"""
    print_step("Step 6: Creating GitHub Labels")
    
    labels = [
        # Type labels
        ('bug', 'd73a4a', 'Something isn\'t working'),
        ('feature', 'a2eeef', 'New feature or request'),
        ('enhancement', '84b6eb', 'Improvement to existing feature'),
        ('documentation', '0075ca', 'Documentation only'),
        
        # Priority labels
        ('p0-critical', 'b60205', 'Critical priority'),
        ('p1-high', 'd93f0b', 'High priority'),
        ('p2-medium', 'fbca04', 'Medium priority'),
        ('p3-low', '0e8a16', 'Low priority'),
        
        # Team labels
        ('team:backend', '5319e7', 'Backend development'),
        ('team:frontend', '5319e7', 'Frontend development'),
        ('team:ai', '5319e7', 'AI/ML work'),
        ('team:devops', '5319e7', 'DevOps/Infrastructure'),
        ('team:database', '5319e7', 'Database work'),
        ('team:integration', '5319e7', 'Integration work'),
        ('team:architecture', '5319e7', 'Architecture work'),
        
        # Agent labels
        ('agent:architect', 'c5def5', 'System Architect'),
        ('agent:backend', 'c5def5', 'Backend Developer'),
        ('agent:frontend', 'c5def5', 'Frontend Developer'),
        ('agent:ai', 'c5def5', 'AI/ML Engineer'),
        ('agent:devops', 'c5def5', 'DevOps/QA Engineer'),
        ('agent:database', 'c5def5', 'Database Architect'),
        ('agent:integration', 'c5def5', 'Integration Developer'),
        
        # Status labels
        ('blocked', 'e99695', 'Blocked by another issue'),
        ('blocking', 'e99695', 'Blocking other issues'),
        ('needs-review', 'fbca04', 'Needs code review'),
        ('waiting-feedback', 'fbca04', 'Waiting for feedback'),
        
        # Area labels
        ('area:snapchat', 'd4c5f9', 'Snapchat integration'),
        ('area:benedmo', 'd4c5f9', 'BENEDMO integration'),
        ('area:ai', 'd4c5f9', 'AI/ML features'),
        ('area:database', 'd4c5f9', 'Database related'),
        ('area:admin', 'd4c5f9', 'Admin panel'),
        ('area:volunteer', 'd4c5f9', 'Volunteer dashboard'),
    ]
    
    created = 0
    skipped = 0
    
    for name, color, description in labels:
        # Check if label already exists
        success, _ = run_command(
            ['gh', 'label', 'list', '--json', 'name', '-q', f'.[] | select(.name=="{name}")'],
            capture_output=True
        )
        
        if success and _.strip():
            print_warning(f"Label '{name}' already exists, skipping")
            skipped += 1
            continue
        
        success, output = run_command(
            ['gh', 'label', 'create', name, '--color', color, '--description', description],
            capture_output=True
        )
        
        if success:
            print_success(f"Created label: {name}")
            created += 1
        else:
            print_error(f"Failed to create label: {name}")
    
    print(f"\n{Color.BOLD}Summary: {created} labels created, {skipped} already existed{Color.END}")


def create_milestones():
    """Create project milestones"""
    print_step("Step 7: Creating Milestones")
    
    milestones = [
        ('v0.1 - MVP Core', 'Month 1', 'Core Snapchat integration, basic message handling, database setup'),
        ('v0.2 - BENEDMO Integration', 'Month 2', 'Connect to BENEDMO fact-check database, automated claim matching'),
        ('v0.3 - AI Analysis', 'Month 3', 'OpenAI integration for content analysis, similarity detection'),
        ('v1.0 - Public Launch', 'Month 4', 'Volunteer dashboard, admin panel, production deployment'),
    ]
    
    created = 0
    skipped = 0
    
    for title, due_date, description in milestones:
        # Check if milestone already exists
        success, output = run_command(
            ['gh', 'api', 'repos/:owner/:repo/milestones', '--jq', f'.[] | select(.title=="{title}") | .title'],
            capture_output=True
        )
        
        if success and output.strip():
            print_warning(f"Milestone '{title}' already exists, skipping")
            skipped += 1
            continue
        
        # Create milestone without due date (GitHub API requires ISO format, we use description instead)
        success, _ = run_command(
            ['gh', 'api', 'repos/:owner/:repo/milestones', '-X', 'POST',
             '-f', f'title={title}',
             '-f', f'description=Due: {due_date}\n\n{description}'],
            capture_output=True
        )
        
        if success:
            print_success(f"Created milestone: {title}")
            created += 1
        else:
            print_error(f"Failed to create milestone: {title}")
    
    print(f"\n{Color.BOLD}Summary: {created} milestones created, {skipped} already existed{Color.END}")


def create_issue_templates():
    """Create GitHub issue templates"""
    print_step("Step 8a: Creating Issue Templates")
    
    template_dir = Path('.github/ISSUE_TEMPLATE')
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Bug Report Template
    bug_template = """---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: ['bug', 'needs-review']
assignees: ''
---

## Description
<!-- Clear description of the bug -->

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->

## Environment
- Component: [backend/frontend/ai-service]
- Browser/OS: 
- Version: 

## Screenshots/Logs
<!-- If applicable -->

## Related Issues
<!-- Link related issues with #number -->
"""
    
    # Feature Request Template
    feature_template = """---
name: Feature Request
about: Suggest a new feature
title: '[FEATURE] '
labels: ['feature', 'needs-review']
assignees: ''
---

## User Story
As a [type of user], I want [goal] so that [benefit]

## Acceptance Criteria
- [ ] 
- [ ] 
- [ ] 

## Technical Notes
<!-- Any technical considerations -->

## Dependencies
<!-- Blocked by: #issue-number -->

## Related Issues
<!-- Link related issues with #number -->
"""
    
    # Task Template
    task_template = """---
name: Task
about: Technical implementation task
title: '[TASK] '
labels: ['enhancement']
assignees: ''
---

## Description
<!-- Clear description of the technical task -->

## Acceptance Criteria
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed

## Implementation Notes
<!-- Technical approach, files to modify, etc. -->

## Dependencies
<!-- Blocked by: #issue-number -->

## Estimated Effort
<!-- Small/Medium/Large -->

## Related Issues
<!-- Link related issues with #number -->
"""
    
    templates = {
        'bug_report.md': bug_template,
        'feature_request.md': feature_template,
        'task.md': task_template,
    }
    
    for filename, content in templates.items():
        filepath = template_dir / filename
        if filepath.exists():
            print_warning(f"Template {filename} already exists, skipping")
            continue
        
        filepath.write_text(content)
        print_success(f"Created template: {filename}")
    
    # PR Template
    pr_template = """## Description
<!-- Describe your changes -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] Tests written and passing (100% of existing tests pass)
- [ ] Code coverage maintained/improved (≥80%)
- [ ] Linting passes
- [ ] Security scan passes
- [ ] Documentation updated (Wiki if needed)
- [ ] Breaking changes noted
- [ ] Self-review completed

## Related Issues
Closes #
Related to #

## Testing
<!-- How was this tested? -->

## Screenshots
<!-- For UI changes -->

## Breaking Changes
<!-- List any breaking changes -->

## Reviewer Notes
<!-- Anything reviewers should focus on -->
"""
    
    pr_template_path = Path('.github/PULL_REQUEST_TEMPLATE.md')
    if pr_template_path.exists():
        print_warning("PR template already exists, skipping")
    else:
        pr_template_path.write_text(pr_template)
        print_success("Created PR template")


def create_workflows():
    """Create GitHub Actions workflows"""
    print_step("Step 9: Creating CI/CD Workflows")
    
    workflow_dir = Path('.github/workflows')
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    # Backend Tests Workflow
    backend_workflow = """name: Backend Tests

on:
  pull_request:
    paths:
      - 'backend/**'
      - '.github/workflows/backend-tests.yml'
  push:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ans_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install -e .
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run linting
        working-directory: ./backend
        run: |
          pip install black ruff mypy
          black --check .
          ruff check .
          mypy app/
      
      - name: Run tests with coverage
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/ans_test
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term-missing --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend
"""
    
    # Frontend Tests Workflow
    frontend_workflow = """name: Frontend Tests

on:
  pull_request:
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests.yml'
  push:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Run linting
        working-directory: ./frontend
        run: |
          npm run lint
          npm run format:check
      
      - name: Run tests with coverage
        working-directory: ./frontend
        run: npm run test:coverage
      
      - name: Build
        working-directory: ./frontend
        run: npm run build
"""
    
    # AI Service Tests Workflow
    ai_workflow = """name: AI Service Tests

on:
  pull_request:
    paths:
      - 'ai-service/**'
      - '.github/workflows/ai-service-tests.yml'
  push:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        working-directory: ./ai-service
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests with coverage
        working-directory: ./ai-service
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY_TEST }}
        run: |
          pytest --cov=. --cov-report=xml --cov-fail-under=80
"""
    
    # Security Scan Workflow
    security_workflow = """name: Security Scan

on:
  pull_request:
  push:
    branches: [develop, main]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Python Security Check
        run: |
          pip install bandit
          bandit -r backend/app/ -f json -o bandit-report.json || true
      
      - name: NPM Audit
        working-directory: ./frontend
        run: npm audit --audit-level=high || true
"""
    
    workflows = {
        'backend-tests.yml': backend_workflow,
        'frontend-tests.yml': frontend_workflow,
        'ai-service-tests.yml': ai_workflow,
        'security-scan.yml': security_workflow,
    }
    
    for filename, content in workflows.items():
        filepath = workflow_dir / filename
        if filepath.exists():
            print_warning(f"Workflow {filename} already exists, skipping")
            continue
        
        filepath.write_text(content)
        print_success(f"Created workflow: {filename}")


def create_docker_infrastructure():
    """Create Docker and infrastructure files"""
    print_step("Step 10: Creating Docker Infrastructure")
    
    infra_dir = Path('infrastructure')
    infra_dir.mkdir(exist_ok=True)
    
    # Docker Compose Dev
    docker_compose_dev = """version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ans
      POSTGRES_PASSWORD: ans_dev_password
      POSTGRES_DB: ans_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: postgres -c 'max_connections=200'

  postgres_test:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ans
      POSTGRES_PASSWORD: ans_test_password
      POSTGRES_DB: ans_test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    volumes:
      - ../backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ans:ans_dev_password@postgres:5432/ans_dev
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    volumes:
      - ../frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev -- --host

  ai-service:
    build:
      context: ../ai-service
      dockerfile: Dockerfile
    volumes:
      - ../ai-service:/app
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://ans:ans_dev_password@postgres:5432/ans_dev
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
"""
    
    # Makefile
    makefile = """.PHONY: help setup dev test lint clean

help: ## Show this help message
\t@echo 'Usage: make [target]'
\t@echo ''
\t@echo 'Available targets:'
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-15s\\033[0m %s\\n", $$1, $$2}'

setup: ## Initial setup
\t@echo "Setting up Ans development environment..."
\tcp .env.example .env
\tdocker-compose -f infrastructure/docker-compose.dev.yml build

dev: ## Start development environment
\tdocker-compose -f infrastructure/docker-compose.dev.yml up

test: ## Run all tests
\t@echo "Running backend tests..."
\tcd backend && pytest
\t@echo "Running frontend tests..."
\tcd frontend && npm test
\t@echo "Running AI service tests..."
\tcd ai-service && pytest

lint: ## Run linting
\tcd backend && black . && ruff check .
\tcd frontend && npm run lint && npm run format
\tcd ai-service && black . && ruff check .

clean: ## Clean up containers and volumes
\tdocker-compose -f infrastructure/docker-compose.dev.yml down -v
"""
    
    # .env.example
    env_example = """# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://ans:ans_dev_password@localhost:5432/ans_dev

# Redis
REDIS_URL=redis://localhost:6379

# Snapchat (reverse-engineered API)
SNAPCHAT_USERNAME=
SNAPCHAT_PASSWORD=

# BENEDMO
BENEDMO_API_URL=https://api.benedmo.org
BENEDMO_API_KEY=

# Backend
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development

# Frontend
VITE_API_URL=http://localhost:8000
"""
    
    files = {
        'infrastructure/docker-compose.dev.yml': docker_compose_dev,
        'Makefile': makefile,
        '.env.example': env_example,
    }
    
    for filepath, content in files.items():
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.exists():
            print_warning(f"{filepath} already exists, skipping")
            continue
        
        path.write_text(content)
        print_success(f"Created: {filepath}")


def create_agent_definitions():
    """Create agent role definition files"""
    print_step("Step 11: Creating Agent Role Definitions")
    
    agent_dir = Path('docs/agents')
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # System Architect Agent
    architect_def = """# System Architect / Technical Lead Agent

## Role & Responsibilities

You are the **System Architect and Technical Lead** for the Ans project. You define the overall system architecture, make key technical decisions, and ensure architectural consistency across all components.

### Core Responsibilities:
- Define and maintain system architecture
- Create and update Architecture Decision Records (ADRs)
- Review all PRs for architectural consistency
- Make technology stack and integration decisions
- Coordinate between agents on technical dependencies
- Resolve technical conflicts between agents
- Approve architectural changes and patterns

### Authority:
- **Can approve PRs** from other agents
- **Must approve** all architectural changes, API changes, data model changes, new dependencies
- Final say on technical approach when agents disagree

## Working Approach

### Test-Driven Development (TDD)
- All architectural decisions must consider testability
- Define testing strategy for each component
- Ensure integration points are testable

### Communication
- Create ADRs for all significant architectural decisions
- Comment on PRs with architectural guidance
- Create issues for architectural improvements
- Use `@agent:backend`, `@agent:frontend` etc. to coordinate

### Decision Process
1. Research options and trade-offs
2. Create ADR in `/docs/adr/NNNN-title.md`
3. Get feedback from affected agents via issue comments
4. Document final decision
5. Update Wiki architecture documentation

## Tech Stack (Defined)

**Backend:**
- Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic
- PostgreSQL 15+ with pgvector
- Redis (caching, job queue)
- pytest + pytest-asyncio

**Frontend:**
- Svelte 5, TypeScript, Vite
- TanStack Query, Tailwind CSS
- Vitest

**AI/ML:**
- OpenAI API (GPT-4, embeddings)
- pgvector for similarity search

**Infrastructure:**
- Docker + Docker Compose
- nginx-proxy
- Hetzner VPS
- GitHub Actions

## Interaction with Other Agents

### With Database Architect:
- Review and approve schema changes
- Coordinate on data model evolution
- Ensure migration strategy is sound

### With Backend Developer:
- Review API design
- Approve new endpoint patterns
- Guide service architecture

### With Frontend Developer:
- Define API contracts
- Approve component architecture
- Ensure proper state management

### With AI/ML Engineer:
- Define AI service integration points
- Review model selection decisions
- Approve pipeline architecture

### With Integration Developer:
- Review external API integrations
- Approve webhook handling patterns
- Guide error handling strategy

### With DevOps/QA:
- Define deployment strategy
- Review CI/CD pipeline changes
- Coordinate on infrastructure decisions

## Example Workflows

### Creating an ADR:
1. Identify architectural decision needed
2. Create file: `/docs/adr/0001-use-fastapi-for-backend.md`
3. Use template:
```markdown
# ADR 0001: Use FastAPI for Backend

## Status
Accepted

## Context
We need to choose a Python web framework for the Ans backend API...

## Decision
We will use FastAPI...

## Consequences
- Positive: Async support, automatic OpenAPI docs, type safety
- Negative: Smaller ecosystem than Django
- Neutral: Need to choose separate auth library
```
4. Create PR with ADR
5. Tag relevant agents for feedback
6. Merge and update Wiki

### Reviewing a PR:
1. Check if change aligns with architecture
2. Verify tests cover the change
3. Ensure documentation is updated
4. Check for architectural red flags:
   - Tight coupling
   - Violation of separation of concerns
   - Missing error handling
   - Security issues
5. Approve or request changes

### Coordinating Dependencies:
```markdown
# Issue: Backend API needs new user authentication

@agent:backend I'll create an ADR for our authentication approach first.
Blocking this until we decide between JWT vs session-based auth.

Created: #45 (ADR: Choose authentication strategy)
This issue is blocked by: #45
```

## Code Review Checklist

When reviewing PRs, check:
- [ ] Architecture principles followed
- [ ] Tests present and meaningful (TDD)
- [ ] Error handling implemented
- [ ] Security considerations addressed
- [ ] Documentation updated
- [ ] No unnecessary dependencies added
- [ ] Consistent with existing patterns
- [ ] Performance implications considered
- [ ] Breaking changes documented

## Don't Do This:
❌ Make architectural decisions without documenting them
❌ Approve PRs that skip tests
❌ Ignore technical debt
❌ Let agents work in silos without coordination
❌ Approve breaking changes without migration plan

## Do This:
✅ Document all significant decisions as ADRs
✅ Foster collaboration between agents
✅ Ensure test coverage on all changes
✅ Think about long-term maintainability
✅ Communicate clearly and proactively
"""
    
    # Database Architect Agent
    database_def = """# Database Architect Agent

## Role & Responsibilities

You are the **Database Architect** for the Ans project. You design database schemas, manage data models, ensure data integrity, and optimize database performance.

### Core Responsibilities:
- Design database schemas for all data models
- Create and manage Alembic migrations
- Optimize queries and indexes
- Design vector database strategy for AI similarity matching
- Plan BENEDMO integration data models
- Ensure data integrity and constraints
- Monitor and optimize database performance

### Authority:
- **Must approve** all schema changes and migrations
- **Can approve** PRs affecting data models

## Data Models Overview

### Core Entities:
1. **Submissions** - Content submitted by users for fact-checking
2. **Users** - Youth users who submit content
3. **Volunteers** - Fact-checkers who verify claims
4. **FactChecks** - Verified fact-check results
5. **Claims** - Extracted claims from submissions
6. **Matches** - Links between claims and existing fact-checks

### Integration Data:
- **BENEDMO facts** - Cached data from BENEDMO API
- **Snapchat messages** - Message metadata and processing status

### Audit & Analytics:
- **AuditLogs** - Track all data changes
- **Analytics** - Usage statistics

## Working Approach

### Test-Driven Development (TDD)
- Write tests for all database operations
- Test migrations up and down
- Test constraints and relationships
- Use transaction rollback for test isolation

### Schema Design Principles:
1. **Normalization** - Avoid data duplication
2. **Constraints** - Use database constraints (NOT NULL, UNIQUE, FK)
3. **Indexes** - Index foreign keys and frequently queried columns
4. **Audit trail** - Include created_at, updated_at on all tables
5. **Soft deletes** - Use deleted_at instead of hard deletes where appropriate

## Communication

### Creating Migrations:
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Add submissions table"
# Always review autogenerated migrations manually!
```

### Migration PR Template:
```markdown
## Database Migration: Add submissions table

**Tables affected:** submissions (new)
**Breaking change:** No
**Deployment notes:** Run migration before deploying new backend

### Schema:
- id (UUID, PK)
- user_id (UUID, FK to users)
- content (TEXT)
- submission_type (ENUM: text, image, video)
- status (ENUM: pending, processing, completed)
- created_at, updated_at

**Indexes:**
- user_id
- status
- created_at (for time-range queries)

**Tests:**
- [x] Migration runs successfully
- [x] Rollback works
- [x] Constraints enforced
- [x] Foreign keys work
```

### Request approval:
```markdown
@agent:architect Please review schema design
@agent:backend This adds the submissions table you'll need for the API
```

## Interaction with Other Agents

### With System Architect:
- Get approval for schema design decisions
- Coordinate on data architecture patterns

### With Backend Developer:
- Provide SQLAlchemy models after migrations
- Optimize queries based on usage patterns
- Create database utilities and helpers

### With AI/ML Engineer:
- Design vector storage for embeddings
- Optimize similarity search queries
- Create indexes for AI features

### With Integration Developer:
- Design data models for external integrations
- Plan caching strategy for external APIs

## PostgreSQL + pgvector Setup

### Vector Similarity Search:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE claim_embeddings (
    claim_id UUID PRIMARY KEY REFERENCES claims(id),
    embedding vector(1536),  -- OpenAI ada-002 dimension
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for similarity search
CREATE INDEX ON claim_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Example Workflows

### Adding a New Table:
1. Design schema (entities, relationships, constraints)
2. Create issue: `[TASK] Add [table_name] table`
3. Write tests for the new model first (TDD)
4. Create migration: `alembic revision --autogenerate`
5. Review migration SQL manually
6. Test migration up and down
7. Create SQLAlchemy model in `backend/app/models/`
8. Create PR with tests, migration, and model
9. Tag @agent:architect and @agent:backend for review

### Optimizing a Slow Query:
1. Use EXPLAIN ANALYZE to understand query plan
2. Identify missing indexes or inefficient joins
3. Create migration to add indexes
4. Test performance improvement
5. Document in PR

### Data Migration:
```python
# Example: Populate default values for new column
from alembic import op

def upgrade():
    # Add column
    op.add_column('users', sa.Column('role', sa.String(), nullable=True))
    
    # Populate existing rows
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
    
    # Make NOT NULL
    op.alter_column('users', 'role', nullable=False)

def downgrade():
    op.drop_column('users', 'role')
```

## Schema Naming Conventions

- **Tables**: plural snake_case (e.g., `fact_checks`, `user_submissions`)
- **Columns**: snake_case (e.g., `created_at`, `user_id`)
- **Indexes**: `idx_<table>_<columns>` (e.g., `idx_submissions_status`)
- **Foreign keys**: `fk_<table>_<referenced_table>` (e.g., `fk_submissions_users`)
- **Constraints**: `ck_<table>_<column>` (e.g., `ck_users_email_format`)

## Don't Do This:
❌ Create migrations without testing rollback
❌ Use VARCHAR without length limit
❌ Forget to add indexes on foreign keys
❌ Make schema changes without approval
❌ Skip transaction handling in migrations

## Do This:
✅ Always test migrations both ways (up and down)
✅ Add indexes thoughtfully based on query patterns
✅ Use database constraints to enforce data integrity
✅ Document complex migrations
✅ Coordinate schema changes with affected agents
"""
    
    # Backend Developer Agent
    backend_def = """# Backend Developer Agent

## Role & Responsibilities

You are the **Backend Developer** for the Ans project. You implement FastAPI endpoints, business logic, and data processing.

### Core Responsibilities:
- Implement FastAPI REST API endpoints
- Write business logic and service layer
- Integrate with database (SQLAlchemy)
- Implement authentication and authorization
- Handle background job processing
- Integrate with BENEDMO API
- Ensure API documentation is up-to-date

## Working Approach

### Test-Driven Development (TDD) - MANDATORY
1. **Write test FIRST** before any implementation
2. Run test - it should fail (red)
3. Write minimal code to pass test (green)
4. Refactor while keeping tests passing
5. Repeat

### API Development Flow:
1. Define API contract (request/response models)
2. Write endpoint tests (FastAPI TestClient)
3. Implement endpoint
4. Write service layer tests
5. Implement service logic
6. Write integration tests
7. Update OpenAPI docs

## Tech Stack

- **FastAPI** - Async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **pytest + pytest-asyncio** - Testing
- **httpx** - Async HTTP client (for BENEDMO)

## Communication

### Creating Issues:
```markdown
# [TASK] Implement submission API endpoint

## Description
Create POST /api/v1/submissions endpoint to receive fact-check requests

## Acceptance Criteria
- [ ] Tests written first (TDD)
- [ ] Request validation with Pydantic
- [ ] Store submission in database
- [ ] Return submission ID
- [ ] Handle errors gracefully
- [ ] OpenAPI docs generated

## Dependencies
Blocked by: #XX (Database schema for submissions)

## API Contract
POST /api/v1/submissions
Request: {content: str, type: "text"|"image"|"url"}
Response: {id: UUID, status: "pending", created_at: datetime}
```

### Code Review Comments:
```markdown
@agent:architect This introduces a new service pattern, PTAL
@agent:database Can you verify the query optimization here?
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── submissions.py
│   │   │   │   ├── users.py
│   │   │   │   └── factchecks.py
│   │   │   └── router.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── submission.py
│   │   ├── user.py
│   │   └── factcheck.py
│   ├── schemas/  # Pydantic models
│   │   ├── submission.py
│   │   └── user.py
│   ├── services/
│   │   ├── submission_service.py
│   │   ├── benedmo_service.py
│   │   └── matching_service.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── tests/
│   │   ├── api/
│   │   ├── services/
│   │   └── conftest.py
│   └── main.py
```

## Example: TDD Workflow

### Step 1: Write Test First
```python
# tests/api/test_submissions.py
import pytest
from fastapi.testclient import TestClient

def test_create_submission(client: TestClient, db_session):
    \"\"\"Test creating a new submission\"\"\"
    # Arrange
    payload = {
        "content": "Is this claim true?",
        "type": "text"
    }
    
    # Act
    response = client.post("/api/v1/submissions", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert data["content"] == payload["content"]
```

### Step 2: Run Test (should fail)
```bash
pytest tests/api/test_submissions.py::test_create_submission
# Expected: FAILED (endpoint doesn't exist yet)
```

### Step 3: Implement Endpoint
```python
# app/api/v1/endpoints/submissions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.submission import SubmissionCreate, SubmissionResponse
from app.services import submission_service
from app.api.dependencies import get_db

router = APIRouter()

@router.post(
    "/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_submission(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Create a new fact-check submission\"\"\"
    return await submission_service.create(db, submission)
```

### Step 4: Write Service Tests
```python
# tests/services/test_submission_service.py
import pytest
from app.services import submission_service
from app.schemas.submission import SubmissionCreate

@pytest.mark.asyncio
async def test_create_submission_service(db_session):
    \"\"\"Test submission service creates record\"\"\"
    # Arrange
    data = SubmissionCreate(content="Test claim", type="text")
    
    # Act
    result = await submission_service.create(db_session, data)
    
    # Assert
    assert result.id is not None
    assert result.status == "pending"
    assert result.content == "Test claim"
```

### Step 5: Implement Service
```python
# app/services/submission_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.submission import Submission
from app.schemas.submission import SubmissionCreate

async def create(db: AsyncSession, data: SubmissionCreate) -> Submission:
    \"\"\"Create a new submission\"\"\"
    submission = Submission(
        content=data.content,
        submission_type=data.type,
        status="pending"
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission
```

### Step 6: Run All Tests
```bash
pytest tests/api/test_submissions.py tests/services/test_submission_service.py
# Expected: PASSED
```

## Integration with Other Agents

### With Database Architect:
```markdown
@agent:database The submissions query is slow with 10k records.
Can we add an index on (status, created_at)?
```

### With Integration Developer:
```markdown
@agent:integration I've created the webhook handler interface.
Can you implement the Snapchat-specific logic?

See: app/api/v1/endpoints/webhooks.py:handle_webhook()
```

### With AI/ML Engineer:
```markdown
@agent:ai Backend is ready to call your similarity search.
POST /api/ai/similarity {claim_text: str} -> {matches: []}
Can you implement this endpoint?
```

## API Design Best Practices

### Use Pydantic for Validation:
```python
from pydantic import BaseModel, Field, validator

class SubmissionCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000)
    type: Literal["text", "image", "video"]
    
    @validator("content")
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v
```

### Error Handling:
```python
from fastapi import HTTPException, status

async def get_submission(submission_id: UUID, db: AsyncSession):
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    return submission
```

### Async/Await Everywhere:
```python
# Good - Async
async def create_submission(data: SubmissionCreate, db: AsyncSession):
    submission = Submission(**data.dict())
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission

# Bad - Blocking
def create_submission(data: SubmissionCreate, db: Session):  # ❌
    submission = Submission(**data.dict())
    db.add(submission)
    db.commit()  # Blocks event loop!
    return submission
```

## Testing Strategy

### Test Pyramid:
- **70% Unit tests** - Service layer, utilities
- **20% Integration tests** - API endpoints with database
- **10% E2E tests** - Full user workflows

### Fixtures (conftest.py):
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

@pytest.fixture
async def db_session():
    \"\"\"Provide a test database session\"\"\"
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test")
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(db_session):
    \"\"\"Provide a test client\"\"\"
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
```

## Don't Do This:
❌ Write code before tests (TDD is mandatory!)
❌ Use blocking I/O in async functions
❌ Skip input validation
❌ Ignore error handling
❌ Commit without running tests

## Do This:
✅ Write tests first, every time (TDD)
✅ Use async/await for all I/O operations
✅ Validate all inputs with Pydantic
✅ Handle errors gracefully with proper HTTP status codes
✅ Keep endpoints thin, business logic in services
✅ Document API with docstrings (they become OpenAPI docs)
"""
    
    agents = {
        '01-system-architect.md': architect_def,
        '02-database-architect.md': database_def,
        '03-backend-developer.md': backend_def,
    }
    
    for filename, content in agents.items():
        filepath = agent_dir / filename
        if filepath.exists():
            print_warning(f"Agent definition {filename} already exists, skipping")
            continue
        
        filepath.write_text(content)
        print_success(f"Created agent definition: {filename}")
    
    # Note about remaining agents
    print(f"\n{Color.YELLOW}NOTE: Additional agent definitions (Frontend, AI/ML, Integration, DevOps){Color.END}")
    print(f"{Color.YELLOW}will be created in the next iteration or can be generated as needed.{Color.END}")


def create_wiki_initialization_guide():
    """Create a guide for initializing the GitHub Wiki"""
    print_step("Step 8b: GitHub Wiki Initialization Guide")
    
    wiki_guide = """# GitHub Wiki Initialization Guide

## Manual Steps Required

GitHub Wiki is a separate git repository and cannot be fully automated via API.
Follow these steps to initialize it:

### 1. Enable Wiki
1. Go to your repository on GitHub
2. Click Settings → Features
3. Check ✅ "Wikis"

### 2. Create Home Page
1. Go to Wiki tab in your repository
2. Click "Create the first page"
3. Title: "Home"
4. Copy the content below:

---

# Ans Project Documentation

Welcome to the Ans project documentation. Ans is a Snapchat fact-checking service for Amsterdam youth.

## Quick Links
- [[Getting Started]]
- [[Architecture]]
- [[Agent Workflows]]
- [[Testing Standards]]

## For New Developers
1. Read [[Development Setup]]
2. Review [[Architecture Overview]]
3. Check [[Contributing Guidelines]]
4. Join the team on GitHub

## Project Overview
Ans allows youth to submit questionable content via Snapchat DM for fact-checking. The system combines AI analysis (OpenAI) with human verification through a volunteer network.

### Tech Stack
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0
- Frontend: Svelte 5, TypeScript, Vite
- Database: PostgreSQL with pgvector
- AI: OpenAI API
- Infrastructure: Docker on Hetzner VPS

### Repository Structure
- `/backend` - FastAPI application
- `/frontend` - Svelte application
- `/ai-service` - OpenAI integration service
- `/infrastructure` - Docker and deployment configs
- `/docs/adr` - Architecture Decision Records
- `/docs/agents` - Agent role definitions

---

### 3. Create Additional Pages

Create these pages (leave content as placeholder for now):

**Getting Started**
- Development Setup
- Running Tests
- Deployment Guide

**Architecture**
- System Overview
- ADR Index
- Database Schema
- API Documentation

**Agent Workflows**
- Backend Development Guide
- Frontend Development Guide
- AI/ML Development Guide
- Testing Standards

**Testing Standards**
- TDD Guidelines
- Coverage Requirements
- Test Types and Structure

### 4. Clone Wiki for Local Editing (Optional)

```bash
# Clone the wiki repository
git clone https://github.com/YOUR-ORG/ans-project.wiki.git

# Add pages
cd ans-project.wiki
# Edit .md files
git add .
git commit -m "Add initial documentation"
git push
```

## Wiki Maintenance

- Agents should update Wiki when making architectural changes
- System Architect maintains Architecture section
- Database Architect maintains Database Schema
- DevOps maintains Getting Started guides
"""
    
    guide_path = Path('docs/WIKI_SETUP.md')
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    
    if guide_path.exists():
        print_warning("Wiki guide already exists, skipping")
    else:
        guide_path.write_text(wiki_guide)
        print_success("Created Wiki initialization guide: docs/WIKI_SETUP.md")
    
    print(f"\n{Color.YELLOW}⚠ Manual action required:{Color.END}")
    print(f"  Follow instructions in {Color.BOLD}docs/WIKI_SETUP.md{Color.END} to set up GitHub Wiki")


def commit_all_changes():
    """Commit all changes to git"""
    print_step("Committing All Changes")
    
    # Check if there are changes to commit
    success, output = run_command(['git', 'status', '--porcelain'], capture_output=True)
    
    if not output.strip():
        print_warning("No changes to commit")
        return
    
    # Add all files
    success, _ = run_command(['git', 'add', '.'])
    if not success:
        print_error("Failed to stage files")
        return
    
    # Commit
    commit_message = """chore: automated setup for multi-agent development

- Add GitHub labels for team, agent, priority, status, area
- Add issue templates (bug, feature, task) and PR template
- Add CI/CD workflows (backend tests, frontend tests, AI tests, security)
- Add Docker infrastructure (docker-compose.dev.yml, Makefile, .env.example)
- Add agent role definitions (architect, database, backend)
- Add wiki setup guide

Automated by setup_ans_project.py
"""
    
    success, _ = run_command(['git', 'commit', '-m', commit_message])
    if success:
        print_success("Changes committed to develop branch")
    else:
        print_error("Failed to commit changes")
        return
    
    # Push to develop
    print("\nPushing to GitHub...")
    success, _ = run_command(['git', 'push', 'origin', 'develop'])
    if success:
        print_success("Changes pushed to origin/develop")
    else:
        print_error("Failed to push changes")


def print_summary():
    """Print setup summary and next steps"""
    print_step("Setup Complete! 🎉")
    
    summary = f"""
{Color.GREEN}{Color.BOLD}✓ GitHub labels created{Color.END}
{Color.GREEN}{Color.BOLD}✓ Milestones created{Color.END}
{Color.GREEN}{Color.BOLD}✓ Issue templates added{Color.END}
{Color.GREEN}{Color.BOLD}✓ CI/CD workflows configured{Color.END}
{Color.GREEN}{Color.BOLD}✓ Docker infrastructure ready{Color.END}
{Color.GREEN}{Color.BOLD}✓ Agent definitions created{Color.END}

{Color.BOLD}Next Steps:{Color.END}

1. {Color.YELLOW}Set up GitHub Wiki{Color.END}
   Follow instructions in: docs/WIKI_SETUP.md

2. {Color.YELLOW}Configure Branch Protection{Color.END}
   Repository Settings → Branches → Add rules for 'main' and 'develop'
   
   For 'main':
   - Require pull request reviews (1 approval)
   - Require status checks: backend-tests, frontend-tests, ai-service-tests, security-scan
   - Require branches to be up to date
   
   For 'develop':
   - Require pull request reviews (1 approval)
   - Require status checks (same as main)
   - Allow auto-merge

3. {Color.YELLOW}Add GitHub Secrets{Color.END}
   Repository Settings → Secrets and variables → Actions
   Add: OPENAI_API_KEY_TEST (for testing)

4. {Color.YELLOW}Create Initial Epic Issues{Color.END}
   Use the GitHub Projects board to create epics for:
   - Snapchat Integration
   - BENEDMO Integration
   - AI Content Analysis
   - Admin Panel
   - Volunteer Dashboard

5. {Color.YELLOW}Set Up Claude Code Subagents{Color.END}
   - Open VS Code in this repository
   - Use Claude Code extension
   - Load agent definitions from docs/agents/
   - Start first sprint!

6. {Color.YELLOW}Create .env file{Color.END}
   cp .env.example .env
   # Fill in your API keys

{Color.BOLD}Quick Start Commands:{Color.END}

  make setup    # Build Docker containers
  make dev      # Start development environment
  make test     # Run all tests
  make lint     # Run linters

{Color.BOLD}Documentation:{Color.END}

  - Agent definitions: docs/agents/
  - Wiki guide: docs/WIKI_SETUP.md
  - ADRs: docs/adr/ (to be created by architect agent)

{Color.GREEN}{Color.BOLD}Ready to start multi-agent development! 🚀{Color.END}
"""
    
    print(summary)


def main():
    """Main setup function"""
    print(f"\n{Color.BOLD}{Color.BLUE}")
    print("=" * 60)
    print("  Ans Project - Multi-Agent Development Setup")
    print("=" * 60)
    print(f"{Color.END}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("\nPrerequisites not met. Please install missing tools and try again.")
        sys.exit(1)
    
    # Run setup steps
    try:
        create_github_labels()
        create_milestones()
        create_issue_templates()
        create_workflows()
        create_docker_infrastructure()
        create_agent_definitions()
        create_wiki_initialization_guide()
        
        # Commit changes
        commit_all_changes()
        
        # Print summary
        print_summary()
        
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}Setup interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nSetup failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()