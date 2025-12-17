# Infrastructure Testing Checklist

This document provides a comprehensive checklist for testing the Docker development environment setup.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2.0+
- Git repository cloned
- Terminal access

## Testing Checklist

### 1. Docker Services Startup

**Objective**: Verify all Docker services start successfully and reach healthy status.

```bash
cd "/path/to/ans-project"
docker compose -f infrastructure/docker-compose.dev.yml up -d
docker compose -f infrastructure/docker-compose.dev.yml ps
```

**Expected Result**:
- All 4 services running: postgres, redis, backend, frontend
- Status shows "Up" and "healthy" for postgres, redis, and backend
- No error messages in output

**Pass Criteria**:
- [ ] All containers start without errors
- [ ] PostgreSQL shows "healthy" status
- [ ] Redis shows "healthy" status
- [ ] Backend shows "healthy" status
- [ ] Frontend shows "Up" status

### 2. Backend Health Endpoint

**Objective**: Test backend API health endpoint responds correctly.

```bash
curl http://localhost:8000/api/v1/health
```

**Expected Result**:
```json
{
    "status": "healthy",
    "service": "ans-backend",
    "version": "0.1.0"
}
```

**Pass Criteria**:
- [ ] Returns HTTP 200 OK
- [ ] Returns valid JSON
- [ ] Contains "status": "healthy"
- [ ] Contains "service" and "version" fields

### 3. Database Connectivity with pgvector

**Objective**: Verify PostgreSQL database is accessible and pgvector extension is installed.

```bash
# Test basic connectivity
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT 1 as test;"

# Verify pgvector extension
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Test vector functionality
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT '[1,2,3]'::vector;"
```

**Expected Result**:
- First query returns `1`
- Second query shows `vector | 0.8.1` (or higher)
- Third query returns the vector without errors

**Pass Criteria**:
- [ ] Database accepts connections
- [ ] pgvector extension is installed
- [ ] Vector operations work correctly
- [ ] Can create and query vector columns

### 4. Redis Connectivity

**Objective**: Verify Redis is accessible and accepting commands.

```bash
# Test Redis ping
docker exec ans-redis redis-cli ping

# Test set/get operations
docker exec ans-redis redis-cli SET test_key "test_value"
docker exec ans-redis redis-cli GET test_key
docker exec ans-redis redis-cli DEL test_key
```

**Expected Result**:
- First command returns `PONG`
- SET returns `OK`
- GET returns `"test_value"`
- DEL returns `(integer) 1`

**Pass Criteria**:
- [ ] Redis responds to PING
- [ ] Can SET values
- [ ] Can GET values
- [ ] Can DELETE values

### 5. Hot Reload - Backend

**Objective**: Verify backend code changes trigger automatic reload.

```bash
# Watch backend logs
docker logs -f ans-backend

# In another terminal, make a small change to any Python file
# For example, add a comment to app/main.py
```

**Expected Result**:
- Logs show `Detected changes in...`
- Server reloads automatically
- No manual restart needed

**Pass Criteria**:
- [ ] Code changes are detected
- [ ] Server reloads automatically
- [ ] API remains accessible after reload
- [ ] No errors during reload

### 6. Hot Reload - Frontend

**Objective**: Verify frontend code changes trigger HMR (Hot Module Replacement).

```bash
# Watch frontend logs
docker logs -f ans-frontend

# Make a small change to frontend/src/routes/+page.svelte
# Browser should update without manual refresh
```

**Expected Result**:
- Vite detects file changes
- Browser updates via HMR
- No full page reload needed

**Pass Criteria**:
- [ ] File changes are detected
- [ ] HMR updates browser automatically
- [ ] Console shows no errors
- [ ] Application state is preserved

### 7. Backend Test Suite

**Objective**: Run backend test suite and verify coverage meets requirements.

```bash
# Run all tests
docker exec ans-backend pytest -v

# Run with coverage report
docker exec ans-backend pytest --cov=app --cov-report=term-missing

# Run specific test file
docker exec ans-backend pytest app/tests/test_health.py -v
```

**Expected Result**:
- All tests pass (or known failures documented)
- Coverage meets minimum threshold (80%)
- No critical warnings

**Pass Criteria**:
- [ ] Test suite runs successfully
- [ ] Coverage is at least 80%
- [ ] No unexpected test failures
- [ ] Test output is clear and informative

### 8. Frontend Accessibility

**Objective**: Verify frontend is accessible from browser.

```bash
# Test HTTP response
curl -I http://localhost:5173/

# Check if frontend serves content
curl http://localhost:5173/ | head -n 20
```

**Expected Result**:
- Returns HTTP 200 OK
- HTML content is served
- No error pages

**Pass Criteria**:
- [ ] Frontend responds on port 5173
- [ ] Returns valid HTML
- [ ] Browser can access http://localhost:5173
- [ ] No CORS or network errors

### 9. End-to-End Form Submission

**Objective**: Test complete flow from frontend to database.

```bash
# Submit a test form via API
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test claim that should be long enough to pass validation requirements for the submission endpoint",
    "submission_type": "text"
  }'

# Verify in database
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT id, content, submission_type FROM submissions ORDER BY created_at DESC LIMIT 1;"
```

**Expected Result**:
- API returns 201 Created with submission ID
- Database contains the submitted data
- Timestamps are correctly set

**Pass Criteria**:
- [ ] API accepts submission
- [ ] Returns valid response with ID
- [ ] Data is persisted in database
- [ ] All fields are correctly stored

### 10. Service Dependencies

**Objective**: Verify services start in correct order with dependencies.

```bash
# Stop all services
docker compose -f infrastructure/docker-compose.dev.yml down

# Start and watch initialization order
docker compose -f infrastructure/docker-compose.dev.yml up
```

**Expected Result**:
- PostgreSQL starts first
- Redis starts first
- Backend waits for database health check
- Frontend waits for backend health check

**Pass Criteria**:
- [ ] PostgreSQL is healthy before backend starts
- [ ] Redis is healthy before backend starts
- [ ] Backend is healthy before frontend starts
- [ ] No race condition errors

### 11. Volume Persistence

**Objective**: Verify data persists across container restarts.

```bash
# Create test data
docker exec ans-postgres psql -U postgres -d ans_dev -c "CREATE TABLE test_persistence (id INT, value TEXT);"
docker exec ans-postgres psql -U postgres -d ans_dev -c "INSERT INTO test_persistence VALUES (1, 'test');"

# Restart containers
docker compose -f infrastructure/docker-compose.dev.yml restart postgres

# Verify data still exists
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT * FROM test_persistence;"

# Cleanup
docker exec ans-postgres psql -U postgres -d ans_dev -c "DROP TABLE test_persistence;"
```

**Expected Result**:
- Data survives container restart
- No data loss

**Pass Criteria**:
- [ ] PostgreSQL data persists after restart
- [ ] Redis data persists after restart
- [ ] Volumes are correctly mounted

### 12. Environment Variables

**Objective**: Verify environment variables are correctly passed to containers.

```bash
# Check backend environment
docker exec ans-backend env | grep -E "(DATABASE_URL|REDIS_URL|DEBUG)"

# Verify backend can connect to dependencies
docker exec ans-backend python -c "import os; print('DB:', os.getenv('DATABASE_URL')); print('Redis:', os.getenv('REDIS_URL'))"
```

**Expected Result**:
- DATABASE_URL points to postgres service
- REDIS_URL points to redis service
- DEBUG is set to true

**Pass Criteria**:
- [ ] All required environment variables are set
- [ ] URLs use correct Docker service names
- [ ] API keys are accessible (if configured)

## Issue Tracking

### Known Issues

1. **Health Endpoint Test Failures** (4 tests)
   - **Issue**: Tests expect `/health` but endpoint is at `/api/v1/health`
   - **Impact**: Test suite shows 4 failures
   - **Status**: Needs fix in backend tests
   - **Severity**: Low (tests need update, not code)

2. **Docker Compose Version Warning**
   - **Issue**: Warning about obsolete `version` attribute in docker-compose.dev.yml
   - **Impact**: Non-critical warning message
   - **Status**: Should be removed
   - **Severity**: Low (cosmetic)

### Resolved Issues

- SSR to SPA migration (See POST_MORTEM_SSR_MIGRATION.md)
- Docker networking for browser-based API calls
- Frontend hot reload with preserved node_modules

## Troubleshooting Guide

### Services Won't Start

```bash
# Check for port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Check Docker logs
docker compose -f infrastructure/docker-compose.dev.yml logs
```

### Database Connection Errors

```bash
# Verify PostgreSQL is accepting connections
docker exec ans-postgres pg_isready -U postgres

# Check if database exists
docker exec ans-postgres psql -U postgres -l
```

### Frontend Can't Reach Backend

- Verify backend is running: `curl http://localhost:8000/api/v1/health`
- Check browser console for CORS errors
- Ensure `VITE_API_URL` is not set (should use default `http://localhost:8000`)
- Perform hard browser refresh (Cmd+Shift+R or Ctrl+Shift+R)

### Hot Reload Not Working

**Backend**:
```bash
# Verify volumes are mounted
docker inspect ans-backend | grep -A 20 Mounts

# Restart container
docker compose -f infrastructure/docker-compose.dev.yml restart backend
```

**Frontend**:
```bash
# Clear Vite cache
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit

# Rebuild frontend
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend
```

## Success Criteria Summary

Infrastructure is considered fully functional when:

- [ ] All 12 checklist items pass
- [ ] No critical issues remain
- [ ] Test coverage is at least 80%
- [ ] Documentation is complete
- [ ] Known issues are tracked in GitHub

## References

- Docker Compose Documentation: https://docs.docker.com/compose/
- FastAPI Health Checks: https://fastapi.tiangolo.com/advanced/
- Vite HMR: https://vitejs.dev/guide/features.html#hot-module-replacement
- pgvector: https://github.com/pgvector/pgvector
- Post-Mortem: SSR Migration: `docs/POST_MORTEM_SSR_MIGRATION.md`

---

**Last Updated**: 2025-12-14
**Reviewed By**: DevOps/QA Engineer
**Status**: Active
