# Authentication System Testing Guide

This guide explains how to test the newly implemented authentication system in the Ans frontend application.

## Prerequisites

1. Backend server must be running at `http://localhost:8000`
2. Frontend dev server must be running (typically `npm run dev`)
3. Backend must have the JWT authentication endpoints implemented

## Testing Steps

### 1. Registration Flow

1. Navigate to `http://localhost:5173` (or your dev server URL)
2. Click "Register" in the navigation bar
3. Fill in the registration form:
   - Email: `test@example.com`
   - Password: `password123` (minimum 8 characters)
   - Confirm Password: `password123`
4. Click "Create account"
5. You should be:
   - Automatically logged in
   - Redirected to `/submit`
   - See your email in the header and navigation

### 2. Login Flow

1. If logged in, click "Logout" in the navigation
2. Click "Login" in the navigation bar
3. Enter your credentials:
   - Email: `test@example.com`
   - Password: `password123`
4. Click "Sign in"
5. You should be:
   - Logged in successfully
   - Redirected to `/submit`
   - See your email and role badge (SUBMITTER) in the navigation

### 3. Protected Routes

**Test Submit Page (Requires Authentication)**
1. Logout if logged in
2. Try to navigate to `/submit`
3. You should be redirected to `/login?redirect=/submit`
4. Login and verify you're redirected back to `/submit`

**Test Admin Page (Requires Admin Role)**
1. Login as a SUBMITTER user
2. Try to navigate to `/admin`
3. You should be redirected to home (non-admin users can't access)
4. Note: Admin link won't show in nav for SUBMITTER users

### 4. Submission with Authentication

1. Login as any user
2. Navigate to `/submit`
3. Fill in the submission form:
   - Content: "This is a test claim that needs fact-checking"
   - Type: Text
4. Click "Submit for Fact-Checking"
5. The submission should succeed (JWT token automatically included)
6. Try submitting without being logged in - button should be disabled

### 5. Admin Interface (Admin/Super Admin Only)

**Note:** You'll need to create an admin user via backend or have backend create a super admin.

To create an admin user via backend CLI/API:
```bash
# Use backend's user creation endpoint or admin script
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -d '{"email":"admin@example.com","password":"admin123","role":"ADMIN"}'
```

Once you have admin credentials:

1. Login as ADMIN or SUPER_ADMIN user
2. Navigate to `/admin` (link will be visible in nav)
3. You should see the User Management table

**Test User Creation:**
1. Click "Create User" button
2. Fill in the form:
   - Email: `newuser@example.com`
   - Password: `newpass123`
   - Role: Select a role (SUBMITTER, REVIEWER, ADMIN, or SUPER_ADMIN if you're super admin)
3. Click "Create User"
4. New user should appear in the table

**Test Role Update:**
1. Find a user in the table
2. Click "Edit Role"
3. Select a different role from dropdown
4. Click "Save"
5. User's role badge should update

**Test User Activation:**
1. Find an active user
2. Click "Deactivate"
3. Status badge should change to "Inactive"
4. Click "Activate" to reactivate

### 6. Token Refresh

The system automatically refreshes tokens when they expire:

1. Login to the application
2. Wait for access token to expire (15 minutes by default)
3. Make any API request (e.g., submit a claim)
4. The system should automatically:
   - Detect the 401 error
   - Use refresh token to get new access token
   - Retry the original request
   - Complete successfully without user intervention

### 7. Logout Flow

1. While logged in, click "Logout" in navigation
2. You should be:
   - Logged out
   - Redirected to `/login`
   - No longer see user info in header/nav
   - See "Login" and "Register" buttons instead

### 8. Session Persistence

1. Login to the application
2. Close the browser tab
3. Open a new tab and navigate to the application
4. You should still be logged in (tokens stored in localStorage)
5. Your user info should be displayed

## Expected Behaviors

### Navigation Changes Based on Auth State

**When Logged Out:**
- Show: "Login" and "Register" buttons
- Hide: User email, role badge, "Logout" button, "Admin" link

**When Logged In (Non-Admin):**
- Show: User email, role badge, "Logout" button
- Hide: "Login" and "Register" buttons, "Admin" link

**When Logged In (Admin/Super Admin):**
- Show: User email, role badge, "Logout" button, "Admin" link
- Hide: "Login" and "Register" buttons

### Role Badge Colors

- SUPER_ADMIN: Purple background
- ADMIN: Blue background
- REVIEWER: Green background
- SUBMITTER: Gray background

## Troubleshooting

### Issue: Cannot submit claims (401 error)
**Solution:** Make sure you're logged in. Check if token exists in localStorage.

### Issue: Redirected to login unexpectedly
**Solution:** Token may have expired. Try logging in again.

### Issue: Admin page shows "Access Denied"
**Solution:** User must have ADMIN or SUPER_ADMIN role. Check role in navigation badge.

### Issue: Token refresh not working
**Solution:**
- Check that refresh token is valid (not expired - 7 days default)
- Verify backend `/api/v1/auth/refresh` endpoint is working
- Check browser console for errors

### Issue: User info not showing after login
**Solution:**
- Check browser localStorage for tokens (`ans_access_token`, `ans_refresh_token`, `ans_user`)
- Verify backend returns user object in login/register response
- Check browser console for errors

## API Endpoints Used

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/users` - List users (admin)
- `POST /api/v1/users` - Create user (admin)
- `PATCH /api/v1/users/{id}/role` - Update user role (admin)
- `PATCH /api/v1/users/{id}` - Update user (admin)
- `POST /api/v1/submissions` - Create submission (authenticated)

## Security Notes

- Tokens are stored in localStorage (consider httpOnly cookies for production)
- Access tokens expire after 15 minutes
- Refresh tokens expire after 7 days
- All authenticated requests include JWT in Authorization header
- Protected routes check authentication before allowing access
- Admin routes verify user role before allowing access
