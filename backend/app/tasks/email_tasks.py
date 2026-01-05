"""
Celery tasks for email delivery

Handles async email sending with retry logic and delivery tracking
"""

from typing import Optional

from celery import Task  # type: ignore[import-not-found]

from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def send_email_task(
    self: Task,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    template: Optional[str] = None,
) -> bool:
    """
    Celery task to send email asynchronously

    Args:
        self: Celery task instance (bound)
        to_email: Recipient email address
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (optional)
        template: Template key (optional)

    Returns:
        True if sent successfully, False otherwise

    Retry Logic:
        - Max retries: 3
        - Retry delay: 60 seconds
        - Exponential backoff
    """
    from app.services.email_service import email_service

    try:
        # Send email using existing email service
        success: bool = email_service.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html or body_text,
            body_text=body_text,
        )

        if not success:
            # Retry if send failed
            raise self.retry(exc=Exception("Email send failed"))

        return True

    except Exception as exc:
        # Retry on exception
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            # Max retries exceeded, log failure
            return False
