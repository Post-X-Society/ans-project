"""
Tests for RTBF API endpoints - Issue #92

Following TDD approach: tests are written FIRST before implementation.
"""

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState


class TestRTBFRequestEndpoints:
    """Test RTBF request API endpoints"""

    @pytest.mark.asyncio
    async def test_create_rtbf_request(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test creating a new RTBF request via API"""
        # Create test user
        user: User = User(
            email="rtbf-api-test@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token: str = create_access_token(data={"sub": str(user.id)})

        payload: dict[str, str] = {
            "reason": "I want all my personal data to be deleted from the system",
        }

        response = client.post(
            "/api/v1/rtbf/requests",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert data["user_id"] == str(user.id)
        assert data["status"] == "pending"
        assert data["reason"] == payload["reason"]

    @pytest.mark.asyncio
    async def test_create_rtbf_request_with_dob(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test creating RTBF request with date of birth for minor detection"""
        user: User = User(
            email="minor-api@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token: str = create_access_token(data={"sub": str(user.id)})

        # Minor (15 years old)
        minor_dob: date = date.today() - timedelta(days=15 * 365)
        payload: dict[str, Any] = {
            "reason": "I am a minor and want my data deleted",
            "date_of_birth": minor_dob.isoformat(),
        }

        response = client.post(
            "/api/v1/rtbf/requests",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert data["requester_date_of_birth"] == minor_dob.isoformat()

    @pytest.mark.asyncio
    async def test_create_rtbf_request_unauthorized(self, client: TestClient) -> None:
        """Test creating RTBF request without authentication"""
        payload: dict[str, str] = {
            "reason": "Delete my data please",
        }

        response = client.post(
            "/api/v1/rtbf/requests",
            json=payload,
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_rtbf_requests(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test getting current user's RTBF requests"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        user: User = User(
            email="my-requests@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create a request for this user
        request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Test request",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(request)
        await db_session.commit()

        token: str = create_access_token(data={"sub": str(user.id)})

        response = client.get(
            "/api/v1/rtbf/requests/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data: list[dict[str, Any]] = response.json()
        assert len(data) == 1
        assert data[0]["reason"] == "Test request"


class TestRTBFAdminEndpoints:
    """Test RTBF admin API endpoints"""

    @pytest.mark.asyncio
    async def test_list_pending_requests_admin(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin listing pending RTBF requests"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        # Create admin user
        admin: User = User(
            email="admin-rtbf@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        # Create submitter users with requests
        for i in range(3):
            user: User = User(
                email=f"submitter{i}@example.com",
                password_hash="hashed_password",
                role=UserRole.SUBMITTER,
                is_active=True,
            )
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)

            request: RTBFRequest = RTBFRequest(
                user_id=user.id,
                reason=f"Request {i}",
                status=RTBFRequestStatus.PENDING,
            )
            db_session.add(request)

        await db_session.commit()
        await db_session.refresh(admin)

        token: str = create_access_token(data={"sub": str(admin.id)})

        response = client.get(
            "/api/v1/rtbf/requests",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["pending_count"] == 3

    @pytest.mark.asyncio
    async def test_list_requests_non_admin_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test non-admin cannot list all RTBF requests"""
        user: User = User(
            email="non-admin@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token: str = create_access_token(data={"sub": str(user.id)})

        response = client.get(
            "/api/v1/rtbf/requests",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_process_rtbf_request(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test admin processing an RTBF request"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        # Create admin
        admin: User = User(
            email="process-admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        # Create user with request
        user: User = User(
            email="to-be-deleted@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Delete me",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)

        token: str = create_access_token(data={"sub": str(admin.id)})

        response = client.post(
            f"/api/v1/rtbf/requests/{request.id}/process",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["status"] == "completed"
        assert data["user_anonymized"] is True

    @pytest.mark.asyncio
    async def test_reject_rtbf_request(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test admin rejecting an RTBF request"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        # Create admin
        admin: User = User(
            email="reject-admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        # Create user with request
        user: User = User(
            email="rejection-test@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Delete me",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)

        token: str = create_access_token(data={"sub": str(admin.id)})

        payload: dict[str, str] = {
            "rejection_reason": "Data required for legal proceedings",
        }

        response = client.post(
            f"/api/v1/rtbf/requests/{request.id}/reject",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == payload["rejection_reason"]


class TestDataExportEndpoints:
    """Test data export API endpoints (GDPR Article 20)"""

    @pytest.mark.asyncio
    async def test_export_my_data(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test user exporting their own data"""
        # Create user with submissions
        user: User = User(
            email="export-test@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create submissions
        submission: Submission = Submission(
            user_id=user.id,
            content="Test submission content",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()

        token: str = create_access_token(data={"sub": str(user.id)})

        response = client.get(
            "/api/v1/rtbf/export",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert "user" in data
        assert "submissions" in data
        assert "export_date" in data
        assert data["user"]["email"] == "export-test@example.com"
        assert len(data["submissions"]) == 1

    @pytest.mark.asyncio
    async def test_export_data_unauthorized(self, client: TestClient) -> None:
        """Test data export without authentication"""
        response = client.get("/api/v1/rtbf/export")
        assert response.status_code == 401


class TestDataSummaryEndpoints:
    """Test data summary endpoints for deletion preview"""

    @pytest.mark.asyncio
    async def test_get_my_data_summary(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test getting summary of user's data"""
        user: User = User(
            email="summary-test@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create submissions
        submission1: Submission = Submission(
            user_id=user.id,
            content="Published content",
            submission_type="text",
            status="completed",
            workflow_state=WorkflowState.PUBLISHED,
        )
        submission2: Submission = Submission(
            user_id=user.id,
            content="Pending content",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission1)
        db_session.add(submission2)
        await db_session.commit()

        token: str = create_access_token(data={"sub": str(user.id)})

        response = client.get(
            "/api/v1/rtbf/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["submissions_count"] == 2
        assert data["published_submissions_count"] == 1
        assert data["can_be_deleted"] is True
        assert len(data["deletion_restrictions"]) > 0
