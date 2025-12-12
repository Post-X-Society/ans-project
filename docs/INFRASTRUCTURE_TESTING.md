# Infrastructure Testing Guide

This document provides instructions for testing the Docker development infrastructure.

**For:** DevOps/QA Engineer Agent
**Related:** Issue #1 - Project Infrastructure Setup
**ADR:** [0001-docker-development-environment.md](adr/0001-docker-development-environment.md)

## Prerequisites

Before testing, ensure you have:
- Docker Desktop installed (or Docker Engine + Docker Compose)
- Git repository cloned
- `.env` file created (copy from `.env.example`)

## Testing Checklist

### 1. ✅ Verify Docker Installation

```bash
docker --version
docker-compose --version
```

Expected: Both commands should return version numbers.

### 2. ✅ Build Containers

```bash
make docker-build
# OR
docker-compose -f infrastructure/docker-compose.dev.yml build
```

**Expected Results:**
- All images build successfully
- No build errors
- Layers are cached for faster rebuilds

**Common Issues:**
- If build fails on backend: Check `backend/pyproject.toml` dependencies
- If build fails on frontend: Frontend agent hasn't initialized project yet (expected)

### 3. ✅ Start Services

```bash
make dev
# OR
docker-compose -f infrastructure/docker-compose.dev.yml up -d
```

**Expected Results:**
- All services start: postgres, redis, backend
- Frontend may fail until Frontend Developer agent initializes it
- Health checks pass

**Verify with:**
```bash
make status
# OR
docker-compose -f infrastructure/docker-compose.dev.yml ps
```

### 4. ✅ Test PostgreSQL + pgvector

```bash
make db-shell
# Inside psql:
SELECT * FROM pg_extension WHERE extname = 'vector';
\q
```

**Expected:** pgvector extension should be listed.

### 5. ✅ Test Redis

```bash
make redis-shell
# Inside redis-cli:
PING
# Expected: PONG
exit
```

### 6. ✅ Test Backend Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "ans-backend",
  "version": "0.1.0"
}
```

**If it fails:**
- Check logs: `make docker-logs-backend`
- Verify backend code exists in `backend/app/`
- Check dependencies installed correctly

### 7. ✅ Test Backend API Docs

Open browser: http://localhost:8000/docs

**Expected:** FastAPI Swagger UI should load

### 8. ✅ Test Frontend (After Frontend Agent Initializes)

Open browser: http://localhost:5173

**Expected:** Svelte dev server running
**Note:** Will fail until Frontend Developer agent creates the project

### 9. ✅ Test Hot Reload (Backend)

1. Make a change to `backend/app/main.py`
2. Watch logs: `make docker-logs-backend`
3. Verify: "Detected file change, reloading..." message appears
4. Test endpoint to confirm change applied

### 10. ✅ Test Database Connectivity from Backend

```bash
# Access backend shell
make backend-shell

# Inside container, run Python:
python3 << EOF
from app.core.database import engine
import asyncio

async def test_db():
    async with engine.begin() as conn:
        result = await conn.execute("SELECT version()")
        print(result.scalar())

asyncio.run(test_db())
EOF
```

**Expected:** PostgreSQL version printed

## Performance Benchmarks

Document these metrics for future comparison:

- **Build time (first build):** ________ seconds
- **Build time (cached):** ________ seconds
- **Startup time (all services healthy):** ________ seconds
- **Backend response time (/health):** ________ ms
- **Memory usage (all services):** ________ MB

Check with:
```bash
docker stats --no-stream
```

## Security Checks

### ✅ Environment Variables
- Verify `.env` is in `.gitignore`
- Confirm no secrets in docker-compose.yml
- Check OPENAI_API_KEY is loaded from environment

### ✅ Network Isolation
```bash
docker network inspect ans-network
```

- Verify services are on isolated network
- Check no unnecessary ports exposed

## Cleanup

```bash
make clean
# OR
docker-compose -f infrastructure/docker-compose.dev.yml down -v
```

**Verify:**
- All containers stopped
- Volumes removed (data cleared)

## Known Issues & Workarounds

### Issue: Frontend fails to start
**Cause:** Frontend project not initialized yet
**Workaround:** Comment out frontend service in docker-compose until Frontend Developer agent creates it

### Issue: Permission errors on Linux
**Cause:** Docker volume permissions
**Workaround:**
```bash
sudo chown -R $USER:$USER backend/ frontend/
```

### Issue: Port already in use
**Cause:** Another service using 5432, 6379, 8000, or 5173
**Workaround:** Change ports in docker-compose.dev.yml

## Success Criteria

Infrastructure testing is complete when:

- [ ] All services build successfully
- [ ] postgres + redis start and pass health checks
- [ ] backend starts and `/health` returns 200
- [ ] pgvector extension is installed
- [ ] Hot reload works for backend
- [ ] Database accessible from backend
- [ ] No security issues found
- [ ] Performance benchmarks documented
- [ ] ADR-0001 reviewed and approved

## Next Steps

After infrastructure testing passes:

1. **Backend Developer:** Implement health endpoint tests (if not done)
2. **Frontend Developer:** Initialize Svelte 5 project
3. **Database Architect:** Create initial schema migrations
4. **DevOps:** Add CI/CD integration for Docker builds

## Reporting Issues

If you find issues:

1. Document the issue clearly
2. Include error messages and logs
3. Comment on issue #1 with findings
4. Tag @agent:architect for architectural issues
5. Tag @agent:backend or @agent:frontend for service-specific issues

---

**Testing completed by:** _________
**Date:** _________
**Status:** [ ] Pass / [ ] Fail
**Notes:** _________
