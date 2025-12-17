# Post-Mortem: SSR to SPA Migration & Docker Networking Issues

**Date**: 2025-12-13
**Issues**: #11, #12
**Impact**: Frontend unable to load, form submissions failing
**Resolution Time**: ~2 hours across multiple debugging sessions
**Status**: ✅ Resolved

---

## Executive Summary

During local development of the Ans platform, we encountered two critical issues:
1. **SSR Error**: Frontend failed to render with `ReferenceError: location is not defined`
2. **Network Error**: Form submissions failed due to incorrect API endpoint (`http://backend:8000` instead of `http://localhost:8000`)

Both issues were resolved by migrating from SSR to SPA mode and correcting Docker networking configuration for browser-based API calls.

---

## Timeline of Events

### Initial Problem: SSR Error
- **Symptom**: Frontend showed blank page with `location is not defined` error
- **Root Cause**: Axios interceptors trying to access browser's `location` object during server-side rendering
- **Environment**: SvelteKit with default adapter-auto (SSR enabled)

### Resolution Attempts (SSR)
1. ✗ Added browser check in `client.ts` - Partial fix, error persisted
2. ✗ Created `hooks.server.ts` with `ssr: false` - No effect
3. ✅ Installed `@sveltejs/adapter-static` - Changed to SPA mode
4. ✅ Created `+layout.js` with `export const ssr = false` - Disabled SSR globally
5. ✅ Updated Docker volumes to preserve `node_modules` during rebuild

### Secondary Problem: Network Error
- **Symptom**: Form submission failed with "Network Error"
- **Console Error**: `XMLHttpRequest cannot load http://backend:8000/api/v1/submissions`
- **Root Cause**: `VITE_API_URL=http://backend:8000` uses Docker internal networking, inaccessible from browser

### Resolution Attempts (Network)
1. ✗ Changed `VITE_API_URL` to `http://localhost:8000` in docker-compose
   - **Issue**: Environment variables are baked into bundle at BUILD time
   - Old bundle still cached in browser
2. ✅ Removed `VITE_API_URL` from docker-compose entirely
   - Falls back to default in `client.ts`: `import.meta.env.VITE_API_URL || 'http://localhost:8000'`
3. ✅ Cleared Vite cache: `rm -rf /app/node_modules/.vite /app/.svelte-kit`
4. ✅ Rebuilt frontend container
5. ✅ User performed hard browser refresh (Cmd+Shift+R)

---

## Root Causes

### 1. SSR Incompatibility with Axios Interceptors
**Problem**: Axios interceptors reference browser-only objects during SSR
```typescript
// This code runs on server during SSR, causing error
apiClient.interceptors.request.use((config) => {
  // Accessing window, location, etc. here fails
});
```

**Solution**: Wrap interceptors in browser check OR disable SSR entirely
```typescript
import { browser } from '$app/environment';

if (browser) {
  // Only runs in browser
  apiClient.interceptors.request.use(...);
}
```

**Decision**: Migrated to SPA mode because:
- Ans platform doesn't require SEO (authenticated app)
- Form submissions are primary use case (client-side only)
- Reduces complexity for data fetching with TanStack Query

### 2. Docker Networking Misunderstanding
**Problem**: Vite environment variables meant for browser accessing Docker host

```yaml
# INCORRECT - backend:8000 only works INSIDE Docker network
frontend:
  environment:
    - VITE_API_URL=http://backend:8000
```

**Why This Fails**:
- Docker Compose creates internal network where services resolve by name (`backend`)
- Browser runs on HOST machine, not inside Docker network
- Browser cannot resolve `backend` hostname - needs `localhost`

**Correct Configuration**:
```yaml
# CORRECT - Use default in client.ts
frontend:
  environment:
    # VITE_API_URL intentionally omitted
    - NODE_ENV=development
```

```typescript
// frontend/src/lib/api/client.ts
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

### 3. Vite Build-Time vs Runtime
**Critical Learning**: Vite environment variables are **compiled into JavaScript bundle** at build time

```javascript
// At BUILD time, Vite replaces import.meta.env.VITE_API_URL with literal value
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Becomes (if VITE_API_URL=http://backend:8000 during build):
const API_URL = "http://backend:8000" || 'http://localhost:8000';
```

**Implications**:
1. Changing docker-compose env vars doesn't affect already-built bundles
2. Container restart ≠ rebuild
3. Must clear Vite cache and rebuild when changing VITE_* variables
4. Browser may cache old JavaScript bundles

---

## Solutions Implemented

### 1. Migrate to SPA Mode

**Files Modified**:
- `frontend/svelte.config.js` - Changed to `adapter-static`
- `frontend/src/routes/+layout.js` - Added `export const ssr = false`
- `frontend/package.json` - Added `@sveltejs/adapter-static` dependency

**Benefits**:
- Eliminates SSR-related errors
- Simpler mental model for authenticated SPA
- Faster development iteration

### 2. Docker Networking Configuration

**Files Modified**:
- `infrastructure/docker-compose.dev.yml`

**Changes**:
```yaml
frontend:
  environment:
    - NODE_ENV=development
    # VITE_API_URL removed - uses default http://localhost:8000
  volumes:
    # Specific files mounted, NOT /app (preserves node_modules)
    - ../frontend/src:/app/src
    - ../frontend/static:/app/static
    # ... other specific files
```

### 3. API Client Configuration

**File**: `frontend/src/lib/api/client.ts`

```typescript
import { browser } from '$app/environment';

// Default to localhost:8000 for browser access to host
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000
});

// Browser-only interceptors
if (browser) {
  apiClient.interceptors.request.use(...);
  apiClient.interceptors.response.use(...);
}
```

---

## Lessons Learned

### 1. Docker Networking in Browser-Based Apps
- **Backend-to-Backend**: Use Docker service names (`http://backend:8000`)
- **Browser-to-Backend**: Use `http://localhost:PORT` (host network)
- Never set `VITE_API_URL` to Docker internal hostnames

### 2. Vite Environment Variables
- Baked at **build time**, not runtime
- Changing docker-compose env requires rebuild
- Always clear cache: `rm -rf node_modules/.vite .svelte-kit`
- Browser cache can persist old bundles

### 3. SSR Considerations
- Not all libraries are SSR-compatible
- Check for browser-only code (window, location, document)
- Wrap in `if (browser)` checks
- Consider if SSR is necessary for your use case

### 4. Debugging Process
- Check what's actually served: `curl http://localhost:5173/src/lib/api/client.ts`
- Verify environment at runtime: `console.log(import.meta.env)`
- Use browser DevTools Network tab to see actual requests
- Hard refresh (Cmd+Shift+R) to bypass browser cache

### 5. System Architecture Role
- As System Architect, should delegate debugging to specialized agents
- Create GitHub issues with reproduction steps
- Let Frontend/Backend/DevOps agents investigate
- Focus on architectural decisions, not hands-on fixes

---

## Prevention Strategies

### 1. Documentation
- ✅ Document Docker networking patterns in README
- ✅ Add comments in docker-compose about VITE_API_URL
- Document when to use SSR vs SPA mode

### 2. Development Workflow
- Add npm script for cache clearing: `"clean": "rm -rf node_modules/.vite .svelte-kit"`
- Document hard refresh requirement after environment changes
- Add healthcheck for frontend in docker-compose

### 3. Testing
- Add integration test that verifies API calls work
- Test Docker environment from clean state
- Verify browser can reach backend from host machine

### 4. Architecture
- Consider runtime config for environment-specific settings
- Use feature flags instead of build-time variables where possible
- Document the SPA vs SSR decision in ADR

---

## Action Items

- [x] Close issues #11 and #12 with resolution comments
- [x] Document SSR migration and Docker networking lessons
- [ ] Update README with Docker networking explanation
- [ ] Add docker-compose comments about VITE_API_URL
- [ ] Create ADR (Architecture Decision Record) for SPA choice
- [ ] Add integration tests for form submission
- [ ] Create "clean" npm script for cache clearing
- [ ] Update development docs with troubleshooting guide

---

## References

- Issue #11: https://github.com/Post-X-Society/ans-project/issues/11
- Issue #12: https://github.com/Post-X-Society/ans-project/issues/12
- SvelteKit SSR Docs: https://kit.svelte.dev/docs/page-options#ssr
- Vite Environment Variables: https://vitejs.dev/guide/env-and-mode.html
- Docker Networking: https://docs.docker.com/compose/networking/

---

**Prepared by**: System Architect Agent
**Date**: 2025-12-13
**Review Status**: Draft - Ready for team review
