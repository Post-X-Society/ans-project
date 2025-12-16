"""
User schemas for user management endpoints
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole


class UserResponse(BaseModel):
    """Schema for user response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role"""

    role: UserRole
