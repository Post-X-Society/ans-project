# ADR-0001: Docker Development Environment Structure

## Status
Accepted

## Context
The Ans project requires a consistent development environment that works across different developer machines and CI/CD pipelines. We need to support:
- Backend (Python/FastAPI)
- Frontend (Svelte 5)
- PostgreSQL with pgvector extension
- Redis for caching
- Hot reload for development
- Easy onboarding for new developers

## Decision
We will use Docker Compose for local development with the following structure:

### Services:
1. **postgres** - PostgreSQL 15 with pgvector extension
   - Image: `pgvector/pgvector:pg15`
   - Port: 5432
   - Includes initialization script for pgvector setup

2. **redis** - Redis 7 for caching and job queues
   - Image: `redis:7-alpine`
   - Port: 6379

3. **backend** - FastAPI application
   - Built from `backend/Dockerfile`
   - Port: 8000
   - Hot reload enabled via volume mounts
   - Health check at `/health`

4. **frontend** - Svelte 5 application
   - Built from `frontend/Dockerfile`
   - Port: 5173
   - Hot reload enabled via volume mounts

### Key Features:
- **Volume Mounts**: Code changes reflect immediately without rebuilding
- **Health Checks**: All services have health checks for reliable startup
- **Networking**: All services on shared `ans-network` bridge
- **Dependency Management**: Services start in correct order using `depends_on` with health conditions

### Developer Experience:
- **Makefile** provides convenient commands:
  - `make setup` - Initial project setup
  - `make dev` - Start all services
  - `make test` - Run all tests
  - `make db-shell` - Access PostgreSQL
  - `make docker-logs` - View logs

## Consequences

### Positive:
- ✅ Consistent environment across all developers
- ✅ Fast onboarding (just `make setup && make dev`)
- ✅ Hot reload speeds up development
- ✅ Easy to add new services (just update docker-compose.yml)
- ✅ CI/CD can use same Docker setup for testing
- ✅ pgvector extension automatically configured

### Negative:
- ⚠️ Requires Docker installed on developer machines
- ⚠️ Initial build can be slow (mitigated by layer caching)
- ⚠️ Volume mounts may have performance issues on some OS (especially macOS)

### Mitigations:
- Provide clear documentation for Docker installation
- Use `.dockerignore` to minimize build context
- Consider Docker Desktop alternatives if performance is an issue

## Alternatives Considered

### 1. Virtual Environment + Manual Services
- **Pros**: No Docker requirement, potentially faster
- **Cons**: Inconsistent environments, complex setup docs, pgvector setup difficult
- **Rejected**: Too much setup friction for new developers

### 2. Full Kubernetes (kind/minikube)
- **Pros**: Production-like environment
- **Cons**: Overkill for local development, slow, complex
- **Rejected**: Unnecessary complexity for MVP phase

### 3. Docker Compose with Remote Services
- **Pros**: Faster startup, less resource usage
- **Cons**: Requires external service dependencies, not portable
- **Rejected**: Not suitable for offline development

## Implementation Notes

### File Structure:
```
infrastructure/
├── docker-compose.dev.yml    # Development environment
├── init-db.sql               # PostgreSQL initialization
backend/
├── Dockerfile                # Backend container
frontend/
├── Dockerfile                # Frontend container
Makefile                      # Convenience commands
```

### Next Steps:
1. ✅ Create docker-compose.dev.yml
2. ✅ Create Dockerfiles for backend and frontend
3. ✅ Create Makefile
4. ⏳ Test infrastructure (Backend Developer agent + DevOps agent)
5. ⏳ Create production docker-compose.prod.yml (DevOps agent)
6. ⏳ Add CI/CD integration (DevOps agent)

## References
- Docker Compose documentation: https://docs.docker.com/compose/
- pgvector: https://github.com/pgvector/pgvector
- FastAPI with Docker: https://fastapi.tiangolo.com/deployment/docker/
- Vite Docker setup: https://vitejs.dev/guide/

## Author
System Architect Agent

## Date
2025-12-12

## Related Issues
- #1 - Project Infrastructure Setup
