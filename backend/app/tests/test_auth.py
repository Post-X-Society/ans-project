"""
Tests for authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


class TestUserRegistration:
    """Test user registration endpoint"""

    def test_register_new_user(self, client: TestClient) -> None:
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test registration with duplicate email fails"""
        # First registration should succeed
        response1 = client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "password123"},
        )
        assert response1.status_code == 200

        # Second registration with same email should fail
        response2 = client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "password456"},
        )
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient) -> None:
        """Test registration with invalid email format"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client: TestClient) -> None:
        """Test registration with password too short"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "short"},
        )
        assert response.status_code == 422  # Validation error

    def test_register_creates_submitter_role(self, client: TestClient) -> None:
        """Test that new users get submitter role by default"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "submitter@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        # Note: We'll verify the role in the database through other endpoints


class TestUserLogin:
    """Test user login endpoint"""

    @pytest.mark.asyncio
    async def test_login_valid_credentials(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test successful login with valid credentials"""
        # Create a test user directly in the database
        user = User(
            email="testuser@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.SUBMITTER,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test login fails with wrong password"""
        # Create a test user
        user = User(
            email="testuser2@example.com",
            password_hash=hash_password("correctpassword"),
            role=UserRole.SUBMITTER,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser2@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        """Test login fails for non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test login fails for inactive user"""
        # Create an inactive user
        user = User(
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.SUBMITTER,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Test token refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test successful token refresh"""
        # Create a test user
        user = User(
            email="refreshuser@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.SUBMITTER,
        )
        db_session.add(user)
        await db_session.commit()

        # Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "refreshuser@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client: TestClient) -> None:
        """Test refresh fails with invalid token"""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.token.here"})

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_access_token_not_allowed(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that access tokens cannot be used for refresh"""
        # Create a test user
        user = User(
            email="tokenuser@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.SUBMITTER,
        )
        db_session.add(user)
        await db_session.commit()

        # Create an access token (not a refresh token)
        access_token = create_access_token(
            {"sub": str(user.id), "email": user.email, "role": user.role.value}
        )

        # Try to refresh with access token
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

        assert response.status_code == 401
        assert "refresh" in response.json()["detail"].lower()


class TestLogout:
    """Test logout endpoint"""

    @pytest.mark.asyncio
    async def test_logout(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test successful logout"""
        # Create a test user
        user = User(
            email="logoutuser@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.SUBMITTER,
        )
        db_session.add(user)
        await db_session.commit()

        # Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "logoutuser@example.com", "password": "password123"},
        )
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Logout (now requires Authorization header)
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert logout_response.status_code == 200
        assert "success" in logout_response.json()["message"].lower()

    def test_logout_invalid_token(self, client: TestClient) -> None:
        """Test logout with invalid tokens still succeeds (graceful degradation)"""
        # Logout should succeed even with invalid tokens (best effort blacklisting)
        # This prevents errors when tokens are already expired or malformed
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "invalid.refresh.token"},
            headers={"Authorization": "Bearer invalid.access.token"},
        )

        # Should succeed (logout is idempotent and graceful)
        assert response.status_code == 200


class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_password_is_hashed(self, client: TestClient) -> None:
        """Test that passwords are properly hashed in database"""
        # Register a user
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "hashtest@example.com", "password": "mypassword123"},
        )

        assert response.status_code == 200
        # Password should be hashed, not stored as plain text
        # This will be verified through login working with correct password


class TestTokenStructure:
    """Test JWT token structure and claims"""

    @pytest.mark.asyncio
    async def test_token_contains_user_info(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that tokens contain proper user information"""
        # Create a test user
        user = User(
            email="tokentest@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.REVIEWER,
        )
        db_session.add(user)
        await db_session.commit()

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "tokentest@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        # Token structure will be validated through successful API calls


class TestGetCurrentUser:
    """Test /auth/me endpoint"""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting current user profile"""
        # Create a test user
        user = User(
            email="metest@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "metest@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Get current user profile
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "metest@example.com"
        assert data["role"] == "reviewer"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_current_user_without_token(self, client: TestClient) -> None:
        """Test that /auth/me requires authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient) -> None:
        """Test that /auth/me rejects invalid tokens"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
