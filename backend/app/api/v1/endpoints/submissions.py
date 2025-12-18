"""
Submissions API endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.submission import Submission
from app.models.spotlight import SpotlightContent
from app.models.user import User, UserRole
from app.schemas.claim import ClaimResponse
from app.schemas.spotlight import SpotlightContentResponse, SpotlightSubmissionCreate
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionWithClaimsResponse,
)
from app.services import submission_service
from app.services.snapchat import snapchat_service

router = APIRouter()


@router.post(
    "",
    response_model=SubmissionWithClaimsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new submission",
    description="Submit content for fact-checking. The submission will be queued for processing.",
)
async def create_submission(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionWithClaimsResponse:
    """
    Create a new fact-check submission (requires authentication).

    - **content**: The text, image URL, or link to fact-check (10-5000 characters)
    - **type**: Type of submission (text, image, or url)

    Returns the created submission with extracted claims
    """
    created = await submission_service.create_submission(db, submission, user_id=current_user.id)

    # Build response with claims
    response_data = SubmissionResponse.model_validate(created)
    return SubmissionWithClaimsResponse(
        **response_data.model_dump(),
        claims=[ClaimResponse.model_validate(claim) for claim in created.claims],
        extracted_claims_count=len(created.claims),
    )


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get a submission by ID",
    description="Retrieve a specific submission by its UUID",
)
async def get_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionResponse:
    """
    Get a submission by ID (requires authentication).

    - **submission_id**: UUID of the submission to retrieve

    Access control:
    - Submission owner can always view their own submissions
    - REVIEWER, ADMIN, SUPER_ADMIN can view any submission
    - Returns 404 if submission not found, 403 if access denied
    """
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    # Check permission: owner OR reviewer/admin/super_admin
    is_owner = submission.user_id == current_user.id
    is_privileged = current_user.role in [
        UserRole.REVIEWER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]

    if not (is_owner or is_privileged):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this submission",
        )

    return SubmissionResponse.model_validate(submission)


@router.get(
    "",
    response_model=SubmissionListResponse,
    summary="List submissions",
    description="Get a paginated list of submissions with role-based filtering",
)
async def list_submissions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionListResponse:
    """
    List submissions with pagination and role-based filtering (requires authentication).

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (1-100, default 50)

    Role-based access:
    - SUBMITTER: Only sees their own submissions
    - REVIEWER/ADMIN/SUPER_ADMIN: Sees all submissions

    Returns a paginated list of submissions ordered by creation date (newest first).
    """
    return await submission_service.list_submissions(
        db=db,
        page=page,
        page_size=page_size,
        user_id=current_user.id,
        user_role=current_user.role,
    )


@router.post(
    "/spotlight",
    response_model=SpotlightContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Snapchat Spotlight content",
    description="Submit a Snapchat Spotlight link for fact-checking. Fetches metadata and downloads video.",
)
async def create_spotlight_submission(
    spotlight_submission: SpotlightSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpotlightContentResponse:
    """
    Create a new Spotlight submission (requires authentication).

    - **spotlight_link**: Full Snapchat Spotlight URL

    This endpoint will:
    1. Fetch metadata from Snapchat API via RapidAPI
    2. Create a submission record
    3. Download the video to local storage
    4. Store all metadata in the database

    Returns the created Spotlight content with all metadata
    """
    # Fetch Spotlight data from API
    spotlight_data = await snapchat_service.fetch_spotlight_data(spotlight_submission.spotlight_link)

    # Parse metadata
    parsed_metadata = snapchat_service.parse_spotlight_metadata(spotlight_data)

    # Create submission record
    submission = Submission(
        user_id=current_user.id,
        content=f"Snapchat Spotlight: {parsed_metadata.get('creator_name', 'Unknown')} - {spotlight_submission.spotlight_link}",
        submission_type="spotlight",
        status="processing",
    )
    db.add(submission)
    await db.flush()  # Get submission ID

    # Download video
    video_local_path = await snapchat_service.download_video(
        parsed_metadata["video_url"], parsed_metadata["spotlight_id"]
    )

    # Create Spotlight content record
    spotlight_content = SpotlightContent(
        submission_id=submission.id,
        spotlight_link=spotlight_submission.spotlight_link,
        spotlight_id=parsed_metadata["spotlight_id"],
        video_url=parsed_metadata["video_url"],
        video_local_path=video_local_path,
        thumbnail_url=parsed_metadata["thumbnail_url"],
        duration_ms=parsed_metadata.get("duration_ms"),
        width=parsed_metadata.get("width"),
        height=parsed_metadata.get("height"),
        creator_username=parsed_metadata.get("creator_username"),
        creator_name=parsed_metadata.get("creator_name"),
        creator_url=parsed_metadata.get("creator_url"),
        view_count=parsed_metadata.get("view_count"),
        share_count=parsed_metadata.get("share_count"),
        comment_count=parsed_metadata.get("comment_count"),
        boost_count=parsed_metadata.get("boost_count"),
        recommend_count=parsed_metadata.get("recommend_count"),
        upload_timestamp=parsed_metadata.get("upload_timestamp"),
        raw_metadata=spotlight_data,
    )
    db.add(spotlight_content)

    # Update submission status
    submission.status = "completed"

    await db.commit()
    await db.refresh(spotlight_content)

    return SpotlightContentResponse.model_validate(spotlight_content)
