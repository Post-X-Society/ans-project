"""
Email service for sending notifications.

Issue #83: Backend: Transparency Page Service with Versioning
ADR 0005: EFCSN Compliance Architecture

Supports:
- Annual review reminder emails for transparency pages
- Async email sending with SMTP
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

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
