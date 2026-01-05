"""
Email delivery log model for tracking email notifications

Tracks all email attempts for delivery monitoring, retry logic, and audit trails
"""

import enum
from typing import Optional

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimeStampedModel


class EmailStatus(str, enum.Enum):
    """Email delivery status enumeration"""

    PENDING = "pending"  # Queued but not yet sent
    SENT = "sent"  # Successfully sent
    FAILED = "failed"  # Failed to send
    BOUNCED = "bounced"  # Bounced back
    DELIVERED = "delivered"  # Confirmed delivered (if tracking available)


class EmailLog(TimeStampedModel):
    """
    Email delivery log for tracking notifications

    Stores all email attempts for:
    - Delivery monitoring
    - Retry logic
    - Compliance audit trails
    - Opt-out enforcement
    """

    __tablename__ = "email_logs"

    to_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    template: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Template key used

    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=EmailStatus.PENDING,
        index=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Error details if failed

    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)  # Number of retry attempts

    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )  # Celery task ID for tracking

    def __repr__(self) -> str:
        return (
            f"<EmailLog(id={self.id}, to={self.to_email}, "
            f"status={self.status.value}, created_at={self.created_at})>"
        )
