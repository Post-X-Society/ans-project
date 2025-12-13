# Ans Backend API

FastAPI backend for the Ans fact-checking service.

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15 with pgvector extension
- Redis

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (when available)
alembic upgrade head
```

## Development

### Running the Server

```bash
# Development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_health.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black app/

# Lint code
ruff app/

# Type checking
mypy app/
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── health.py      # Health check endpoint
│   ├── core/
│   │   ├── config.py              # Application configuration
│   │   └── database.py            # Database setup
│   ├── models/                    # SQLAlchemy models (to be added)
│   ├── schemas/                   # Pydantic schemas (to be added)
│   ├── services/                  # Business logic (to be added)
│   ├── tests/
│   │   ├── conftest.py            # Pytest fixtures
│   │   └── test_health.py         # Health endpoint tests
│   └── main.py                    # FastAPI application
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Project configuration
└── README.md                      # This file
```

## Test-Driven Development (TDD)

This project follows TDD principles:

1. **Write tests FIRST** before implementation
2. Run tests - they should fail (RED)
3. Write minimal code to pass tests (GREEN)
4. Refactor while keeping tests passing (REFACTOR)

See [docs/agents/03-backend-developer.md](../docs/agents/03-backend-developer.md) for detailed TDD workflow.

## API Endpoints

### Health Check
- `GET /health` - Returns service status

### Root
- `GET /` - API information and documentation links

## Environment Variables

See `.env.example` for all available configuration options.

## Contributing

1. Pick an issue from the GitHub Project
2. Create a feature branch: `feature/backend/your-feature`
3. Write tests FIRST (TDD)
4. Implement feature
5. Ensure tests pass and coverage ≥ 80%
6. Create Pull Request

See [docs/AGENT_COORDINATION.md](../docs/AGENT_COORDINATION.md) for full workflow.
