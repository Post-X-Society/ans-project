# Local Development & Testing Guide
## Ans Fact-Checking Platform

**Last Updated**: 2025-12-17
**Version**: Phase 3 Complete

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop installed and running
- Git installed
- Terminal/Command line access

### Step 1: Clone & Setup

```bash
# Navigate to project directory
cd "/Users/pieter/Nextcloud-Hetzner/PXS Cloud/Projects/25010 Ans Snap Ams/03 Documents/Ans app/ans-project"

# Copy environment template
make setup

# Edit .env file and add your API keys
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# Backend Security (generate a secure key)
SECRET_KEY=$(openssl rand -hex 32)

# OpenAI (optional for Phase 3, mocked for now)
OPENAI_API_KEY=sk-your-key-here  # Optional, claim extraction is mocked

# Leave these as defaults
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ans_dev
```

### Step 2: Build & Start

```bash
# Build Docker containers (first time only)
make docker-build

# Start all services
make docker-up
```

**Expected Output:**
```
✓ Services started
  - Backend API: http://localhost:8000
  - Frontend: http://localhost:5173
  - API Docs: http://localhost:8000/docs
  - PostgreSQL: localhost:5432
  - Redis: localhost:6379
```

### Step 3: Run Migrations

```bash
# Apply database migrations
make db-migrate
```

### Step 4: Verify Everything Works

```bash
# Check service status
docker ps

# Test backend health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","service":"ans-backend","version":"0.1.0"}
```

---

## 📍 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Docs (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API docs |
| **Frontend** | http://localhost:5173 | Svelte application |
| **PostgreSQL** | localhost:5432 | Database (user: postgres, pass: postgres) |
| **Redis** | localhost:6379 | Cache and job queue |

---

## 🧪 Manual Testing Guide

### Test 1: Health Check (No Auth Required)

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "service": "ans-backend",
  "version": "0.1.0"
}
```

---

### Test 2: User Registration

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'

# Expected response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the access_token** - you'll need it for authenticated requests!

---

### Test 3: User Login

```bash
# Login with existing user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'

# Expected response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Test 4: Get Current User Info

```bash
# Set your token (replace with actual token from registration/login)
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get current user info
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Expected response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "role": "submitter",
  "is_active": true,
  "created_at": "2025-12-17T10:00:00Z",
  "updated_at": "2025-12-17T10:00:00Z"
}
```

---

### Test 5: Submit Content with Claim Extraction (Phase 3!)

```bash
# Submit content for fact-checking (requires authentication)
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Climate change is real and vaccines are safe. The earth is round.",
    "type": "text"
  }'

# Expected response (201 Created):
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Climate change is real and vaccines are safe. The earth is round.",
  "submission_type": "text",
  "status": "processing",
  "created_at": "2025-12-17T10:05:00Z",
  "updated_at": "2025-12-17T10:05:01Z",
  "extracted_claims_count": 3,
  "claims": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "content": "Climate change is real",
      "source": "submission:660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2025-12-17T10:05:01Z"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "content": "vaccines are safe",
      "source": "submission:660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2025-12-17T10:05:01Z"
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "content": "The earth is round",
      "source": "submission:660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2025-12-17T10:05:01Z"
    }
  ]
}
```

**Note**: Claim extraction is currently **mocked** (simple sentence splitter). Phase 4 will integrate real OpenAI GPT-4.

---

### Test 6: Get Submission with Claims

```bash
# Get a specific submission (requires authentication)
# Replace {submission_id} with actual ID from previous response
curl http://localhost:8000/api/v1/submissions/660e8400-e29b-41d4-a716-446655440001 \
  -H "Authorization: Bearer $TOKEN"

# Expected response (200 OK):
# Same as Test 5 response
```

---

### Test 7: List All Submissions

```bash
# List submissions with pagination
curl "http://localhost:8000/api/v1/submissions?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Expected response (200 OK):
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "Climate change is real...",
      "submission_type": "text",
      "status": "processing",
      "created_at": "2025-12-17T10:05:00Z",
      "updated_at": "2025-12-17T10:05:01Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

### Test 8: Authorization Tests (Negative Cases)

#### A. Submit Without Authentication (Should Fail)
```bash
# Try to submit without token
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This should fail",
    "type": "text"
  }'

# Expected response (401 Unauthorized):
{
  "detail": "Not authenticated"
}
```

#### B. Access Another User's Submission (Should Fail)
```bash
# Register second user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user2@example.com",
    "password": "password123"
  }'

# Save TOKEN2 from response

# Try to access first user's submission with second user's token
curl http://localhost:8000/api/v1/submissions/660e8400-e29b-41d4-a716-446655440001 \
  -H "Authorization: Bearer $TOKEN2"

# Expected response (403 Forbidden):
{
  "detail": "Forbidden"
}
```

---

### Test 9: Admin Operations (Create Admin First)

```bash
# First, create a super admin user manually in database
docker exec -it ans-postgres psql -U postgres -d ans_dev -c \
  "UPDATE users SET role='super_admin' WHERE email='test@example.com';"

# Login again to get new token with admin permissions
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'

# Save new TOKEN with admin role

# List all users (admin only)
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN"

# Expected response (200 OK):
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "role": "super_admin",
    "is_active": true,
    "created_at": "2025-12-17T10:00:00Z",
    "updated_at": "2025-12-17T10:00:00Z"
  },
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440000",
    "email": "user2@example.com",
    "role": "submitter",
    "is_active": true,
    "created_at": "2025-12-17T10:10:00Z",
    "updated_at": "2025-12-17T10:10:00Z"
  }
]
```

---

## 🔍 Using Swagger UI (Interactive Testing)

The **easiest way to test** is using the interactive API documentation:

1. Open browser: http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Register/login via `/api/v1/auth/register` or `/api/v1/auth/login`
4. Copy the `access_token` from response
5. Click "Authorize" button again
6. Enter: `Bearer your-token-here`
7. Click "Authorize" and "Close"
8. Now all endpoints will include your token automatically!

**Try these endpoints in order:**
1. `POST /api/v1/auth/register` - Create account
2. `GET /api/v1/users/me` - Get your info
3. `POST /api/v1/submissions` - Submit content
4. `GET /api/v1/submissions/{id}` - View submission with claims
5. `GET /api/v1/submissions` - List all submissions

---

## 📊 Monitoring & Logs

### View Logs
```bash
# All services
make docker-logs

# Backend only
make docker-logs-backend

# Frontend only
make docker-logs-frontend

# Follow logs in real-time
docker compose -f infrastructure/docker-compose.dev.yml logs -f backend
```

### Check Service Status
```bash
# List running containers
docker ps

# Check backend health
curl http://localhost:8000/api/v1/health

# Check database connection
docker exec -it ans-postgres psql -U postgres -d ans_dev -c "SELECT 1;"
```

### Database Inspection
```bash
# Open PostgreSQL shell
make db-shell

# Inside psql, run queries:
\dt                              # List tables
SELECT * FROM users;             # View users
SELECT * FROM submissions;       # View submissions
SELECT * FROM claims;            # View claims
SELECT * FROM submission_claims; # View links
\q                              # Exit
```

### Redis Inspection
```bash
# Open Redis CLI
make redis-shell

# Inside redis-cli:
PING                    # Test connection
KEYS *                  # List all keys
GET some_key           # Get value
MONITOR                # Watch all commands
quit                   # Exit
```

---

## 🧹 Maintenance Commands

### Restart Services
```bash
# Restart all services
make docker-down
make docker-up

# Restart specific service
docker compose -f infrastructure/docker-compose.dev.yml restart backend
```

### Reset Database
```bash
# Stop services and remove volumes (⚠️ deletes all data)
make clean

# Rebuild and restart
make docker-build
make docker-up
make db-migrate
```

### Run Tests
```bash
# All tests
docker exec -it ans-backend pytest app/tests/ -v

# With coverage
docker exec -it ans-backend pytest app/tests/ --cov=app --cov-report=term-missing

# Specific test file
docker exec -it ans-backend pytest app/tests/test_auth.py -v
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find what's using the port
lsof -i :8000   # Backend
lsof -i :5173   # Frontend
lsof -i :5432   # PostgreSQL

# Kill the process or change port in docker-compose.dev.yml
```

### Database Connection Error
```bash
# Restart PostgreSQL
docker compose -f infrastructure/docker-compose.dev.yml restart postgres

# Check logs
docker logs ans-postgres

# Verify database exists
docker exec -it ans-postgres psql -U postgres -l
```

### "Not authenticated" Error
```bash
# Verify token is valid
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v

# If token expired, login again to get new token
```

### Services Won't Start
```bash
# Check Docker is running
docker info

# Clean and rebuild
make clean
make docker-build
make docker-up
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Project README**: [../README.md](../README.md)
- **Phase 3 Design**: [PHASE_3_DESIGN.md](PHASE_3_DESIGN.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 🎯 Quick Test Checklist

Use this checklist to verify everything works:

- [ ] Services start successfully (`make docker-up`)
- [ ] Health endpoint responds (`curl http://localhost:8000/api/v1/health`)
- [ ] User registration works
- [ ] User login returns JWT token
- [ ] Can get current user info with token
- [ ] Can submit content (authenticated)
- [ ] Submission extracts claims automatically
- [ ] Can view submission with claims
- [ ] Cannot submit without authentication (401)
- [ ] Cannot view other users' submissions (403)
- [ ] Swagger UI works at http://localhost:8000/docs

---

**Happy Testing! 🚀**

If you encounter issues, check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or the logs using `make docker-logs`.
