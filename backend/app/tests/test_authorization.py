"""
Comprehensive tests for authorization and role-based access control
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


@pytest.fixture
async def submitter_user(db_session: AsyncSession) -> User:
    """Create a submitter user for testing"""
    user = User(
        email="submitter@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def reviewer_user(db_session: AsyncSession) -> User:
    """Create a reviewer user for testing"""
    user = User(
        email="reviewer@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing"""
    user = User(
        email="admin@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    """Create a super admin user for testing"""
    user = User(
        email="superadmin@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user for testing"""
    user = User(
        email="inactive@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def get_auth_header(user: User) -> dict:
    """Helper function to create authorization header"""
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


class TestGetCurrentUser:
    """Tests for GET /api/v1/users/me endpoint"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client: TestClient, submitter_user: User):
        """Test getting current user information with valid token"""
        headers = get_auth_header(submitter_user)
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == submitter_user.email
        assert data["role"] == submitter_user.role.value
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token returns 401"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token returns 401"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, client: TestClient, inactive_user: User):
        """Test getting current user when account is inactive returns 403"""
        headers = get_auth_header(inactive_user)
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()


class TestListUsers:
    """Tests for GET /api/v1/users endpoint"""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(
        self, client: TestClient, admin_user: User, submitter_user: User
    ):
        """Test admin can list all users"""
        headers = get_auth_header(admin_user)
        response = client.get("/api/v1/users", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least admin and submitter
        # Verify ordering by created_at desc
        if len(data) >= 2:
            # Newer users should come first
            assert data[0]["created_at"] >= data[1]["created_at"]

    @pytest.mark.asyncio
    async def test_list_users_as_super_admin(
        self, client: TestClient, super_admin_user: User, submitter_user: User
    ):
        """Test super admin can list all users"""
        headers = get_auth_header(super_admin_user)
        response = client.get("/api/v1/users", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_list_users_as_submitter(self, client: TestClient, submitter_user: User):
        """Test submitter cannot list users"""
        headers = get_auth_header(submitter_user)
        response = client.get("/api/v1/users", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permissions" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_users_as_reviewer(self, client: TestClient, reviewer_user: User):
        """Test reviewer cannot list users"""
        headers = get_auth_header(reviewer_user)
        response = client.get("/api/v1/users", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_own_profile(self, client: TestClient, submitter_user: User):
        """Test user can view their own profile"""
        headers = get_auth_header(submitter_user)
        response = client.get(f"/api/v1/users/{submitter_user.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == submitter_user.email
        assert data["role"] == submitter_user.role.value
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_other_user_as_submitter(
        self, client: TestClient, submitter_user: User, admin_user: User
    ):
        """Test submitter cannot view other user's profile"""
        headers = get_auth_header(submitter_user)
        response = client.get(f"/api/v1/users/{admin_user.id}", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_other_user_as_admin(
        self, client: TestClient, admin_user: User, submitter_user: User
    ):
        """Test admin can view other user's profile"""
        headers = get_auth_header(admin_user)
        response = client.get(f"/api/v1/users/{submitter_user.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == submitter_user.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, client: TestClient, admin_user: User):
        """Test getting non-existent user returns 404"""
        headers = get_auth_header(admin_user)
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/users/{fake_uuid}", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateUserRole:
    """Tests for PATCH /api/v1/users/{user_id}/role endpoint"""

    @pytest.mark.asyncio
    async def test_admin_promote_submitter_to_reviewer(
        self, client: TestClient, admin_user: User, submitter_user: User
    ):
        """Test admin can promote submitter to reviewer"""
        headers = get_auth_header(admin_user)
        response = client.patch(
            f"/api/v1/users/{submitter_user.id}/role",
            headers=headers,
            json={"role": UserRole.REVIEWER.value},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.REVIEWER.value

    @pytest.mark.asyncio
    async def test_admin_cannot_promote_to_admin(
        self, client: TestClient, admin_user: User, submitter_user: User
    ):
        """Test admin cannot promote user to admin role"""
        headers = get_auth_header(admin_user)
        response = client.patch(
            f"/api/v1/users/{submitter_user.id}/role",
            headers=headers,
            json={"role": UserRole.ADMIN.value},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "promote" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_modify_other_admin(
        self, client: TestClient, admin_user: User, db_session: AsyncSession
    ):
        """Test admin cannot modify another admin's role"""
        # Create another admin
        other_admin = User(
            email="otheradmin@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(other_admin)
        await db_session.commit()
        await db_session.refresh(other_admin)

        headers = get_auth_header(admin_user)
        response = client.patch(
            f"/api/v1/users/{other_admin.id}/role",
            headers=headers,
            json={"role": UserRole.REVIEWER.value},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "cannot modify" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_super_admin_can_promote_to_admin(
        self, client: TestClient, super_admin_user: User, submitter_user: User
    ):
        """Test super admin can promote user to admin"""
        headers = get_auth_header(super_admin_user)
        response = client.patch(
            f"/api/v1/users/{submitter_user.id}/role",
            headers=headers,
            json={"role": UserRole.ADMIN.value},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.ADMIN.value

    @pytest.mark.asyncio
    async def test_super_admin_can_modify_admin(
        self, client: TestClient, super_admin_user: User, admin_user: User
    ):
        """Test super admin can modify admin's role"""
        headers = get_auth_header(super_admin_user)
        response = client.patch(
            f"/api/v1/users/{admin_user.id}/role",
            headers=headers,
            json={"role": UserRole.REVIEWER.value},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.REVIEWER.value

    @pytest.mark.asyncio
    async def test_submitter_cannot_update_role(
        self, client: TestClient, submitter_user: User, reviewer_user: User
    ):
        """Test submitter cannot update any user's role"""
        headers = get_auth_header(submitter_user)
        response = client.patch(
            f"/api/v1/users/{reviewer_user.id}/role",
            headers=headers,
            json={"role": UserRole.SUBMITTER.value},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_role_nonexistent_user(self, client: TestClient, admin_user: User):
        """Test updating role of non-existent user returns 404"""
        headers = get_auth_header(admin_user)
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/api/v1/users/{fake_uuid}/role",
            headers=headers,
            json={"role": UserRole.REVIEWER.value},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{user_id} endpoint"""

    @pytest.mark.asyncio
    async def test_super_admin_can_delete_user(
        self, client: TestClient, super_admin_user: User, submitter_user: User
    ):
        """Test super admin can delete users"""
        headers = get_auth_header(super_admin_user)
        response = client.delete(f"/api/v1/users/{submitter_user.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_super_admin_cannot_delete_self(self, client: TestClient, super_admin_user: User):
        """Test super admin cannot delete their own account"""
        headers = get_auth_header(super_admin_user)
        response = client.delete(f"/api/v1/users/{super_admin_user.id}", headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "own account" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_user(
        self, client: TestClient, admin_user: User, submitter_user: User
    ):
        """Test admin cannot delete users"""
        headers = get_auth_header(admin_user)
        response = client.delete(f"/api/v1/users/{submitter_user.id}", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_submitter_cannot_delete_user(
        self, client: TestClient, submitter_user: User, reviewer_user: User
    ):
        """Test submitter cannot delete users"""
        headers = get_auth_header(submitter_user)
        response = client.delete(f"/api/v1/users/{reviewer_user.id}", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, client: TestClient, super_admin_user: User):
        """Test deleting non-existent user returns 404"""
        headers = get_auth_header(super_admin_user)
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/users/{fake_uuid}", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRoleHierarchy:
    """Tests for role hierarchy enforcement"""

    @pytest.mark.asyncio
    async def test_role_hierarchy_list_users(
        self,
        client: TestClient,
        submitter_user: User,
        reviewer_user: User,
        admin_user: User,
        super_admin_user: User,
    ):
        """Test role hierarchy for listing users"""
        # Submitter - should fail
        headers = get_auth_header(submitter_user)
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Reviewer - should fail
        headers = get_auth_header(reviewer_user)
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Admin - should succeed
        headers = get_auth_header(admin_user)
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Super Admin - should succeed
        headers = get_auth_header(super_admin_user)
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == status.HTTP_200_OK


class TestTokenValidation:
    """Tests for token validation edge cases"""

    @pytest.mark.asyncio
    async def test_malformed_token(self, client: TestClient):
        """Test request with malformed token"""
        headers = {"Authorization": "Bearer not.a.valid.jwt"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client: TestClient, submitter_user: User):
        """Test request with token missing Bearer prefix"""
        token_data = {
            "sub": str(submitter_user.id),
            "email": submitter_user.email,
            "role": submitter_user.role.value,
        }
        token = create_access_token(token_data)
        headers = {"Authorization": token}  # Missing "Bearer " prefix
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_with_nonexistent_user_id(self, client: TestClient):
        """Test token with user ID that doesn't exist in database"""
        token_data = {
            "sub": "00000000-0000-0000-0000-000000000000",
            "email": "nonexistent@test.com",
            "role": UserRole.SUBMITTER.value,
        }
        token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_without_sub_claim(self, client: TestClient):
        """Test token without 'sub' claim returns 401"""
        # Create token without sub claim
        token_data = {"email": "test@test.com", "role": UserRole.SUBMITTER.value}
        token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_with_invalid_uuid(self, client: TestClient):
        """Test token with invalid UUID format returns 401"""
        token_data = {
            "sub": "not-a-valid-uuid",
            "email": "test@test.com",
            "role": UserRole.SUBMITTER.value,
        }
        token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestIntegrationScenarios:
    """Integration tests for complete authorization workflows"""

    @pytest.mark.asyncio
    async def test_complete_user_management_workflow(
        self, client: TestClient, super_admin_user: User, db_session: AsyncSession
    ):
        """Test complete workflow: create user, promote, view, demote, delete"""
        # Create a new submitter user
        new_user = User(
            email="workflow@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(new_user)
        await db_session.commit()
        await db_session.refresh(new_user)

        headers = get_auth_header(super_admin_user)

        # View the user
        response = client.get(f"/api/v1/users/{new_user.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == UserRole.SUBMITTER.value

        # Promote to reviewer
        response = client.patch(
            f"/api/v1/users/{new_user.id}/role",
            headers=headers,
            json={"role": UserRole.REVIEWER.value},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == UserRole.REVIEWER.value

        # Promote to admin
        response = client.patch(
            f"/api/v1/users/{new_user.id}/role",
            headers=headers,
            json={"role": UserRole.ADMIN.value},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == UserRole.ADMIN.value

        # Demote back to submitter
        response = client.patch(
            f"/api/v1/users/{new_user.id}/role",
            headers=headers,
            json={"role": UserRole.SUBMITTER.value},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == UserRole.SUBMITTER.value

        # Delete the user
        response = client.delete(f"/api/v1/users/{new_user.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify user is deleted
        response = client.get(f"/api/v1/users/{new_user.id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
