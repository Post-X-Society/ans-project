"""
Pydantic schemas for email template API

Issue #95: Email Templates (Multilingual EN/NL)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.email_template import EmailTemplateType


class EmailTemplateBase(BaseModel):
    """Base schema for email template"""

    template_key: str = Field(..., min_length=1, max_length=100)
    template_type: EmailTemplateType
    name: dict[str, str] = Field(..., description="Multilingual template name")
    description: dict[str, str] = Field(..., description="Multilingual description")
    subject: dict[str, str] = Field(..., description="Multilingual subject line")
    body_text: dict[str, str] = Field(..., description="Multilingual plain text body")
    body_html: dict[str, str] = Field(..., description="Multilingual HTML body")
    variables: dict[str, str] = Field(..., description="Available template variables")
    is_active: bool = True
    notes: Optional[str] = None


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating a new email template"""

    last_modified_by: Optional[str] = None


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template"""

    name: Optional[dict[str, str]] = None
    description: Optional[dict[str, str]] = None
    subject: Optional[dict[str, str]] = None
    body_text: Optional[dict[str, str]] = None
    body_html: Optional[dict[str, str]] = None
    variables: Optional[dict[str, str]] = None
    is_active: Optional[bool] = None
    last_modified_by: Optional[str] = None
    notes: Optional[str] = None


class EmailTemplateResponse(EmailTemplateBase):
    """Schema for email template response"""

    id: UUID
    version: int
    last_modified_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateRenderRequest(BaseModel):
    """Schema for rendering a template"""

    template_key: str
    context: dict[str, str]
    language: str = Field("en", pattern="^(en|nl)$")


class EmailTemplateRenderResponse(BaseModel):
    """Schema for rendered template response"""

    subject: str
    body_text: str
    body_html: str
