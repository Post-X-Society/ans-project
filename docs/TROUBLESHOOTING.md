# Troubleshooting Guide

Quick lookup guide for common issues encountered during development. Organized by error message and symptom for fast resolution.

**Last Updated**: 2025-12-15
**Maintainer**: DevOps/QA Engineer

---

## Quick Index

Jump directly to your issue:

### SSR and Frontend Issues
- ["location is not defined" during SSR](#location-is-not-defined)
- ["XMLHttpRequest cannot load http://backend:8000"](#xmlhttprequest-cannot-load)
- [Blank page after environment changes](#blank-page-after-environment-changes)
- [Vite cache corruption / stale code](#vite-cache-corruption)
- [Hard refresh not working](#hard-refresh-not-working)

### Docker Networking Issues
- [Frontend can't reach backend](#frontend-cant-reach-backend)
- [VITE_API_URL confusion](#vite_api_url-confusion)
- [Browser vs container networking](#browser-vs-container-networking)

### Common Docker Issues
- [Port already in use (5432, 6379, 8000, 5173)](#port-already-in-use)
- [Services won't start](#services-wont-start)
- [Volume permission issues](#volume-permission-issues)
- [Hot reload not working](#hot-reload-not-working)

### Database Issues
- ["database does not exist"](#database-does-not-exist)
- ["pgvector extension not found"](#pgvector-extension-not-found)
- [Connection refused / can't connect](#database-connection-refused)

### Backend Issues
- [ModuleNotFoundError / import errors](#moduleerror-backend)
- [Uvicorn not reloading](#uvicorn-not-reloading)
- [Tests failing with import errors](#tests-failing-import-errors)

### Frontend Issues
- ["Cannot find module" in frontend](#cannot-find-module-frontend)
- [npm dependencies not installed](#npm-dependencies-not-installed)

### Test Issues
- [Coverage below 80%](#coverage-below-80)
- [Path issues in tests (e.g., /health vs /api/v1/health)](#path-issues-in-tests)

### Nuclear Option
- [Clean slate / start from scratch](#clean-slate)

---

## SSR and Frontend Issues

### "location is not defined"

**Symptom**: Frontend shows blank page with `ReferenceError: location is not defined` in console

**Error Message**:
```
ReferenceError: location is not defined
    at client.ts:XX
```

**Cause**: Axios interceptors or other code trying to access browser-only objects (window, location, document) during server-side rendering. This happens when SvelteKit runs code on the server that expects browser APIs.

**Solution**:

Option 1 - Wrap code in browser check:
```typescript
import { browser } from '$app/environment';

if (browser) {
  // Only runs in browser
  apiClient.interceptors.request.use(...);
}
```

Option 2 - Disable SSR completely (recommended for SPAs):
```bash
# 1. Install static adapter
cd frontend
npm install -D @sveltejs/adapter-static

# 2. Update svelte.config.js
# Change adapter-auto to adapter-static

# 3. Create src/routes/+layout.js
echo "export const ssr = false;" > src/routes/+layout.js

# 4. Rebuild container
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend
```

**Verification**: Frontend loads without errors, no SSR-related messages in console

**Prevention**:
- Always wrap browser-only code in `if (browser)` checks
- Consider if SSR is needed - authenticated SPAs often don't require it
- Document SSR vs SPA decision in ADR

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - Full analysis
- GitHub Issues #11, #12

---

### "XMLHttpRequest cannot load"

**Symptom**: Form submissions or API calls fail with network errors

**Error Message**:
```
XMLHttpRequest cannot load http://backend:8000/api/v1/submissions
```

**Cause**: `VITE_API_URL` is set to a Docker internal hostname (`http://backend:8000`). Docker service names only work INSIDE the Docker network. The browser runs on your HOST machine and cannot resolve Docker service names.

**Solution**:

```bash
# 1. Remove VITE_API_URL from docker-compose.dev.yml
# The frontend will use default: http://localhost:8000

# 2. Clear Vite cache
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit

# 3. Rebuild frontend
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend

# 4. Hard refresh browser
# Mac: Cmd+Shift+R
# Windows/Linux: Ctrl+Shift+F5
```

**Verification**:
```bash
# Check backend is accessible from host
curl http://localhost:8000/api/v1/health

# Should return: {"status":"healthy",...}
```

**Prevention**:
- NEVER set `VITE_API_URL` to Docker service names
- Use `http://localhost:PORT` for browser-to-backend communication
- Use service names only for container-to-container communication
- Document in docker-compose.yml with comments

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - Docker networking section
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - End-to-end testing

---

### Blank page after environment changes

**Symptom**: Frontend shows blank white page after changing environment variables, no errors in console

**Cause**: Vite bundles environment variables at BUILD time, not runtime. Changing docker-compose.yml environment variables doesn't affect already-built JavaScript bundles. Browser may also cache old bundles.

**Solution**:

```bash
# 1. Clear Vite cache inside container
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit

# 2. Rebuild frontend (this re-bundles with new env vars)
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend

# 3. Hard refresh browser to bypass cache
# Mac: Cmd+Shift+R
# Windows/Linux: Ctrl+Shift+F5
# Alternative: DevTools → Right-click refresh → "Empty Cache and Hard Reload"
```

**Verification**:
```bash
# Check what URL is actually in the bundle
curl http://localhost:5173/src/lib/api/client.ts

# Or check in browser console:
console.log(import.meta.env.VITE_API_URL)
```

**Prevention**:
- Document that VITE_* changes require rebuild
- Add npm script: `"clean": "rm -rf node_modules/.vite .svelte-kit"`
- Consider runtime config for environment-specific settings
- Use feature flags instead of build-time variables where possible

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - "Vite Build-Time vs Runtime" section

---

### Vite cache corruption

**Symptom**: Bizarre errors, stale code appearing in browser, or frontend behaving unexpectedly despite code changes

**Error Message**: Various, often confusing and unrelated to actual problem

**Cause**: Vite's cache (`.vite` directory) or SvelteKit's build cache (`.svelte-kit`) can become corrupted or stale, especially after major changes or environment variable updates.

**Solution**:

```bash
# Option 1: Clear cache in running container
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit

# Option 2: Clear cache locally (if developing without Docker)
cd frontend
rm -rf node_modules/.vite .svelte-kit

# Then restart/rebuild frontend
docker compose -f infrastructure/docker-compose.dev.yml restart frontend

# If that doesn't work, rebuild:
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend

# Finally, hard refresh browser
```

**Verification**: Check browser DevTools console for errors, verify latest code is running

**Prevention**:
- Add `clean` script to package.json: `"clean": "rm -rf node_modules/.vite .svelte-kit"`
- Run clean before major changes
- Clear cache after environment variable changes

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md)

---

### Hard refresh not working

**Symptom**: Browser refresh doesn't show latest changes, old code persists

**Cause**: Browser has aggressively cached JavaScript bundles

**Solution**:

```bash
# Try these in order:

# 1. Standard hard refresh
# Mac: Cmd+Shift+R
# Windows/Linux: Ctrl+Shift+F5

# 2. DevTools method (most reliable)
# Open DevTools (F12)
# Right-click the refresh button
# Select "Empty Cache and Hard Reload"

# 3. Clear browser cache manually
# Chrome: Settings → Privacy → Clear browsing data → Cached images and files

# 4. Open in incognito/private window (to verify cache issue)

# 5. If still not working, clear Vite cache and rebuild:
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend
```

**Verification**: Check DevTools Network tab, verify files are being fetched fresh (not from cache)

**Prevention**:
- Use DevTools with cache disabled during development (Settings → Network → Disable cache)
- Document hard refresh requirement for team members

---

## Docker Networking Issues

### Frontend can't reach backend

**Symptom**: Frontend shows network errors when trying to communicate with backend API

**Error Message**:
```
Network Error
Failed to fetch
ERR_CONNECTION_REFUSED
```

**Cause**: Incorrect API URL configuration - either using Docker internal hostname, or backend not running, or port mismatch.

**Solution**:

```bash
# 1. Verify backend is running and healthy
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy","service":"ans-backend","version":"0.1.0"}

# 2. Check backend is accessible from host
docker compose -f infrastructure/docker-compose.dev.yml ps
# Backend should show "Up" and "healthy"

# 3. Verify frontend is using correct URL
# Check frontend/src/lib/api/client.ts
# Should have: const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

# 4. Ensure VITE_API_URL is NOT set in docker-compose.dev.yml
# Remove any VITE_API_URL entries from frontend environment

# 5. Clear cache and rebuild
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend

# 6. Hard browser refresh
# Mac: Cmd+Shift+R
# Windows/Linux: Ctrl+Shift+F5
```

**Verification**:
- Backend health check works: `curl http://localhost:8000/api/v1/health`
- Browser console shows no CORS errors
- API calls succeed in browser DevTools Network tab

**Prevention**:
- Document Docker networking patterns clearly
- Add comments in docker-compose.yml about VITE_API_URL
- Use defaults in code, not docker-compose

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - "Docker Networking Misunderstanding"
- [README.md](../README.md) - Troubleshooting section

---

### VITE_API_URL confusion

**Symptom**: Confusion about what URL to use, or changes not taking effect

**Error Message**: N/A - Configuration issue

**Cause**: Misunderstanding how Vite environment variables work and Docker networking

**Solution**:

**Understanding the problem**:
- Docker service names (e.g., `backend`) only work INSIDE Docker network
- Browser runs on HOST machine, needs `localhost:PORT`
- Vite bakes `VITE_*` variables into bundle at BUILD time

**Correct configuration**:

```yaml
# infrastructure/docker-compose.dev.yml
frontend:
  environment:
    - NODE_ENV=development
    # VITE_API_URL intentionally omitted - uses default from code
```

```typescript
// frontend/src/lib/api/client.ts
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const apiClient = axios.create({ baseURL: API_URL });
```

**How to verify what's in the bundle**:
```bash
# Check console in browser
console.log(import.meta.env.VITE_API_URL)

# Or check the built file
docker exec ans-frontend grep -r "localhost:8000" /app/.svelte-kit/
```

**Verification**: API calls work from browser without errors

**Prevention**:
- Document build-time vs runtime behavior
- Use sensible defaults in code
- Avoid setting VITE_* in docker-compose unless absolutely necessary
- Remember: env var changes require rebuild + hard refresh

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - "Vite Build-Time vs Runtime"

---

### Browser vs container networking

**Symptom**: Confusion about when to use Docker service names vs localhost

**Explanation**:

Docker Compose creates an internal network where services can reach each other by name. However, the browser runs on your HOST machine, outside the Docker network.

**Rule of Thumb**:

| Source | Destination | Use |
|--------|-------------|-----|
| Browser | Backend | `http://localhost:8000` |
| Backend | PostgreSQL | `http://postgres:5432` |
| Backend | Redis | `redis://redis:6379` |
| Frontend Container | Backend | `http://backend:8000` (rarely needed) |

**Key Concept**:
- **Browser-to-Backend**: Browser runs on HOST, use `localhost:8000`
- **Backend-to-Database**: Both in Docker network, use service name `postgres:5432`
- **Backend-to-Redis**: Both in Docker network, use service name `redis:6379`

**Common Mistake**:
```yaml
# WRONG - Browser can't resolve 'backend'
frontend:
  environment:
    - VITE_API_URL=http://backend:8000

# CORRECT - Use localhost for browser
frontend:
  environment:
    # Omit VITE_API_URL, let code default to http://localhost:8000
```

**Verification**:
- `curl http://localhost:8000/api/v1/health` works from your terminal
- Frontend can successfully call API endpoints

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - "Docker Networking Misunderstanding"
- Docker Networking Docs: https://docs.docker.com/compose/networking/

---

## Common Docker Issues

### Port already in use

**Symptom**: Docker Compose fails to start with port conflict error

**Error Message**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use
Error starting userland proxy: listen tcp4 0.0.0.0:6379: bind: address already in use
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
Error starting userland proxy: listen tcp4 0.0.0.0:5173: bind: address already in use
```

**Cause**: Another process is already using the port, or containers from previous runs are still running

**Solution**:

```bash
# 1. Check what's using the ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# 2. Kill the process if needed
# Find PID from lsof output, then:
kill -9 <PID>

# 3. Or stop existing Docker containers
docker compose -f infrastructure/docker-compose.dev.yml down

# 4. Check for orphaned containers
docker ps -a | grep ans-

# 5. If containers are stuck, force remove
docker rm -f ans-postgres ans-redis ans-backend ans-frontend

# 6. Alternative: Change ports in docker-compose.dev.yml
# Example: Change "5432:5432" to "5433:5432" for PostgreSQL
```

**Verification**: `docker compose -f infrastructure/docker-compose.dev.yml ps` shows all services running

**Prevention**:
- Always use `make docker-down` or `docker compose down` when stopping
- Don't run duplicate dev environments simultaneously
- Document standard ports in README

---

### Services won't start

**Symptom**: Some or all Docker services fail to start, remain in "Restarting" state, or exit immediately

**Error Message**: Various, check logs

**Cause**: Multiple possible causes - dependency not ready, configuration error, port conflict, missing environment variables

**Solution**:

```bash
# 1. Check status of all services
docker compose -f infrastructure/docker-compose.dev.yml ps

# 2. View logs to identify the failing service
docker compose -f infrastructure/docker-compose.dev.yml logs

# 3. Check specific service logs
docker compose -f infrastructure/docker-compose.dev.yml logs backend
docker compose -f infrastructure/docker-compose.dev.yml logs postgres

# 4. Common fixes:

# If PostgreSQL fails:
# - Check port 5432 is available: lsof -i :5432
# - Check volume permissions: ls -la $(docker volume inspect ans-project_postgres_data -f '{{.Mountpoint}}')

# If backend fails:
# - Check DATABASE_URL is set correctly
# - Check dependencies are healthy: docker compose ps
# - Check migrations ran: docker compose exec backend alembic current

# If frontend fails:
# - Check node_modules exist: docker compose exec frontend ls -la /app/node_modules
# - Check for build errors: docker compose logs frontend

# 5. Check environment variables are set
docker compose -f infrastructure/docker-compose.dev.yml exec backend env | grep -E "(DATABASE|REDIS|DEBUG)"

# 6. Nuclear option - clean and rebuild
make clean
make docker-build
make docker-up
```

**Verification**:
```bash
# All services should show "Up" and "healthy"
docker compose -f infrastructure/docker-compose.dev.yml ps

# Health checks should pass
curl http://localhost:8000/api/v1/health
```

**Prevention**:
- Check Docker Desktop has sufficient resources (Settings → Resources)
- Ensure dependencies start before dependents (use depends_on with conditions)
- Add healthchecks to all services
- Document startup order and dependencies

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Service dependencies section

---

### Volume permission issues

**Symptom**: "Permission denied" errors when containers try to read/write files

**Error Message**:
```
PermissionError: [Errno 13] Permission denied: '/app/...'
Error: EACCES: permission denied
```

**Cause**: File ownership mismatch between host and container, common on Linux systems

**Solution**:

```bash
# On Linux systems:

# 1. Fix backend permissions
sudo chown -R $USER:$USER backend/

# 2. Fix frontend permissions
sudo chown -R $USER:$USER frontend/

# 3. Fix database volume (if needed)
# First, stop containers
docker compose -f infrastructure/docker-compose.dev.yml down
# Remove and recreate volume
docker volume rm ans-project_postgres_data
# Restart services
docker compose -f infrastructure/docker-compose.dev.yml up -d

# 4. For Docker volume permissions
# Check volume ownership
docker volume inspect ans-project_postgres_data

# 5. Alternative: Run container as current user
# Add to docker-compose.dev.yml:
# user: "${UID}:${GID}"
```

**Verification**: Services start without permission errors in logs

**Prevention**:
- Document permission requirements for Linux users
- Consider using named volumes instead of bind mounts where appropriate
- Set correct user/group in Dockerfile if needed

---

### Hot reload not working

**Symptom**: Code changes don't trigger automatic reload in backend or frontend

**Cause**: Volume mounts incorrect, or file watching not working

#### Backend Hot Reload

**Solution**:
```bash
# 1. Verify volume mounts are correct
docker inspect ans-backend | grep -A 20 Mounts
# Should show backend/app mounted to /app/app

# 2. Check Uvicorn is running with --reload flag
docker compose -f infrastructure/docker-compose.dev.yml logs backend | grep reload
# Should see: "Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)"

# 3. Test by making a change
# Add a comment to backend/app/main.py
# Check logs:
docker logs -f ans-backend
# Should see: "Detected changes in..." and reload message

# 4. If not working, restart container
docker compose -f infrastructure/docker-compose.dev.yml restart backend

# 5. Verify Dockerfile has --reload flag
grep -r "reload" backend/Dockerfile
```

#### Frontend Hot Reload

**Solution**:
```bash
# 1. Verify volume mounts
docker inspect ans-frontend | grep -A 20 Mounts
# Should show specific directories mounted, NOT entire /app

# 2. Check node_modules is NOT bind-mounted
# node_modules should be in container, not on host

# 3. Verify Vite is running in dev mode
docker compose -f infrastructure/docker-compose.dev.yml logs frontend
# Should see: "VITE v5.x.x ready in..."

# 4. Test by making a change
# Edit frontend/src/routes/+page.svelte
# Browser should update automatically via HMR

# 5. If not working, clear cache and rebuild
docker exec ans-frontend rm -rf /app/node_modules/.vite /app/.svelte-kit
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend

# 6. Check browser console for HMR errors
# Open DevTools, look for "[vite]" messages
```

**Verification**:
- Backend: Make a change, see reload message in logs
- Frontend: Make a change, see HMR update in browser console, page updates without refresh

**Prevention**:
- Mount specific directories, not entire /app
- Exclude node_modules from bind mounts
- Document hot reload requirements in README

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Hot reload testing sections

---

## Database Issues

### "database does not exist"

**Symptom**: Backend fails to start or connect to database

**Error Message**:
```
psycopg2.OperationalError: FATAL: database "ans_dev" does not exist
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: database "ans_dev" does not exist
```

**Cause**: Database hasn't been initialized, or initialization script didn't run

**Solution**:

```bash
# 1. Check if database exists
docker exec ans-postgres psql -U postgres -l

# 2. If ans_dev is missing, create it
docker exec ans-postgres psql -U postgres -c "CREATE DATABASE ans_dev;"

# 3. Enable pgvector extension
docker exec ans-postgres psql -U postgres -d ans_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. Run migrations
docker compose -f infrastructure/docker-compose.dev.yml exec backend alembic upgrade head

# 5. Verify database is ready
docker exec ans-postgres psql -U postgres -d ans_dev -c "\dt"
# Should show tables

# 6. If problem persists, reinitialize database:
docker compose -f infrastructure/docker-compose.dev.yml down -v
docker volume rm ans-project_postgres_data
docker compose -f infrastructure/docker-compose.dev.yml up -d postgres
# Wait for postgres to be healthy
docker compose -f infrastructure/docker-compose.dev.yml up -d
```

**Verification**:
```bash
# Database exists and is accessible
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT 1 as test;"
# Should return: 1

# Backend can connect
curl http://localhost:8000/api/v1/health
```

**Prevention**:
- Ensure init-db.sql is correctly configured
- Use health checks in docker-compose
- Document database setup in README

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Database connectivity section

---

### "pgvector extension not found"

**Symptom**: Database operations fail with vector-related errors

**Error Message**:
```
psycopg2.errors.UndefinedObject: type "vector" does not exist
ERROR: type "vector" does not exist
```

**Cause**: pgvector extension not installed or not enabled in the database

**Solution**:

```bash
# 1. Check if extension is installed
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# 2. If not installed, enable it
docker exec ans-postgres psql -U postgres -d ans_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3. Verify it works
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT '[1,2,3]'::vector;"
# Should return: [1,2,3]

# 4. If extension is not available at all, check PostgreSQL image
# Ensure you're using pgvector/pgvector:pg15 or similar
grep -A 5 "postgres:" infrastructure/docker-compose.dev.yml

# 5. If wrong image, update docker-compose.dev.yml and rebuild:
docker compose -f infrastructure/docker-compose.dev.yml down -v
docker compose -f infrastructure/docker-compose.dev.yml up -d --build postgres
```

**Verification**:
```bash
# Extension is installed
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
# Should show: vector | 0.8.1 (or higher)

# Can use vector operations
docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT '[1,2,3]'::vector <-> '[3,2,1]'::vector;"
```

**Prevention**:
- Use pgvector-enabled PostgreSQL image in docker-compose
- Document pgvector requirement
- Include extension creation in init-db.sql

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - pgvector testing
- pgvector GitHub: https://github.com/pgvector/pgvector

---

### Database connection refused

**Symptom**: Backend can't connect to PostgreSQL

**Error Message**:
```
psycopg2.OperationalError: could not connect to server: Connection refused
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection refused
```

**Cause**: PostgreSQL not running, not healthy, or credentials incorrect

**Solution**:

```bash
# 1. Check if PostgreSQL is running
docker compose -f infrastructure/docker-compose.dev.yml ps postgres
# Should show "Up" and "healthy"

# 2. Check port is accessible
lsof -i :5432
# Should show docker-proxy

# 3. Test connection manually
docker exec ans-postgres pg_isready -U postgres
# Should return: "accepting connections"

# 4. Test with psql
docker exec ans-postgres psql -U postgres -c "SELECT 1;"
# Should return: 1

# 5. Check DATABASE_URL is correct
docker compose -f infrastructure/docker-compose.dev.yml exec backend env | grep DATABASE_URL
# Should be: postgresql://postgres:postgres@postgres:5432/ans_dev

# 6. Check credentials match
# In .env or docker-compose.dev.yml:
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres

# 7. If still failing, restart PostgreSQL
docker compose -f infrastructure/docker-compose.dev.yml restart postgres

# 8. Check logs for errors
docker compose -f infrastructure/docker-compose.dev.yml logs postgres
```

**Verification**:
```bash
# Can connect from backend container
docker compose -f infrastructure/docker-compose.dev.yml exec backend python -c "
from app.core.database import engine
with engine.connect() as conn:
    print('Connected successfully')
"
```

**Prevention**:
- Use health checks in docker-compose
- Ensure backend depends_on postgres with condition: service_healthy
- Document connection string format

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Database connectivity

---

## Backend Issues

### ModuleNotFoundError (Backend)

**Symptom**: Backend fails to start or import errors occur

**Error Message**:
```
ModuleNotFoundError: No module named 'app'
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'X' from 'app.Y'
```

**Cause**: Python dependencies not installed, or PYTHONPATH not set correctly

**Solution**:

```bash
# 1. Check if dependencies are installed
docker compose -f infrastructure/docker-compose.dev.yml exec backend pip list

# 2. Reinstall dependencies in container
docker compose -f infrastructure/docker-compose.dev.yml exec backend pip install -e ".[dev]"

# 3. If that fails, rebuild container
docker compose -f infrastructure/docker-compose.dev.yml up -d --build backend

# 4. Check PYTHONPATH is set
docker compose -f infrastructure/docker-compose.dev.yml exec backend env | grep PYTHON
# Should show PYTHONPATH includes /app

# 5. Verify working directory
docker compose -f infrastructure/docker-compose.dev.yml exec backend pwd
# Should be /app

# 6. Check imports work
docker compose -f infrastructure/docker-compose.dev.yml exec backend python -c "from app.main import app; print('OK')"
```

**Verification**: Backend starts without import errors, API is accessible

**Prevention**:
- Document dependency installation in README
- Use requirements.txt for reproducible builds
- Set PYTHONPATH in Dockerfile

---

### Uvicorn not reloading

**Symptom**: Backend code changes don't trigger automatic reload

**Cause**: Volume mounts incorrect, --reload flag missing, or file watching not working

**Solution**:

```bash
# 1. Check if --reload flag is set
docker compose -f infrastructure/docker-compose.dev.yml logs backend | grep reload
# Should see Uvicorn with --reload

# 2. Verify volume mounts
docker inspect ans-backend | grep -A 20 Mounts
# backend/app should be mounted to /app/app

# 3. Test by making a change
# Add a comment to backend/app/main.py
# Watch logs:
docker logs -f ans-backend
# Should see "Detected changes in..." message

# 4. Check Dockerfile CMD
grep CMD backend/Dockerfile
# Should include: --reload

# 5. Restart backend
docker compose -f infrastructure/docker-compose.dev.yml restart backend

# 6. If still not working, check file system events
# On macOS, ensure Docker Desktop has proper file sharing permissions
# Docker Desktop → Settings → Resources → File Sharing
```

**Verification**: Make a change to Python file, see reload message in logs within 2-3 seconds

**Prevention**:
- Document hot reload in README
- Ensure volume mounts in docker-compose include backend/app
- Use --reload flag in development Dockerfile

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Backend hot reload section

---

### Tests failing (import errors)

**Symptom**: pytest fails with import errors when running tests

**Error Message**:
```
ImportError: cannot import name 'X' from 'app.Y'
ModuleNotFoundError: No module named 'app'
```

**Cause**: PYTHONPATH not set correctly when running tests, or wrong working directory

**Solution**:

```bash
# 1. Run tests from correct directory
docker compose -f infrastructure/docker-compose.dev.yml exec backend bash
cd /app
pytest -v

# 2. Or set PYTHONPATH explicitly
docker compose -f infrastructure/docker-compose.dev.yml exec backend bash -c "PYTHONPATH=/app pytest -v"

# 3. Check conftest.py exists
docker compose -f infrastructure/docker-compose.dev.yml exec backend ls -la /app/app/tests/conftest.py

# 4. Verify test files are named correctly
# Should be: test_*.py or *_test.py
docker compose -f infrastructure/docker-compose.dev.yml exec backend ls /app/app/tests/

# 5. Check pytest.ini or pyproject.toml configuration
docker compose -f infrastructure/docker-compose.dev.yml exec backend cat /app/pyproject.toml | grep -A 10 "\[tool.pytest"

# 6. Use Makefile command (handles paths correctly)
make test-backend
```

**Verification**: All tests run successfully without import errors

**Prevention**:
- Document test running in README
- Set PYTHONPATH in pyproject.toml or pytest.ini
- Use Makefile commands that handle paths correctly

---

## Frontend Issues

### "Cannot find module" (Frontend)

**Symptom**: Frontend fails to start or import errors occur

**Error Message**:
```
Error: Cannot find module 'svelte'
Error: Cannot find module '@/lib/components/...'
```

**Cause**: npm dependencies not installed in container

**Solution**:

```bash
# 1. Check if node_modules exists
docker compose -f infrastructure/docker-compose.dev.yml exec frontend ls -la /app/node_modules

# 2. Install dependencies
docker compose -f infrastructure/docker-compose.dev.yml exec frontend npm install

# 3. If that fails, rebuild container
docker compose -f infrastructure/docker-compose.dev.yml up -d --build frontend

# 4. Check package.json exists
docker compose -f infrastructure/docker-compose.dev.yml exec frontend cat /app/package.json

# 5. Verify npm version
docker compose -f infrastructure/docker-compose.dev.yml exec frontend npm --version
# Should be 9.x or higher

# 6. Clear npm cache if needed
docker compose -f infrastructure/docker-compose.dev.yml exec frontend npm cache clean --force
docker compose -f infrastructure/docker-compose.dev.yml exec frontend npm install
```

**Verification**: Frontend starts successfully, no module errors in logs

**Prevention**:
- Ensure Dockerfile includes `npm install` step
- Don't bind mount node_modules directory
- Document dependency installation in README

---

### npm dependencies not installed

**Symptom**: Frontend container exits immediately or fails to start Vite dev server

**Cause**: Dependencies weren't installed during image build, or node_modules was overwritten by volume mount

**Solution**:

```bash
# 1. Check if issue is volume mount
docker compose -f infrastructure/docker-compose.dev.yml exec frontend ls -la /app/node_modules

# 2. Rebuild with no cache
docker compose -f infrastructure/docker-compose.dev.yml build --no-cache frontend

# 3. Ensure volume mounts don't overwrite node_modules
# Check docker-compose.dev.yml:
# Volumes should mount specific directories, NOT /app
# - ../frontend/src:/app/src  ✓ Good
# - ../frontend:/app  ✗ Bad (overwrites node_modules)

# 4. If volumes are correct, install dependencies
docker compose -f infrastructure/docker-compose.dev.yml exec frontend npm install

# 5. Restart frontend
docker compose -f infrastructure/docker-compose.dev.yml restart frontend
```

**Verification**:
```bash
# node_modules exists and has packages
docker compose -f infrastructure/docker-compose.dev.yml exec frontend ls /app/node_modules | wc -l
# Should show hundreds of packages

# Frontend is running
curl http://localhost:5173
# Should return HTML
```

**Prevention**:
- Mount specific directories only
- Never mount entire /app directory
- Document volume mount strategy

**Related**:
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - Volume mount configuration

---

## Test Issues

### Coverage below 80%

**Symptom**: Test suite runs but coverage report shows less than 80%

**Error Message**:
```
FAILED - Required test coverage of 80% not reached. Total coverage: 65.00%
```

**Cause**: Insufficient tests, or uncovered code paths

**Solution**:

```bash
# 1. Run coverage report to see what's missing
docker compose -f infrastructure/docker-compose.dev.yml exec backend pytest --cov=app --cov-report=term-missing

# Output shows which lines are not covered:
# app/main.py                  45      10      78%   12-15, 23-26

# 2. Write tests for uncovered lines
# Focus on:
# - Error handling paths
# - Edge cases
# - Utility functions

# 3. Check if test files follow naming convention
# Should be: test_*.py or *_test.py
docker compose -f infrastructure/docker-compose.dev.yml exec backend find /app/app/tests -name "*.py"

# 4. Ensure all modules have corresponding test files
# Example: app/services/fact_checker.py → app/tests/test_fact_checker.py

# 5. Run specific test to increase coverage
docker compose -f infrastructure/docker-compose.dev.yml exec backend pytest app/tests/test_X.py --cov=app.services.X

# 6. If needed, adjust coverage threshold temporarily
# Edit pyproject.toml:
# [tool.pytest.ini_options]
# fail_under = 70  # Temporarily lower, but aim for 80%
```

**Verification**: `pytest --cov=app` shows ≥ 80% coverage

**Prevention**:
- Follow TDD: write tests before implementation
- Review coverage report regularly
- Make coverage part of CI/CD checks

---

### Path issues in tests

**Symptom**: Tests fail because they expect different API paths than implemented

**Error Message**:
```
AssertionError: assert 404 == 200
E       Failed: 404 response when expecting 200
```

**Cause**: Tests use incorrect endpoint path (e.g., `/health` instead of `/api/v1/health`)

**Solution**:

```bash
# 1. Identify the failing test
docker compose -f infrastructure/docker-compose.dev.yml exec backend pytest -v

# 2. Check what path the test is using
# Example: app/tests/test_health.py
docker compose -f infrastructure/docker-compose.dev.yml exec backend cat /app/app/tests/test_health.py

# 3. Check what the actual endpoint path is
docker compose -f infrastructure/docker-compose.dev.yml exec backend cat /app/app/api/v1/endpoints/health.py

# Or test with curl:
curl -I http://localhost:8000/health  # 404
curl -I http://localhost:8000/api/v1/health  # 200

# 4. Update test to use correct path
# Change:
# response = client.get("/health")
# To:
# response = client.get("/api/v1/health")

# 5. Or update implementation if path should change
# Update router to use simpler path if that's desired

# 6. Verify with curl after fix
curl http://localhost:8000/api/v1/health
```

**Verification**: All tests pass, no 404 errors

**Prevention**:
- Document API path structure in README or API docs
- Use constants for paths:
  ```python
  API_V1_PREFIX = "/api/v1"
  HEALTH_PATH = f"{API_V1_PREFIX}/health"
  ```
- Include path in test names: `test_health_endpoint_returns_200()`

**Related**:
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Known issues section
- GitHub Issue #18 - Health endpoint test failures

---

## Clean Slate

### Start from scratch

**When to use**: When all else fails, or you have multiple compounding issues

**WARNING**: This will delete all data in your local development environment

```bash
# 1. Stop all containers
docker compose -f infrastructure/docker-compose.dev.yml down

# 2. Remove all volumes (WARNING: deletes database data)
docker compose -f infrastructure/docker-compose.dev.yml down -v

# 3. Remove all project containers
docker ps -a | grep ans- | awk '{print $1}' | xargs docker rm -f

# 4. Remove all project volumes
docker volume ls | grep ans-project | awk '{print $2}' | xargs docker volume rm

# 5. Remove all project images
docker images | grep ans- | awk '{print $3}' | xargs docker rmi -f

# 6. (Optional) Prune entire Docker system
# WARNING: This affects ALL Docker resources, not just this project
docker system prune -a --volumes

# 7. Clear local caches
cd frontend
rm -rf node_modules/.vite .svelte-kit node_modules
cd ..

# 8. Rebuild from scratch
make setup
# Edit .env with your API keys

make docker-build
make docker-up

# 9. Verify everything works
make status
curl http://localhost:8000/api/v1/health
curl http://localhost:5173

# 10. Run migrations
make db-migrate

# 11. Run tests
make test
```

**Verification**:
- All services show "Up" and "healthy": `docker compose ps`
- Backend health check works: `curl http://localhost:8000/api/v1/health`
- Frontend loads: Open http://localhost:5173 in browser
- Tests pass: `make test`

**When to use this**:
- Multiple conflicting errors
- Suspected Docker state corruption
- After major configuration changes
- When onboarding new developers (clean slate)

---

## Additional Resources

### Documentation
- [README.md](../README.md) - Project setup and development guide
- [POST_MORTEM_SSR_MIGRATION.md](POST_MORTEM_SSR_MIGRATION.md) - Detailed lessons learned from Sprint 1
- [INFRASTRUCTURE_TESTING.md](INFRASTRUCTURE_TESTING.md) - Complete testing checklist
- [AGENT_COORDINATION.md](AGENT_COORDINATION.md) - Development workflow

### GitHub Issues (Historical)
- Issue #11 - SSR location error (CLOSED)
- Issue #12 - Docker networking error (CLOSED)
- Issue #18 - Health endpoint path mismatch

### External Resources
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [SvelteKit SSR Documentation](https://kit.svelte.dev/docs/page-options#ssr)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)

### Getting Help

If this guide doesn't solve your problem:

1. **Search Documentation**: Check all docs in `docs/` directory
2. **Check Logs**: `make docker-logs` often reveals the root cause
3. **Search Issues**: Check GitHub issues for similar problems
4. **Create Issue**: Open a new GitHub issue with:
   - Clear description of the problem
   - Error messages (full text)
   - Steps to reproduce
   - System info (`docker --version`, OS, etc.)
   - What you've already tried

### Maintenance

This troubleshooting guide should be updated when:
- New issues are discovered
- Solutions change due to architecture updates
- New common problems emerge
- External dependencies change

**Last Updated**: 2025-12-15
**Next Review**: After each sprint or major release

---

**Remember**: Most issues can be resolved in < 10 minutes with this guide. When in doubt, try the Clean Slate approach and rebuild from scratch.
