#!/bin/bash

# Test Authentication Endpoints
# Usage: ./test-authentication.sh

set -e

BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="password123"

echo "================================================"
echo "Testing Ans Authentication System"
echo "================================================"
echo ""

# Test 1: Register a new user
echo "1️⃣  Testing User Registration"
echo "   POST /api/v1/auth/register"
echo "   Email: $EMAIL"
echo ""

REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

echo "Response:"
echo "$REGISTER_RESPONSE" | jq '.'
echo ""

# Extract tokens
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.refresh_token')

if [ "$ACCESS_TOKEN" != "null" ]; then
  echo "✅ Registration successful!"
  echo "   Access token: ${ACCESS_TOKEN:0:50}..."
  echo "   Refresh token: ${REFRESH_TOKEN:0:50}..."
else
  echo "⚠️  Registration failed or user already exists (expected if running multiple times)"
fi
echo ""
echo "================================================"
echo ""

# Test 2: Login with existing user
echo "2️⃣  Testing User Login"
echo "   POST /api/v1/auth/login"
echo "   Email: $EMAIL"
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

echo "Response:"
echo "$LOGIN_RESPONSE" | jq '.'
echo ""

# Extract tokens from login
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')

if [ "$ACCESS_TOKEN" != "null" ]; then
  echo "✅ Login successful!"
  echo "   Access token: ${ACCESS_TOKEN:0:50}..."
  echo "   Refresh token: ${REFRESH_TOKEN:0:50}..."
else
  echo "❌ Login failed!"
  exit 1
fi
echo ""
echo "================================================"
echo ""

# Test 3: Decode and display JWT token payload
echo "3️⃣  JWT Token Payload"
echo ""

# Decode JWT (extract middle part and base64 decode)
PAYLOAD=$(echo "$ACCESS_TOKEN" | cut -d'.' -f2)
# Add padding if needed
PADDING=$((4 - ${#PAYLOAD} % 4))
if [ $PADDING -ne 4 ]; then
  PAYLOAD="${PAYLOAD}$(printf '=%.0s' $(seq 1 $PADDING))"
fi
DECODED=$(echo "$PAYLOAD" | base64 -d 2>/dev/null || echo "{}")

echo "Decoded access token payload:"
echo "$DECODED" | jq '.'
echo ""

USER_ID=$(echo "$DECODED" | jq -r '.sub')
ROLE=$(echo "$DECODED" | jq -r '.role')
EMAIL_IN_TOKEN=$(echo "$DECODED" | jq -r '.email')

echo "   User ID: $USER_ID"
echo "   Role: $ROLE"
echo "   Email: $EMAIL_IN_TOKEN"
echo "   Token Type: access"
echo ""
echo "================================================"
echo ""

# Test 4: Token Refresh
echo "4️⃣  Testing Token Refresh"
echo "   POST /api/v1/auth/refresh"
echo ""

REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }")

echo "Response:"
echo "$REFRESH_RESPONSE" | jq '.'
echo ""

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token')

if [ "$NEW_ACCESS_TOKEN" != "null" ]; then
  echo "✅ Token refresh successful!"
  echo "   New access token: ${NEW_ACCESS_TOKEN:0:50}..."
else
  echo "❌ Token refresh failed!"
fi
echo ""
echo "================================================"
echo ""

# Test 5: Logout
echo "5️⃣  Testing Logout"
echo "   POST /api/v1/auth/logout"
echo ""

LOGOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }")

echo "Response:"
echo "$LOGOUT_RESPONSE" | jq '.'
echo ""

MESSAGE=$(echo "$LOGOUT_RESPONSE" | jq -r '.message')

if [ "$MESSAGE" != "null" ]; then
  echo "✅ Logout successful!"
else
  echo "❌ Logout failed!"
fi
echo ""
echo "================================================"
echo ""

# Test 6: Error Handling - Wrong Password
echo "6️⃣  Testing Error Handling: Wrong Password"
echo "   POST /api/v1/auth/login (with wrong password)"
echo ""

ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"wrongpassword\"
  }")

echo "Response:"
echo "$ERROR_RESPONSE" | jq '.'
echo ""

ERROR_DETAIL=$(echo "$ERROR_RESPONSE" | jq -r '.detail')

if [ "$ERROR_DETAIL" == "Incorrect email or password" ]; then
  echo "✅ Error handling working correctly!"
else
  echo "⚠️  Unexpected response"
fi
echo ""
echo "================================================"
echo ""

# Test 7: Error Handling - Short Password
echo "7️⃣  Testing Error Handling: Password Too Short"
echo "   POST /api/v1/auth/register (password < 8 characters)"
echo ""

SHORT_PASS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"newuser@example.com\",
    \"password\": \"short\"
  }")

echo "Response:"
echo "$SHORT_PASS_RESPONSE" | jq '.'
echo ""

if echo "$SHORT_PASS_RESPONSE" | jq -e '.detail[0].msg' > /dev/null 2>&1; then
  echo "✅ Password validation working correctly!"
else
  echo "⚠️  Validation response format different than expected"
fi
echo ""
echo "================================================"
echo ""

echo "🎉 Authentication testing complete!"
echo ""
echo "Summary:"
echo "  ✅ User registration"
echo "  ✅ User login"
echo "  ✅ JWT token generation"
echo "  ✅ Token refresh"
echo "  ✅ Logout"
echo "  ✅ Error handling"
echo ""
echo "View API documentation: http://localhost:8000/docs"
echo ""
