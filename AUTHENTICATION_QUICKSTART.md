# Authentication System - Quick Start Guide

## What Was Implemented

A complete frontend authentication system for the Ans fact-checking application, including:

- User registration and login
- JWT token management with automatic refresh
- Protected routes (authentication required)
- Role-based access control (admin panel)
- Admin user management interface
- Session persistence

## Getting Started

### 1. Start the Backend (if not already running)

```bash
cd backend
# Activate virtual environment and start server
# The backend should be running at http://localhost:8000
```

### 2. Start the Frontend

```bash
cd frontend
npm run dev
# Frontend should start at http://localhost:5173
```

### 3. Test Basic Auth Flow

#### Register a New User
1. Open http://localhost:5173
2. Click "Register" in the navigation
3. Fill in:
   - Email: `user@example.com`
   - Password: `password123`
   - Confirm Password: `password123`
4. Click "Create account"
5. You'll be auto-logged in and redirected to `/submit`

#### Submit a Claim
1. While logged in, go to `/submit`
2. Enter a claim (10-5000 characters)
3. Select type (text/image/url)
4. Click "Submit for Fact-Checking"
5. Submission should succeed with JWT authentication

#### Logout
1. Click "Logout" in the navigation
2. You'll be logged out and redirected to login page

### 4. Test Admin Features

You'll need an admin user. Create one via backend:

```bash
# Option 1: Use backend CLI/management command
cd backend
python -m app.scripts.create_admin admin@example.com admin123

# Option 2: Use the API (requires existing super admin token)
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -d '{"email":"admin@example.com","password":"admin123","role":"ADMIN"}'
```

Then:
1. Login with admin credentials
2. Navigate to `/admin` (link visible in nav)
3. Create users, update roles, activate/deactivate users

## File Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api/
│   │   │   ├── auth.ts          # Auth API functions (login, register, etc.)
│   │   │   ├── users.ts         # User management API (admin)
│   │   │   ├── client.ts        # Modified: JWT interceptors
│   │   │   └── types.ts         # Modified: Auth types added
│   │   ├── stores/
│   │   │   └── auth.ts          # Auth state management
│   │   └── components/
│   │       ├── Nav.svelte       # Modified: Auth UI
│   │       ├── Header.svelte    # Modified: User display
│   │       └── SubmissionForm.svelte  # Modified: Auth check
│   └── routes/
│       ├── login/
│       │   └── +page.svelte     # Login page
│       ├── register/
│       │   └── +page.svelte     # Register page
│       ├── admin/
│       │   ├── +page.svelte     # Modified: User management UI
│       │   └── +page.ts         # Route guard (admin only)
│       └── submit/
│           └── +page.ts         # Route guard (auth required)
├── AUTHENTICATION_TESTING.md           # Detailed testing guide
└── AUTHENTICATION_IMPLEMENTATION_SUMMARY.md  # Technical details
```

## Key Features

### 1. Automatic Token Refresh
- Access tokens expire after 15 minutes
- System automatically refreshes using refresh token
- No user intervention needed
- Failed requests are retried after refresh

### 2. Session Persistence
- Tokens stored in localStorage
- User stays logged in across page refreshes
- User stays logged in across browser tabs
- Logout clears all session data

### 3. Protected Routes
- `/submit` requires authentication
- `/admin` requires ADMIN or SUPER_ADMIN role
- Unauthorized access redirects to login
- Preserves intended destination URL

### 4. Role-Based UI
- Navigation shows/hides based on auth state
- Admin link only visible to admins
- Role badges color-coded by level
- User info displayed in header when logged in

### 5. Error Handling
- User-friendly error messages
- Specific handling for auth failures
- Links to recovery actions (e.g., login)
- Console logging for debugging

## Common Issues & Solutions

### Issue: 401 Errors on Submission
**Cause:** Not logged in or token expired
**Solution:** Login again

### Issue: Can't Access Admin Panel
**Cause:** User lacks admin role
**Solution:** User must be ADMIN or SUPER_ADMIN

### Issue: Tokens Not Persisting
**Cause:** localStorage disabled or private browsing
**Solution:** Enable localStorage or exit private browsing

### Issue: CORS Errors
**Cause:** Backend CORS not configured for frontend origin
**Solution:** Add frontend URL to backend CORS allowed origins

## API Endpoints Reference

| Method | Endpoint | Auth Required | Role Required | Description |
|--------|----------|---------------|---------------|-------------|
| POST | /api/v1/auth/register | No | - | Register new user |
| POST | /api/v1/auth/login | No | - | Login user |
| POST | /api/v1/auth/refresh | No | - | Refresh access token |
| POST | /api/v1/auth/logout | Yes | - | Logout user |
| GET | /api/v1/users | Yes | ADMIN+ | List users |
| POST | /api/v1/users | Yes | ADMIN+ | Create user |
| PATCH | /api/v1/users/{id}/role | Yes | ADMIN+ | Update user role |
| PATCH | /api/v1/users/{id} | Yes | ADMIN+ | Update user |
| POST | /api/v1/submissions | Yes | - | Submit claim |

## User Roles

| Role | Level | Permissions |
|------|-------|-------------|
| SUBMITTER | 1 | Submit claims |
| REVIEWER | 2 | Submit + review claims |
| ADMIN | 3 | Submit + review + manage users |
| SUPER_ADMIN | 4 | Full system access |

## Environment Variables

```bash
# Frontend (.env)
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## Next Steps

1. **Test the complete flow** using AUTHENTICATION_TESTING.md
2. **Review technical details** in AUTHENTICATION_IMPLEMENTATION_SUMMARY.md
3. **Customize styling** if needed (Tailwind CSS classes)
4. **Add email verification** for production use
5. **Implement password reset** for better UX
6. **Consider httpOnly cookies** for enhanced security

## Support

For detailed testing instructions, see: `frontend/AUTHENTICATION_TESTING.md`
For implementation details, see: `frontend/AUTHENTICATION_IMPLEMENTATION_SUMMARY.md`

## Success Criteria

You'll know everything is working when:
- ✓ You can register a new user
- ✓ You can login with credentials
- ✓ Submit page is protected (redirects when logged out)
- ✓ You can submit claims when authenticated
- ✓ Admin panel is accessible to admin users
- ✓ You can create and manage users in admin panel
- ✓ Session persists across page refreshes
- ✓ Logout clears session and redirects to login
