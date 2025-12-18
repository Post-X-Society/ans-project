"""
User management endpoints with role-based access control
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin, require_super_admin
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserRoleUpdate, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.

    Requires:
        - Valid JWT access token

    Returns:
        UserResponse: Current user's information
    """
    return current_user


@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin+ only).

    Requires:
        - Admin or Super Admin role

    Returns:
        List[UserResponse]: List of all users ordered by creation date
    """
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user by ID (self or admin+).

    Users can view their own profile, admins can view any profile.

    Requires:
        - Valid JWT access token
        - Either viewing own profile OR admin/super_admin role

    Args:
        user_id: UUID of the user to retrieve

    Returns:
        UserResponse: User information

    Raises:
        HTTPException: 403 if user tries to view another user's profile without admin rights
        HTTPException: 404 if user not found
    """
    # Users can view their own profile, admins can view any profile
    if user_id != current_user.id and current_user.role not in [
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user role (admin+ with restrictions).

    Permission rules:
    - Admins can modify submitter and reviewer roles only
    - Admins cannot modify other admins or super admins
    - Super admins can modify any role

    Requires:
        - Admin or Super Admin role

    Args:
        user_id: UUID of the user to update
        role_update: New role information

    Returns:
        UserResponse: Updated user information

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 403 if insufficient permissions for the requested change
    """
    # Get target user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Permission checks
    if current_user.role == UserRole.ADMIN:
        # Admins cannot demote other admins or super admins
        if target_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify admin or super admin roles",
            )
        # Admins cannot promote to admin or super admin
        if role_update.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot promote users to admin or super admin",
            )

    # Super admins can change any role
    target_user.role = role_update.role
    await db.commit()
    await db.refresh(target_user)

    return target_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user information (admin+ only).

    Permission rules:
    - Admins can update submitters and reviewers only
    - Admins cannot update other admins or super admins
    - Super admins can update any user

    Requires:
        - Admin or Super Admin role

    Args:
        user_id: UUID of the user to update
        user_update: Fields to update (email, is_active)

    Returns:
        UserResponse: Updated user information

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 403 if insufficient permissions
    """
    # Get target user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Permission checks
    if current_user.role == UserRole.ADMIN:
        # Admins cannot modify other admins or super admins
        if target_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify admin or super admin users",
            )

    # Update fields if provided
    if user_update.email is not None:
        target_user.email = user_update.email
    if user_update.is_active is not None:
        target_user.is_active = user_update.is_active

    await db.commit()
    await db.refresh(target_user)

    return target_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete user (super admin only).

    Requires:
        - Super Admin role

    Args:
        user_id: UUID of the user to delete

    Returns:
        dict: Success message

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if trying to delete own account
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
        )

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}
