"""
Service layer for submission operations
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.submission import SubmissionCreate, SubmissionListResponse, SubmissionResponse
from app.services import claim_service


async def create_submission(
    db: AsyncSession, data: SubmissionCreate, user_id: Optional[UUID] = None
) -> Submission:
    """
    Create a new submission with claim extraction

    Args:
        db: Database session
        data: Submission creation data
        user_id: Optional authenticated user ID

    Returns:
        Created submission with extracted claims
    """
    # If no user_id provided, use default for backward compatibility
    if user_id is None:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            # Create a default user for testing
            from app.models.user import UserRole

            user = User(email="default@example.com", password_hash="hash", role=UserRole.SUBMITTER)
            db.add(user)
            await db.flush()
        user_id = user.id

    # Create submission with status "processing" (will extract claims)
    submission = Submission(
        user_id=user_id,
        content=data.content,
        submission_type=data.type,
        status="processing",
    )
    db.add(submission)
    await db.flush()  # Flush to get ID

    # Extract claims from content
    extracted_claims = await claim_service.extract_claims_from_text(data.content)

    # Create claim objects
    claims = []
    for claim_data in extracted_claims:
        claim = await claim_service.create_claim(
            db=db,
            content=claim_data["content"],
            source=f"submission:{submission.id}",
            confidence=claim_data.get("confidence", 0.90),
        )
        claims.append(claim)

    # Link claims to submission using association table insert
    from app.models.base import submission_claims
    from sqlalchemy import insert

    if claims:
        values = [
            {"submission_id": submission.id, "claim_id": claim.id} for claim in claims
        ]
        await db.execute(insert(submission_claims).values(values))

    await db.commit()

    # Manually refresh with claims loaded
    await db.refresh(submission)
    # Load claims eagerly
    from sqlalchemy import select
    from app.models.claim import Claim

    stmt = (
        select(Claim)
        .join(submission_claims)
        .where(submission_claims.c.submission_id == submission.id)
    )
    result = await db.execute(stmt)
    submission.claims = list(result.scalars().all())

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
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    user_id: Optional[UUID] = None,
    user_role: Optional[UserRole] = None,
    assigned_to_me: Optional[bool] = None,
    status: Optional[str] = None,
) -> SubmissionListResponse:
    """
    List submissions with pagination and role-based filtering

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        user_id: Optional user ID for filtering (submitters see only their own)
        user_role: Optional user role for access control
        assigned_to_me: Optional filter for reviewers to see only assigned submissions
        status: Optional filter by submission status

    Returns:
        Paginated list of submissions
    """
    from app.models.submission_reviewer import SubmissionReviewer
    from sqlalchemy.orm import selectinload

    # Calculate offset
    offset = (page - 1) * page_size

    # Build base query with eager loading of reviewer assignments
    stmt = select(Submission).options(selectinload(Submission.reviewer_assignments))

    # Apply role-based filtering
    if user_role == UserRole.SUBMITTER and user_id:
        # Submitters only see their own submissions
        stmt = stmt.where(Submission.user_id == user_id)
    # REVIEWER, ADMIN, SUPER_ADMIN see all submissions (no filter by default)

    # Apply assigned_to_me filter for REVIEWERS only
    # Admins and super_admins ignore this filter (they always see all)
    if assigned_to_me is True and user_role == UserRole.REVIEWER and user_id:
        # Join with submission_reviewers to filter by assignment
        stmt = stmt.join(SubmissionReviewer).where(SubmissionReviewer.reviewer_id == user_id)

    # Apply status filter if provided
    if status:
        stmt = stmt.where(Submission.status == status)

    # Get total count with filters
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Get submissions with pagination
    stmt = stmt.order_by(Submission.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    submissions = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # Build response items with reviewer info and is_assigned_to_me flag
    items = []
    for submission in submissions:
        # Build reviewer list from reviewer_assignments
        reviewers = []
        is_assigned = False
        for assignment in submission.reviewer_assignments:
            reviewer_info = {
                "id": assignment.reviewer.id,
                "email": assignment.reviewer.email,
                "role": assignment.reviewer.role.value,
            }
            reviewers.append(reviewer_info)
            # Check if current user is assigned
            if user_id and assignment.reviewer_id == user_id:
                is_assigned = True

        # Create response dict
        submission_dict = {
            "id": submission.id,
            "user_id": submission.user_id,
            "content": submission.content,
            "submission_type": submission.submission_type,
            "status": submission.status,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
            "reviewers": reviewers,
            "is_assigned_to_me": is_assigned,
        }
        items.append(SubmissionResponse(**submission_dict))

    return SubmissionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
