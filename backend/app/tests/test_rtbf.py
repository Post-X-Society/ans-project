"""
Tests for Right to be Forgotten (RTBF) workflow - Issue #92

Following TDD approach: tests are written FIRST before implementation.
These tests cover:
1. RTBF request model
2. RTBF service operations
3. Personal data deletion workflow
4. Anonymization for published content
5. Data export functionality (GDPR Article 20)
6. Automatic minor anonymization
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState


class TestRTBFRequestModel:
    """Test RTBF request model creation and validation"""

    @pytest.mark.asyncio
    async def test_create_rtbf_request(self, db_session: AsyncSession) -> None:
        """Test creating a new RTBF request"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        # Create a test user first
        user: User = User(
            email="rtbf-test@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create RTBF request
        rtbf_request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="I want my data deleted",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(rtbf_request)
        await db_session.commit()
        await db_session.refresh(rtbf_request)

        # Assert
        assert rtbf_request.id is not None
        assert isinstance(rtbf_request.id, UUID)
        assert rtbf_request.user_id == user.id
        assert rtbf_request.reason == "I want my data deleted"
        assert rtbf_request.status == RTBFRequestStatus.PENDING
        assert rtbf_request.created_at is not None

    @pytest.mark.asyncio
    async def test_rtbf_request_status_transitions(self, db_session: AsyncSession) -> None:
        """Test RTBF request status transitions"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        user: User = User(
            email="rtbf-status@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        rtbf_request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Test status transitions",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(rtbf_request)
        await db_session.commit()

        # Transition to processing
        rtbf_request.status = RTBFRequestStatus.PROCESSING
        await db_session.commit()
        await db_session.refresh(rtbf_request)
        assert rtbf_request.status == RTBFRequestStatus.PROCESSING

        # Transition to completed
        rtbf_request.status = RTBFRequestStatus.COMPLETED
        rtbf_request.completed_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(rtbf_request)
        assert rtbf_request.status == RTBFRequestStatus.COMPLETED
        assert rtbf_request.completed_at is not None

    @pytest.mark.asyncio
    async def test_rtbf_request_with_date_of_birth(self, db_session: AsyncSession) -> None:
        """Test RTBF request stores date of birth for minor detection"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus

        user: User = User(
            email="rtbf-minor@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create request with date of birth (minor - 15 years old)
        minor_dob: date = date.today() - timedelta(days=15 * 365)
        rtbf_request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Minor data deletion",
            status=RTBFRequestStatus.PENDING,
            requester_date_of_birth=minor_dob,
        )
        db_session.add(rtbf_request)
        await db_session.commit()
        await db_session.refresh(rtbf_request)

        assert rtbf_request.requester_date_of_birth == minor_dob


class TestRTBFService:
    """Test RTBF service operations"""

    @pytest.mark.asyncio
    async def test_create_rtbf_request_service(self, db_session: AsyncSession) -> None:
        """Test creating RTBF request via service"""
        from app.models.rtbf_request import RTBFRequestStatus
        from app.services.rtbf_service import RTBFService

        # Create test user
        user: User = User(
            email="rtbf-service@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create request via service
        service: RTBFService = RTBFService(db_session)
        request = await service.create_request(
            user_id=user.id,
            reason="Service test deletion request",
        )

        assert request.id is not None
        assert request.user_id == user.id
        assert request.status == RTBFRequestStatus.PENDING

    @pytest.mark.asyncio
    async def test_delete_user_personal_data(self, db_session: AsyncSession) -> None:
        """Test deleting user's personal data (email anonymization)"""
        from app.services.rtbf_service import RTBFService

        # Create test user with submission
        user: User = User(
            email="delete-me@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        user_id: UUID = user.id

        # Create submission in non-published state
        submission: Submission = Submission(
            user_id=user.id,
            content="Test content for deletion",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Delete personal data
        service: RTBFService = RTBFService(db_session)
        result = await service.delete_user_personal_data(user_id)

        assert result["user_anonymized"] is True
        assert result["submissions_deleted"] == 1

        # Verify user email is anonymized
        await db_session.refresh(user)
        assert user.email.startswith("deleted_")
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_anonymize_published_content(self, db_session: AsyncSession) -> None:
        """Test anonymization preserves published content but removes PII"""
        from app.services.rtbf_service import RTBFService

        # Create test user with published submission
        user: User = User(
            email="anonymize-me@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create published submission (should be anonymized, not deleted)
        submission: Submission = Submission(
            user_id=user.id,
            content="Important fact-check content",
            submission_type="text",
            status="completed",
            workflow_state=WorkflowState.PUBLISHED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        submission_id: UUID = submission.id

        # Process RTBF request
        service: RTBFService = RTBFService(db_session)
        result = await service.delete_user_personal_data(user.id)

        # Published content should be preserved but user link anonymized
        assert result["submissions_anonymized"] == 1
        assert result["submissions_deleted"] == 0

        # Verify submission still exists
        stmt = select(Submission).where(Submission.id == submission_id)
        db_result = await db_session.execute(stmt)
        existing_submission = db_result.scalar_one_or_none()
        assert existing_submission is not None
        assert existing_submission.content == "Important fact-check content"

    @pytest.mark.asyncio
    async def test_reject_rtbf_request(self, db_session: AsyncSession) -> None:
        """Test rejecting RTBF request with reason"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus
        from app.services.rtbf_service import RTBFService

        user: User = User(
            email="reject-rtbf@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        rtbf_request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Delete my data",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(rtbf_request)
        await db_session.commit()
        await db_session.refresh(rtbf_request)

        service: RTBFService = RTBFService(db_session)
        rejected = await service.reject_request(
            request_id=rtbf_request.id,
            rejection_reason="Legal hold on data",
        )

        assert rejected.status == RTBFRequestStatus.REJECTED
        assert rejected.rejection_reason == "Legal hold on data"


class TestDataExport:
    """Test data export functionality (GDPR Article 20)"""

    @pytest.mark.asyncio
    async def test_export_user_data(self, db_session: AsyncSession) -> None:
        """Test exporting all user data in portable format"""
        from app.services.rtbf_service import RTBFService

        # Create test user with submissions
        user: User = User(
            email="export-me@example.com",
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
            content="First submission content",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        submission2: Submission = Submission(
            user_id=user.id,
            content="Second submission content",
            submission_type="url",
            status="pending",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission1)
        db_session.add(submission2)
        await db_session.commit()

        # Export user data
        service: RTBFService = RTBFService(db_session)
        export_data: dict[str, Any] = await service.export_user_data(user.id)

        # Verify export structure
        assert "user" in export_data
        assert "submissions" in export_data
        assert "export_date" in export_data

        # Verify user data
        assert export_data["user"]["email"] == "export-me@example.com"
        assert export_data["user"]["role"] == "submitter"

        # Verify submissions
        assert len(export_data["submissions"]) == 2

    @pytest.mark.asyncio
    async def test_export_user_data_includes_all_related_data(
        self, db_session: AsyncSession
    ) -> None:
        """Test export includes all related data (submissions, corrections, etc.)"""
        from app.services.rtbf_service import RTBFService

        user: User = User(
            email="full-export@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service: RTBFService = RTBFService(db_session)
        export_data: dict[str, Any] = await service.export_user_data(user.id)

        # Verify all expected keys are present
        expected_keys: list[str] = ["user", "submissions", "export_date", "format_version"]
        for key in expected_keys:
            assert key in export_data


class TestMinorAnonymization:
    """Test automatic minor anonymization (age detection)"""

    @pytest.mark.asyncio
    async def test_detect_minor_from_date_of_birth(self, db_session: AsyncSession) -> None:
        """Test detecting if user is a minor based on date of birth"""
        from app.services.rtbf_service import RTBFService

        service: RTBFService = RTBFService(db_session)

        # Test minor (15 years old)
        minor_dob: date = date.today() - timedelta(days=15 * 365)
        assert service.is_minor(minor_dob) is True

        # Test adult (20 years old)
        adult_dob: date = date.today() - timedelta(days=20 * 365)
        assert service.is_minor(adult_dob) is False

        # Test edge case (exactly 18)
        edge_dob: date = date.today() - timedelta(days=18 * 365)
        assert service.is_minor(edge_dob) is False

    @pytest.mark.asyncio
    async def test_auto_anonymize_minor_data(self, db_session: AsyncSession) -> None:
        """Test automatic anonymization when user is detected as minor"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus
        from app.services.rtbf_service import RTBFService

        user: User = User(
            email="minor-user@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create RTBF request for a minor
        minor_dob: date = date.today() - timedelta(days=15 * 365)
        rtbf_request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Minor data deletion",
            status=RTBFRequestStatus.PENDING,
            requester_date_of_birth=minor_dob,
        )
        db_session.add(rtbf_request)
        await db_session.commit()
        await db_session.refresh(rtbf_request)

        service: RTBFService = RTBFService(db_session)

        # Process should auto-approve for minors
        result = await service.process_request(rtbf_request.id)

        # Minor requests should be auto-approved and processed
        assert result["auto_approved"] is True
        assert result["reason"] == "minor_protection"

    @pytest.mark.asyncio
    async def test_minor_age_threshold_configuration(self, db_session: AsyncSession) -> None:
        """Test minor age threshold is configurable (default 18)"""
        from app.services.rtbf_service import RTBFService

        service: RTBFService = RTBFService(db_session)

        # Default threshold should be 18
        assert service.minor_age_threshold == 18

        # 17 year old should be minor
        seventeen_dob: date = date.today() - timedelta(days=17 * 365)
        assert service.is_minor(seventeen_dob) is True

        # 18 year old should not be minor
        eighteen_dob: date = date.today() - timedelta(days=18 * 365)
        assert service.is_minor(eighteen_dob) is False


class TestRTBFRequestList:
    """Test listing and managing RTBF requests"""

    @pytest.mark.asyncio
    async def test_list_pending_requests(self, db_session: AsyncSession) -> None:
        """Test listing pending RTBF requests for admin"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus
        from app.services.rtbf_service import RTBFService

        # Create multiple users with requests
        users: list[User] = []
        for i in range(3):
            user: User = User(
                email=f"user{i}@example.com",
                password_hash="hashed_password",
                role=UserRole.SUBMITTER,
                is_active=True,
            )
            db_session.add(user)
            users.append(user)
        await db_session.commit()

        # Create requests with different statuses
        for i, user in enumerate(users):
            await db_session.refresh(user)
            status = RTBFRequestStatus.PENDING if i < 2 else RTBFRequestStatus.COMPLETED
            request: RTBFRequest = RTBFRequest(
                user_id=user.id,
                reason=f"Request {i}",
                status=status,
            )
            db_session.add(request)
        await db_session.commit()

        service: RTBFService = RTBFService(db_session)
        pending = await service.list_pending_requests()

        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_get_request_by_id(self, db_session: AsyncSession) -> None:
        """Test getting RTBF request by ID"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus
        from app.services.rtbf_service import RTBFService

        user: User = User(
            email="get-request@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        rtbf_request: RTBFRequest = RTBFRequest(
            user_id=user.id,
            reason="Test request",
            status=RTBFRequestStatus.PENDING,
        )
        db_session.add(rtbf_request)
        await db_session.commit()
        await db_session.refresh(rtbf_request)

        service: RTBFService = RTBFService(db_session)
        found = await service.get_request_by_id(rtbf_request.id)

        assert found is not None
        assert found.id == rtbf_request.id
        assert found.reason == "Test request"

    @pytest.mark.asyncio
    async def test_get_user_requests(self, db_session: AsyncSession) -> None:
        """Test getting all RTBF requests for a specific user"""
        from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus
        from app.services.rtbf_service import RTBFService

        user: User = User(
            email="multiple-requests@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create multiple requests for same user
        for i in range(2):
            request: RTBFRequest = RTBFRequest(
                user_id=user.id,
                reason=f"Request {i}",
                status=RTBFRequestStatus.PENDING,
            )
            db_session.add(request)
        await db_session.commit()

        service: RTBFService = RTBFService(db_session)
        user_requests = await service.get_user_requests(user.id)

        assert len(user_requests) == 2
