"""
Email service for sending notifications.

Issue #83: Backend: Transparency Page Service with Versioning
Issue #94: Backend: Email Service Infrastructure (Celery + SMTP)
ADR 0005: EFCSN Compliance Architecture

Supports:
- Annual review reminder emails for transparency pages
- Transactional email notifications (submissions, corrections, reviews)
- Async email sending with SMTP
- Email delivery tracking
- User opt-out mechanism
- Celery queue integration
"""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        """Initialize email service with settings."""
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS

    @property
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return settings.smtp_configured

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email synchronously.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional, derived from HTML if not provided)

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("SMTP not configured, skipping email send")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add plain text part
            if body_text is None:
                # Simple HTML to text conversion
                import re

                body_text = re.sub("<[^<]+?>", "", body_html)
            msg.attach(MIMEText(body_text, "plain"))

            # Add HTML part
            msg.attach(MIMEText(body_html, "html"))

            # Send email
            with smtplib.SMTP(self.host, self.port) as server:  # type: ignore[arg-type]
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)  # type: ignore[arg-type]
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_email_async(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        template: Optional[str] = None,
    ) -> bool:
        """
        Send email asynchronously with opt-out checking and delivery tracking.

        Issue #94: Async wrapper for email sending with database tracking

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)
            db: Database session for logging and opt-out checking (optional)
            template: Template key used (optional, for logging)

        Returns:
            True if email sent successfully, False otherwise
        """
        # Check opt-out status if database session provided
        if db is not None:
            from app.models.user import User

            stmt = select(User).where(User.email == to_email)
            result = await db.execute(stmt)
            user: Optional[User] = result.scalar_one_or_none()

            if user and user.email_opt_out:
                # User opted out - do not send
                logger.info(f"Email not sent to {to_email}: user opted out")
                if db is not None:
                    await self._log_email(
                        db=db,
                        to_email=to_email,
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                        template=template,
                        status="failed",
                        error_message="User opted out of emails",
                    )
                return False

        # Send email in thread pool to avoid blocking
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.send_email,
                to_email,
                subject,
                body_html or body_text,
                body_text,
            )

            # Log successful delivery
            if db is not None:
                await self._log_email(
                    db=db,
                    to_email=to_email,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    template=template,
                    status="sent",
                )

            return True

        except Exception as e:
            logger.error(f"Async email send failed to {to_email}: {e}")
            # Log failed delivery
            if db is not None:
                await self._log_email(
                    db=db,
                    to_email=to_email,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    template=template,
                    status="failed",
                    error_message=str(e),
                )

            return False

    async def send_template_email(
        self,
        template: str,
        to_email: str,
        context: dict[str, Any],
        db: Optional[AsyncSession] = None,
        language: str = "en",
    ) -> bool:
        """
        Send email using database-backed template with multilingual support.

        Issue #95: Database-backed multilingual templates

        Args:
            template: Email template identifier (template_key)
            to_email: Recipient email address
            context: Template variables
            db: Database session for logging and template retrieval (required)
            language: Language code (en, nl) - defaults to en

        Returns:
            True if email sent successfully, False otherwise
        """
        from app.services.email_template_service import EmailTemplateService

        if db is None:
            logger.error("Database session required for template email sending")
            return False

        try:
            # Use database-backed template service
            template_service = EmailTemplateService()

            subject, body_text, body_html = await template_service.render_template(
                db, template, context, language
            )

            return await self.send_email_async(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                db=db,
                template=template,
            )
        except Exception as e:
            logger.error(f"Template email send failed: {e}")
            return False

    def queue_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        template: Optional[str] = None,
    ) -> str:
        """
        Queue email for async delivery via Celery.

        Issue #94: Celery integration for email queue

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            template: Template key (optional)

        Returns:
            Celery task ID
        """
        from app.tasks.email_tasks import send_email_task

        task = send_email_task.delay(
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            template=template,
        )
        return str(task.id)

    def render_template(self, template: str, context: dict[str, Any]) -> tuple[str, str]:
        """
        Render email template.

        Issue #94: Template rendering helper

        Args:
            template: Email template identifier
            context: Template variables

        Returns:
            Tuple of (subject, body_text)

        Raises:
            ValueError: If template not found
        """
        from app.services.email_templates import EmailTemplate, render_template

        if isinstance(template, str):
            template_enum = EmailTemplate(template)
        else:
            template_enum = template

        subject, body_text, _ = render_template(template_enum, context)
        return subject, body_text

    async def _log_email(
        self,
        db: AsyncSession,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str],
        template: Optional[str],
        status: str,
        error_message: Optional[str] = None,
        celery_task_id: Optional[str] = None,
    ) -> None:
        """
        Log email delivery attempt.

        Issue #94: Email delivery tracking

        Args:
            db: Database session
            to_email: Recipient email
            subject: Email subject
            body_text: Text body
            body_html: HTML body
            template: Template key
            status: Delivery status
            error_message: Error message if failed
            celery_task_id: Celery task ID if queued
        """
        from app.models.email_log import EmailLog, EmailStatus

        # Convert string status to enum
        if isinstance(status, str):
            status_enum = EmailStatus(status)
        else:
            status_enum = status

        email_log: EmailLog = EmailLog(
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            template=template,
            status=status_enum,
            error_message=error_message,
            celery_task_id=celery_task_id,
        )

        db.add(email_log)
        await db.commit()


def send_review_reminder_email(
    to_email: str,
    page_slugs: list[str],
    page_titles: list[dict[str, str]],
    due_dates: list[datetime],
) -> bool:
    """
    Send annual review reminder email for transparency pages.

    Args:
        to_email: Admin email address
        page_slugs: List of page slugs due for review
        page_titles: List of page title dicts (multilingual)
        due_dates: List of next_review_due dates

    Returns:
        True if email was sent successfully, False otherwise
    """
    if not page_slugs:
        return True  # Nothing to send

    email_service = EmailService()

    # Build the email content
    subject = f"[AnsCheckt] Annual Review Due: {len(page_slugs)} Transparency Page(s)"

    # Build pages list HTML
    pages_html = ""
    for i, (slug, title, due_date) in enumerate(zip(page_slugs, page_titles, due_dates)):
        en_title = title.get("en", slug)
        is_overdue = due_date < datetime.now(due_date.tzinfo)
        status = (
            '<span style="color: red; font-weight: bold;">(OVERDUE)</span>' if is_overdue else ""
        )
        due_str = due_date.strftime("%Y-%m-%d")
        pages_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{i + 1}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{en_title}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><code>{slug}</code></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{due_str} {status}</td>
        </tr>
        """

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Annual Review Reminder</h2>

        <p>The following transparency pages are due for their annual review
        as required by EFCSN compliance standards:</p>

        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th style="padding: 8px; border: 1px solid #ddd;">#</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Page Title</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Slug</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Review Due</th>
                </tr>
            </thead>
            <tbody>
                {pages_html}
            </tbody>
        </table>

        <p><strong>Action Required:</strong> Please review and update these pages
        to ensure continued EFCSN compliance.</p>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="color: #666; font-size: 12px;">
            This is an automated message from AnsCheckt.
            Do not reply to this email.
        </p>
    </body>
    </html>
    """

    return email_service.send_email(to_email, subject, body_html)


# Singleton instance
email_service = EmailService()
