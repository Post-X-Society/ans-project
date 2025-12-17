"""
Submissions API endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.submission import SubmissionCreate, SubmissionListResponse, SubmissionResponse
from app.services import submission_service

router = APIRouter()


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new submission",
    description="Submit content for fact-checking. The submission will be queued for processing.",
)
async def create_submission(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    """
    Create a new fact-check submission.

    - **content**: The text, image URL, or link to fact-check (10-5000 characters)
    - **type**: Type of submission (text, image, or url)

    Returns the created submission with status "pending"
    """
    created = await submission_service.create_submission(db, submission)
    return SubmissionResponse.model_validate(created)


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get a submission by ID",
    description="Retrieve a specific submission by its UUID",
)
async def get_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    """
    Get a submission by ID.

    - **submission_id**: UUID of the submission to retrieve

    Returns 404 if submission not found.
    """
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )
    return SubmissionResponse.model_validate(submission)


@router.get(
    "",
    response_model=SubmissionListResponse,
    summary="List submissions",
    description="Get a paginated list of submissions, ordered by creation date (newest first)",
)
async def list_submissions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
) -> SubmissionListResponse:
    """
    List submissions with pagination.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (1-100, default 50)

    Returns a paginated list of submissions ordered by creation date (newest first).
    """
    return await submission_service.list_submissions(db, page, page_size)
