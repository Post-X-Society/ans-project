"""
Service layer for submission operations
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionListResponse, SubmissionResponse


async def create_submission(db: AsyncSession, data: SubmissionCreate) -> Submission:
    """
    Create a new submission

    Args:
        db: Database session
        data: Submission creation data

    Returns:
        Created submission
    """
    # For now, create a test user if none exists (auth will be added later)
    # In production, this will come from the authenticated user
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        # Create a default user for testing
        user = User(email="default@example.com", password_hash="hash", role="user")
        db.add(user)
        await db.flush()

    submission = Submission(
        user_id=user.id,
        content=data.content,
        submission_type=data.type,
        status="pending",
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_submission(db: AsyncSession, submission_id: UUID) -> Optional[Submission]:
    """
    Get a submission by ID

    Args:
        db: Database session
        submission_id: Submission UUID

    Returns:
        Submission if found, None otherwise
    """
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    return result.scalar_one_or_none()


async def list_submissions(
    db: AsyncSession, page: int = 1, page_size: int = 50
) -> SubmissionListResponse:
    """
    List submissions with pagination

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of submissions
    """
    # Calculate offset
    offset = (page - 1) * page_size

    # Get total count
    count_result = await db.execute(select(func.count()).select_from(Submission))
    total = count_result.scalar_one()

    # Get submissions
    result = await db.execute(
        select(Submission).order_by(Submission.created_at.desc()).offset(offset).limit(page_size)
    )
    submissions = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return SubmissionListResponse(
        items=[SubmissionResponse.model_validate(s) for s in submissions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
