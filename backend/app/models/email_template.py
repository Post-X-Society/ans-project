"""
Email template model for multilingual transactional emails

Issue #95: Email Templates (Multilingual EN/NL)
ADR 0004: Multilingual Support with Text-Based Language Files
ADR 0005: EFCSN Compliance Architecture

Stores email templates in database for runtime editability without deployment
"""

import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

# Cross-database compatible JSONB type (JSONB for PostgreSQL, JSON for SQLite)
JSONType = JSON().with_variant(JSONB, "postgresql")


class EmailTemplateType(str, enum.Enum):
    """Email template type enumeration"""

    # Submission & Review
    SUBMISSION_RECEIVED = "submission_received"
    REVIEWER_ASSIGNED = "reviewer_assigned"
    REVIEW_ASSIGNED = "review_assigned"
    REVIEW_COMPLETED = "review_completed"

    # Workflow Status Updates
    WORKFLOW_UPDATE = "workflow_update"
    WORKFLOW_SUBMITTED = "workflow_submitted"
    WORKFLOW_QUEUED = "workflow_queued"
    WORKFLOW_ASSIGNED = "workflow_assigned"
    WORKFLOW_IN_RESEARCH = "workflow_in_research"
    WORKFLOW_DRAFT_READY = "workflow_draft_ready"
    WORKFLOW_ADMIN_REVIEW = "workflow_admin_review"
    WORKFLOW_PEER_REVIEW = "workflow_peer_review"
    WORKFLOW_FINAL_APPROVAL = "workflow_final_approval"
    WORKFLOW_PUBLISHED = "workflow_published"
    WORKFLOW_REJECTED = "workflow_rejected"

    # Corrections
    CORRECTION_REQUEST_RECEIVED = "correction_request_received"
    CORRECTION_APPROVED = "correction_approved"
    CORRECTION_REJECTED = "correction_rejected"
    CORRECTION_RESOLUTION = "correction_resolution"

    # Peer Review
    PEER_REVIEW_REQUEST = "peer_review_request"
    PEER_REVIEW_COMPLETED = "peer_review_completed"

    # Publishing
    FACT_CHECK_PUBLISHED = "fact_check_published"

    # Drafts & Reminders
    DRAFT_REMINDER = "draft_reminder"
    TRANSPARENCY_PAGE_REVIEW_REMINDER = "transparency_page_review_reminder"

    # System & User Management
    SYSTEM_NOTIFICATION = "system_notification"
    WEEKLY_DIGEST = "weekly_digest"
    PASSWORD_RESET = "password_reset"
    WELCOME_EMAIL = "welcome_email"
    ACCOUNT_VERIFICATION = "account_verification"


class EmailTemplate(TimeStampedModel):
    """
    Email template model for multilingual transactional emails

    Stores templates in database for:
    - Runtime editability without deployment
    - Multilingual support (EN, NL)
    - Version control and audit trail
    - A/B testing capabilities (future)
    """

    __tablename__ = "email_templates"

    template_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    """Unique identifier for the template (e.g., 'submission_received')"""

    template_type: Mapped[EmailTemplateType] = mapped_column(
        Enum(EmailTemplateType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )
    """Template type from enum for categorization"""

    name: Mapped[dict[str, str]] = mapped_column(
        JSONType, nullable=False
    )  # {"en": "Submission Received", "nl": "Inzending Ontvangen"}
    """Human-readable template name (multilingual)"""

    description: Mapped[dict[str, str]] = mapped_column(
        JSONType, nullable=False
    )  # {"en": "Sent when...", "nl": "Verzonden wanneer..."}
    """Template description for admin reference (multilingual)"""

    subject: Mapped[dict[str, str]] = mapped_column(
        JSONType, nullable=False
    )  # {"en": "Your submission...", "nl": "Uw inzending..."}
    """Email subject line (multilingual, supports Jinja2 variables)"""

    body_text: Mapped[dict[str, str]] = mapped_column(
        JSONType, nullable=False
    )  # {"en": "Dear {{name}}...", "nl": "Beste {{name}}..."}
    """Plain text email body (multilingual, supports Jinja2 variables)"""

    body_html: Mapped[dict[str, str]] = mapped_column(
        JSONType, nullable=False
    )  # {"en": "<html>...</html>", "nl": "<html>...</html>"}
    """HTML email body (multilingual, supports Jinja2 variables)"""

    variables: Mapped[dict[str, str]] = mapped_column(
        JSONType, nullable=False
    )  # {"submission_id": "string", "claim_text": "string", ...}
    """Available template variables and their types for validation"""

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    """Whether this template is currently active"""

    version: Mapped[int] = mapped_column(nullable=False, default=1)
    """Template version number for tracking changes"""

    last_modified_by: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # User email
    """Email of user who last modified this template"""

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    """Internal notes about template changes or usage"""

    def __repr__(self) -> str:
        return (
            f"<EmailTemplate(key={self.template_key}, "
            f"type={self.template_type.value}, version={self.version})>"
        )
