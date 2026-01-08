# API Documentation

**Ans Fact-Checking Platform API v1**

Base URL: `http://localhost:8000/api/v1` (development)

## Table of Contents

- [Authentication](#authentication)
- [Interactive Documentation](#interactive-documentation)
- [Common Patterns](#common-patterns)
- [Endpoints Overview](#endpoints-overview)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Authentication

The Ans API uses JWT (JSON Web Token) bearer authentication for protected endpoints.

### Obtaining a Token

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "role": "submitter"
  }
}
```

### Using the Token

Include the access token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Token Refresh

Access tokens expire after 15 minutes. Use the refresh token to get a new one:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

## Interactive Documentation

The API provides two interactive documentation interfaces:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Try out API calls directly
  - See request/response schemas
  - Automatic authentication handling

- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
  - Clean, readable documentation
  - Print-friendly format
  - Search functionality

## Common Patterns

### Pagination

List endpoints support pagination using `page` and `page_size` parameters:

```bash
GET /api/v1/submissions?page=1&page_size=20
```

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Filtering

Use query parameters to filter results:

```bash
# Filter by status
GET /api/v1/submissions?status=pending

# Filter by date range
GET /api/v1/submissions?created_after=2024-01-01

# Multiple filters
GET /api/v1/submissions?status=pending&assigned_to_me=true
```

### Sorting

```bash
GET /api/v1/submissions?sort_by=created_at&sort_order=desc
```

### Error Responses

All error responses follow this structure:

```json
{
  "detail": "Detailed error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-08T14:30:00Z"
}
```

## Endpoints Overview

### Authentication & Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login and get tokens |
| POST | `/auth/refresh` | No | Refresh access token |
| GET | `/auth/me` | Yes | Get current user |
| PUT | `/auth/me` | Yes | Update current user |

### Submissions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/submissions` | Yes | Create submission |
| GET | `/submissions` | Yes | List submissions (role-based) |
| GET | `/submissions/{id}` | Yes | Get submission details |
| PUT | `/submissions/{id}` | Yes | Update submission |
| DELETE | `/submissions/{id}` | Yes (Admin) | Delete submission |
| POST | `/submissions/{id}/reviewers/me` | Yes (Reviewer+) | Self-assign as reviewer |
| POST | `/submissions/{id}/reviewers/{reviewer_id}` | Yes (Admin) | Assign reviewer |
| DELETE | `/submissions/{id}/reviewers/{reviewer_id}` | Yes (Admin) | Remove reviewer |

### Ratings

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/ratings/definitions` | No | List rating definitions |
| POST | `/fact-checks/{id}/rating` | Yes (Reviewer+) | Assign rating |
| GET | `/fact-checks/{id}/ratings` | Yes | Get rating history |
| GET | `/fact-checks/{id}/rating/current` | Yes | Get current rating |

### Workflow

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/workflow/{submission_id}/transition` | Yes (Reviewer+) | Trigger state change |
| GET | `/workflow/{submission_id}/history` | Yes | Get workflow history |
| GET | `/workflow/{submission_id}/current` | Yes | Get current state |
| GET | `/workflow/{submission_id}/available-transitions` | Yes | Get available transitions |

### Sources

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/sources` | Yes (Reviewer+) | Add source to fact-check |
| GET | `/sources/{fact_check_id}` | Yes | List sources for fact-check |
| PUT | `/sources/{id}` | Yes (Reviewer+) | Update source |
| DELETE | `/sources/{id}` | Yes (Reviewer+) | Delete source |

### Corrections

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/corrections` | No | Submit correction request (public) |
| GET | `/corrections` | Yes (Admin) | List all corrections |
| GET | `/corrections/public-log` | No | Public corrections log |
| POST | `/corrections/{id}/accept` | Yes (Admin) | Accept correction |
| POST | `/corrections/{id}/reject` | Yes (Admin) | Reject correction |
| POST | `/corrections/{id}/apply` | Yes (Admin) | Apply correction |

### Analytics

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/analytics/dashboard` | Yes (Admin) | EFCSN compliance dashboard |
| GET | `/analytics/fact-checks/monthly` | Yes (Admin) | Monthly fact-check counts |
| GET | `/analytics/ratings/distribution` | Yes (Admin) | Rating distribution |
| GET | `/analytics/corrections/rate` | Yes (Admin) | Correction rate metrics |
| GET | `/analytics/time-to-publication` | Yes (Admin) | Time-to-publication metrics |
| GET | `/analytics/compliance/checklist` | Yes (Admin) | EFCSN compliance status |

### Transparency

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/transparency/{slug}` | No | Get public transparency page |
| GET | `/transparency` | Yes (Admin) | List all transparency pages |
| POST | `/transparency` | Yes (Admin) | Create transparency page |
| PUT | `/transparency/{id}` | Yes (Admin) | Update transparency page |
| GET | `/transparency/reports/monthly/{year}/{month}` | No | Get monthly transparency report |

## Error Handling

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Submission with ID 123 not found",
  "error_code": "RESOURCE_NOT_FOUND",
  "timestamp": "2024-01-08T14:30:00Z",
  "path": "/api/v1/submissions/123"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: Invalid credentials
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `RESOURCE_CONFLICT`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Rate Limiting

Currently, rate limiting is **not enforced** in the development environment.

In production, the following limits apply:
- **Authenticated users**: 1000 requests/hour
- **Anonymous users**: 100 requests/hour
- **Correction submissions**: 10/hour per IP

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1641571200
```

## Examples

### Complete Submission Workflow

```bash
# 1. Register and login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r '.access_token')

# 2. Create a submission
SUBMISSION_ID=$(curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Climate change is a hoax",
    "submission_type": "web"
  }' | jq -r '.id')

# 3. Self-assign as reviewer (if you're a reviewer)
curl -X POST "http://localhost:8000/api/v1/submissions/$SUBMISSION_ID/reviewers/me" \
  -H "Authorization: Bearer $TOKEN"

# 4. Transition to research state
curl -X POST "http://localhost:8000/api/v1/workflow/$SUBMISSION_ID/transition" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_state": "in_research"}'

# 5. Add sources
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fact_check_id": "'"$FACT_CHECK_ID"'",
    "url": "https://climate.nasa.gov/",
    "source_type": "scientific_study",
    "credibility_rating": 5,
    "relevance": "contradicts"
  }'

# 6. Assign rating
curl -X POST "http://localhost:8000/api/v1/fact-checks/$FACT_CHECK_ID/rating" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": "FALSE",
    "justification": "Scientific consensus overwhelmingly supports climate change..."
  }'

# 7. Publish
curl -X POST "http://localhost:8000/api/v1/workflow/$SUBMISSION_ID/transition" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_state": "published"}'
```

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Set up session with auth header
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}"})

# Create submission
submission = session.post(
    f"{BASE_URL}/submissions",
    json={
        "content": "The earth is flat",
        "submission_type": "web"
    }
).json()

print(f"Created submission: {submission['id']}")

# Get all my submissions
my_submissions = session.get(
    f"{BASE_URL}/submissions",
    params={"assigned_to_me": True}
).json()

print(f"My submissions: {len(my_submissions['items'])}")
```

### JavaScript/TypeScript Client Example

```typescript
const BASE_URL = 'http://localhost:8000/api/v1';

// Login
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});

const { access_token } = await loginResponse.json();

// Create submission
const submissionResponse = await fetch(`${BASE_URL}/submissions`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    content: 'Vaccines cause autism',
    submission_type: 'web'
  })
});

const submission = await submissionResponse.json();
console.log('Created submission:', submission.id);

// Get submissions
const listResponse = await fetch(
  `${BASE_URL}/submissions?status=pending`,
  {
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);

const { items, total } = await listResponse.json();
console.log(`Found ${total} pending submissions`);
```

## Webhooks

Future feature: Webhooks for external integrations (Snapchat, Slack notifications).

## Versioning

The API uses URL versioning (`/api/v1`). Major version changes will:
- Be announced in advance
- Maintain backward compatibility for 6 months
- Provide migration guides

## Support

- **Issues**: [GitHub Issues](https://github.com/Post-X-Society/ans-project/issues)
- **Documentation**: [Full Documentation](../README.md)
- **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

Last Updated: 2026-01-08
