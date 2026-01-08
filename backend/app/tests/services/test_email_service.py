"""
Tests for email service using Celery

Following TDD approach: Tests written FIRST before implementation
Issue #94: Email Service Infrastructure
"""

from typing import Any, Generator
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.models.email_log import EmailLog, EmailStatus
from app.models.user import User, UserRole
from app.services.email_service import EmailService
from app.services.email_templates import EmailTemplate


class TestEmailService:
    """Test suite for email service functionality"""

    @pytest.fixture
    def email_service(self) -> EmailService:
        """Provide email service instance"""
        return EmailService()

    @pytest.fixture
    def mock_smtp(self) -> Generator[Mock, None, None]:
        """Provide mocked SMTP connection"""
        with patch("smtplib.SMTP") as mock:
            smtp_instance: Mock = Mock()
            mock.return_value.__enter__.return_value = smtp_instance
            yield smtp_instance

    def test_email_service_initialization(self, email_service: EmailService) -> None:
        """Test email service can be instantiated"""
        assert email_service is not None
        assert isinstance(email_service, EmailService)

    def test_smtp_configured_check(self, email_service: EmailService) -> None:
        """Test SMTP configuration validation"""
        is_configured: bool = email_service.is_configured
        assert isinstance(is_configured, bool)

    def test_send_simple_email_sync(self, email_service: EmailService, mock_smtp: Mock) -> None:
        """Test sending a simple email (synchronous)"""
        # Arrange
        to_email: str = "test@example.com"
        subject: str = "Test Subject"
        body: str = "Test email body"

        # Mock SMTP settings to make smtp_configured return True
        with patch("app.services.email_service.settings.SMTP_HOST", "smtp.example.com"), \
             patch("app.services.email_service.settings.SMTP_USER", "user"), \
             patch("app.services.email_service.settings.SMTP_PASSWORD", "pass"):
            # Act
            result: bool = email_service.send_email(
                to_email=to_email, subject=subject, body_html=body
            )

            # Assert
            assert result is True
            mock_smtp.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_async(self, email_service: EmailService, mock_smtp: Mock) -> None:
        """Test sending email asynchronously"""
        # Arrange
        to_email: str = "async@example.com"
        subject: str = "Async Test"
        body_text: str = "Plain text"
        body_html: str = "<p>HTML body</p>"

        # Mock SMTP settings to make smtp_configured return True
        with patch("app.services.email_service.settings.SMTP_HOST", "smtp.example.com"), \
             patch("app.services.email_service.settings.SMTP_USER", "user"), \
             patch("app.services.email_service.settings.SMTP_PASSWORD", "pass"):
            # Act
            result: bool = await email_service.send_email_async(
                to_email=to_email, subject=subject, body_text=body_text, body_html=body_html
            )

            # Assert
            assert result is True
            mock_smtp.sendmail.assert_called_once()


class TestEmailDeliveryTracking:
    """Test email delivery tracking functionality"""

    @pytest.mark.asyncio
    async def test_create_email_log(self, db_session: Any) -> None:
        """Test creating email delivery log entry"""
        # Arrange
        email_log: EmailLog = EmailLog(
            to_email="test@example.com",
            subject="Test Subject",
            template="submission_received",
            status=EmailStatus.SENT,
        )

        # Act
        db_session.add(email_log)
        await db_session.commit()
        await db_session.refresh(email_log)

        # Assert
        assert email_log.id is not None
        assert email_log.to_email == "test@example.com"
        assert email_log.status == EmailStatus.SENT
        assert email_log.created_at is not None


class TestEmailOptOut:
    """Test email opt-out functionality"""

    @pytest.mark.asyncio
    async def test_user_can_opt_out_of_emails(self, db_session: Any) -> None:
        """Test users can opt out of email notifications"""
        # Arrange
        user: User = User(
            email="optout@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            email_opt_out=False,
        )
        db_session.add(user)
        await db_session.commit()

        # Act
        user.email_opt_out = True
        await db_session.commit()
        await db_session.refresh(user)

        # Assert
        assert user.email_opt_out is True

    @pytest.mark.asyncio
    async def test_do_not_send_to_opted_out_users(self, db_session: Any) -> None:
        """Test emails are not sent to users who opted out"""
        with patch("smtplib.SMTP") as mock_smtp:
            smtp_instance: Mock = Mock()
            mock_smtp.return_value.__enter__.return_value = smtp_instance

            # Arrange
            user: User = User(
                email="opted_out@example.com",
                password_hash="hashed",
                role=UserRole.SUBMITTER,
                email_opt_out=True,
            )
            db_session.add(user)
            await db_session.commit()

            email_service: EmailService = EmailService()

            # Act
            result: bool = await email_service.send_email_async(
                to_email=user.email,
                subject="Test",
                body_text="Body",
                db=db_session,
            )

            # Assert - Email should not be sent
            assert result is False
            smtp_instance.sendmail.assert_not_called()


class TestEmailTemplates:
    """Test email template rendering"""

    @pytest.fixture
    def email_service(self) -> EmailService:
        """Provide email service instance"""
        return EmailService()

    def test_submission_received_template(self, email_service: EmailService) -> None:
        """Test submission received email template"""
        # Arrange
        context: dict[str, Any] = {
            "submission_id": str(uuid4()),
            "claim_text": "Is this true?",
            "opt_out_url": "https://example.com/opt-out",
        }

        # Act
        subject, body = email_service.render_template(
            EmailTemplate.SUBMISSION_RECEIVED.value, context
        )

        # Assert
        assert "submission" in subject.lower() or "received" in subject.lower()
        assert context["submission_id"] in body
        assert context["claim_text"] in body

    def test_workflow_update_template(self, email_service: EmailService) -> None:
        """Test workflow status update email template"""
        # Arrange
        context: dict[str, Any] = {
            "submission_id": str(uuid4()),
            "new_status": "IN_RESEARCH",
            "reviewer_name": "John Doe",
            "submission_url": "https://example.com/submissions/123",
            "opt_out_url": "https://example.com/opt-out",
        }

        # Act
        subject, body = email_service.render_template(EmailTemplate.WORKFLOW_UPDATE.value, context)

        # Assert
        assert "status" in subject.lower() or "update" in subject.lower()
        assert context["new_status"] in body
        assert context["reviewer_name"] in body
