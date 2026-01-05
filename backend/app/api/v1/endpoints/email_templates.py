"""
Email template management API endpoints

Issue #95: Email Templates (Multilingual EN/NL)
Provides CRUD operations for admin template management
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.email_template import EmailTemplateType
from app.models.user import User
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateRenderRequest,
    EmailTemplateRenderResponse,
    EmailTemplateResponse,
    EmailTemplateUpdate,
)
from app.services.email_template_service import EmailTemplateService

router = APIRouter()


@router.get("/", response_model=List[EmailTemplateResponse])
async def list_templates(
    *,
    db: AsyncSession = Depends(get_db),
    include_inactive: bool = False,
    template_type: EmailTemplateType | None = None,
    current_user: User = Depends(require_admin),
) -> Any:
    """
    List all email templates (admin only)

    Args:
        include_inactive: Include inactive templates
        template_type: Filter by template type
    """
    service = EmailTemplateService()
    templates = await service.list_templates(db, include_inactive, template_type)
    return templates


@router.get("/{template_key}", response_model=EmailTemplateResponse)
async def get_template(
    *,
    db: AsyncSession = Depends(get_db),
    template_key: str,
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get email template by key (admin only)
    """
    service = EmailTemplateService()
    template = await service.get_template(db, template_key, include_inactive=True)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found",
        )

    return template


@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    *,
    db: AsyncSession = Depends(get_db),
    template_in: EmailTemplateCreate,
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Create new email template (admin only)
    """
    service = EmailTemplateService()

    try:
        template = await service.create_template(
            db,
            template_key=template_in.template_key,
            template_type=template_in.template_type,
            name=template_in.name,
            description=template_in.description,
            subject=template_in.subject,
            body_text=template_in.body_text,
            body_html=template_in.body_html,
            variables=template_in.variables,
            is_active=template_in.is_active,
            last_modified_by=template_in.last_modified_by or current_user.email,
            notes=template_in.notes,
        )
        return template

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.patch("/{template_key}", response_model=EmailTemplateResponse)
async def update_template(
    *,
    db: AsyncSession = Depends(get_db),
    template_key: str,
    template_in: EmailTemplateUpdate,
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Update email template (admin only)
    """
    service = EmailTemplateService()

    try:
        template = await service.update_template(
            db,
            template_key,
            name=template_in.name,
            description=template_in.description,
            subject=template_in.subject,
            body_text=template_in.body_text,
            body_html=template_in.body_html,
            variables=template_in.variables,
            is_active=template_in.is_active,
            last_modified_by=template_in.last_modified_by or current_user.email,
            notes=template_in.notes,
        )
        return template

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{template_key}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_template(
    *,
    db: AsyncSession = Depends(get_db),
    template_key: str,
    current_user: User = Depends(require_admin),
) -> None:
    """
    Deactivate email template (admin only)

    Note: Templates are not deleted, only deactivated for audit trail
    """
    service = EmailTemplateService()

    try:
        await service.deactivate_template(db, template_key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/render", response_model=EmailTemplateRenderResponse)
async def render_template(
    *,
    db: AsyncSession = Depends(get_db),
    render_request: EmailTemplateRenderRequest,
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Preview rendered template with test data (admin only)

    Useful for testing templates before sending
    """
    service = EmailTemplateService()

    try:
        subject, body_text, body_html = await service.render_template(
            db,
            render_request.template_key,
            render_request.context,
            render_request.language,
        )

        return EmailTemplateRenderResponse(
            subject=subject, body_text=body_text, body_html=body_html
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
