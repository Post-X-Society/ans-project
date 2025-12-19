"""
Reviewer assignment endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, get_db
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole
from app.schemas.reviewer_assignment import (
    ReviewerAssignmentCreate,
    ReviewerAssignmentResponse,
    ReviewerInfo,
    ReviewerRemoveResponse,
)

router = APIRouter()


def _user_has_permission(user: User, action: str) -> bool:
    """Check if user has permission for reviewer assignment actions"""
    # Only admins and super_admins can assign/remove reviewers
    if action in ["assign", "remove"]:
        return user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    # Admins, reviewers, and the submission owner can view reviewers
    elif action == "view":
        return user.role in [
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
            UserRole.REVIEWER,
            UserRole.SUBMITTER,
        ]
    return False


async def _get_submission_or_404(db: AsyncSession, submission_id: UUID) -> Submission:
    """Get submission by ID or raise 404"""
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.reviewer_assignments))
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Submission {submission_id} not found"
        )
    return submission


async def _get_user_or_404(db: AsyncSession, user_id: UUID) -> User:
    """Get user by ID or raise 404"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )
    return user


def _format_reviewer_info(assignment: SubmissionReviewer) -> ReviewerInfo:
    """Format reviewer assignment into ReviewerInfo"""
    # Get full_name from volunteer profile if available
    full_name = None
    if assignment.reviewer.volunteer:
        full_name = assignment.reviewer.volunteer.full_name

    return ReviewerInfo(
        id=assignment.reviewer.id,
        email=assignment.reviewer.email,
        role=assignment.reviewer.role.value,  # Convert enum to string
        full_name=full_name,
        assigned_at=assignment.created_at,
    )


@router.post("/{submission_id}/reviewers", response_model=ReviewerAssignmentResponse)
async def assign_reviewers(
    submission_id: UUID,
    assignment_data: ReviewerAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign one or more reviewers to a submission (Admin/Super Admin only)
    """
    # Check permissions
    if not _user_has_permission(current_user, "assign"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to assign reviewers",
        )

    # Get submission
    submission = await _get_submission_or_404(db, submission_id)

    # Get existing reviewer IDs from database (fresh query)
    result = await db.execute(
        select(SubmissionReviewer.reviewer_id).where(
            SubmissionReviewer.submission_id == submission_id
        )
    )
    existing_reviewer_ids = {row[0] for row in result.all()}

    # Validate all reviewer IDs and check their roles
    reviewers_to_assign = []
    for reviewer_id in assignment_data.reviewer_ids:
        # Check if already assigned
        if reviewer_id in existing_reviewer_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Reviewer {reviewer_id} is already assigned to this submission",
            )

        # Get user and validate
        user = await _get_user_or_404(db, reviewer_id)

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is inactive and cannot be assigned as reviewer",
            )

        # Check if user has reviewer role (ONLY reviewer, not admin/super_admin)
        if user.role != UserRole.REVIEWER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"User does not have reviewer role"
            )

        reviewers_to_assign.append(user)

    # Create assignments
    for reviewer in reviewers_to_assign:
        assignment = SubmissionReviewer(
            submission_id=submission_id, reviewer_id=reviewer.id, assigned_by_id=current_user.id
        )
        db.add(assignment)

    await db.commit()

    # Reload submission with updated assignments
    await db.refresh(submission)
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.reviewer_assignments).selectinload(SubmissionReviewer.reviewer)
        )
    )
    submission = result.scalar_one()

    # Format response
    reviewers = [
        _format_reviewer_info(assignment) for assignment in submission.reviewer_assignments
    ]

    return ReviewerAssignmentResponse(id=submission.id, reviewers=reviewers)


@router.delete("/{submission_id}/reviewers/{reviewer_id}", response_model=ReviewerRemoveResponse)
async def remove_reviewer(
    submission_id: UUID,
    reviewer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a reviewer from a submission (Admin/Super Admin only)
    """
    # Check permissions
    if not _user_has_permission(current_user, "remove"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove reviewers",
        )

    # Get submission
    submission = await _get_submission_or_404(db, submission_id)

    # Find the assignment
    result = await db.execute(
        select(SubmissionReviewer)
        .where(
            SubmissionReviewer.submission_id == submission_id,
            SubmissionReviewer.reviewer_id == reviewer_id,
        )
        .options(selectinload(SubmissionReviewer.reviewer))
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Reviewer assignment not found"
        )

    # Delete the assignment
    await db.delete(assignment)
    await db.commit()

    # Get remaining reviewers
    result = await db.execute(
        select(SubmissionReviewer)
        .where(SubmissionReviewer.submission_id == submission_id)
        .options(selectinload(SubmissionReviewer.reviewer))
    )
    remaining_assignments = result.scalars().all()
    remaining_reviewers = [
        _format_reviewer_info(assignment) for assignment in remaining_assignments
    ]

    return ReviewerRemoveResponse(
        message="Reviewer removed successfully",
        submission_id=submission_id,
        reviewer_id=reviewer_id,
        remaining_reviewers=remaining_reviewers,
    )


@router.get("/{submission_id}/reviewers", response_model=list[ReviewerInfo])
async def get_reviewers(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of reviewers assigned to a submission

    - Admins/Super Admins: Can view any submission
    - Reviewers: Can view only if they are assigned to the submission
    - Submitters: Can only view their own submissions
    """
    # Get submission
    submission = await _get_submission_or_404(db, submission_id)

    # Permission logic based on role
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    is_owner = submission.user_id == current_user.id

    # Check if user is assigned as reviewer
    is_assigned_reviewer = False
    if current_user.role == UserRole.REVIEWER:
        result = await db.execute(
            select(SubmissionReviewer).where(
                SubmissionReviewer.submission_id == submission_id,
                SubmissionReviewer.reviewer_id == current_user.id,
            )
        )
        is_assigned_reviewer = result.scalar_one_or_none() is not None

    # Check permissions
    if not (is_admin or is_owner or is_assigned_reviewer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view reviewer assignments",
        )

    # Get all assignments with reviewer info
    result = await db.execute(
        select(SubmissionReviewer)
        .where(SubmissionReviewer.submission_id == submission_id)
        .options(selectinload(SubmissionReviewer.reviewer))
    )
    assignments = result.scalars().all()

    # Format and return list of reviewers
    reviewers = [_format_reviewer_info(assignment) for assignment in assignments]
    return reviewers
