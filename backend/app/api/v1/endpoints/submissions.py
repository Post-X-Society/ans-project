"""
Submissions API endpoints
"""

from typing import Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.spotlight import SpotlightContent
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole
from app.schemas.claim import ClaimResponse
from app.schemas.spotlight import SpotlightContentResponse, SpotlightSubmissionCreate
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionWithClaimsResponse,
)
from app.schemas.user import UserResponse
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
    assigned_to_me: Optional[bool] = Query(
        None, description="Filter by assignments (reviewers only)"
    ),
    status: Optional[str] = Query(None, description="Filter by submission status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionListResponse:
    """
    List submissions with pagination and role-based filtering (requires authentication).

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (1-100, default 50)
    - **assigned_to_me**: Filter to show only submissions assigned to the current reviewer
    - **status**: Filter by submission status (pending, processing, completed, rejected)

    Role-based access:
    - SUBMITTER: Only sees their own submissions
    - REVIEWER: Sees all submissions, or only assigned ones with assigned_to_me=true
    - ADMIN/SUPER_ADMIN: Sees all submissions (assigned_to_me filter ignored)

    Returns a paginated list of submissions ordered by creation date (newest first).
    """
    return await submission_service.list_submissions(
        db=db,
        page=page,
        page_size=page_size,
        user_id=current_user.id,
        user_role=current_user.role,
        assigned_to_me=assigned_to_me,
        status=status,
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
    spotlight_data = await snapchat_service.fetch_spotlight_data(
        spotlight_submission.spotlight_link
    )

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


@router.post(
    "/{submission_id}/reviewers/me",
    status_code=status.HTTP_201_CREATED,
    summary="Self-assign as reviewer",
    description="Assign yourself as a reviewer to a submission (Reviewer/Admin/Super Admin)",
    responses={
        201: {"description": "Successfully assigned as reviewer"},
        200: {"description": "Already assigned as reviewer (idempotent)"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Submission not found"},
    },
)
async def self_assign_as_reviewer(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Union[dict[str, str], Response]:
    """
    Self-assign as a reviewer to a submission (requires Reviewer+ role).

    - **submission_id**: UUID of the submission to assign yourself to

    This endpoint allows reviewers, admins, and super admins to assign themselves
    to a submission without requiring admin intervention.

    Returns:
    - 201 Created: Successfully assigned as reviewer
    - 200 OK: Already assigned (idempotent operation)
    - 403 Forbidden: User lacks required role
    - 404 Not Found: Submission does not exist
    """
    # Check permission: only reviewers, admins, and super admins can self-assign
    if current_user.role not in [UserRole.REVIEWER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only reviewers, admins, and super admins can self-assign.",
        )

    # Verify submission exists
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    # Check if already assigned (for idempotent behavior)
    is_already_assigned = await submission_service.is_reviewer_assigned(
        db=db,
        submission_id=submission_id,
        reviewer_id=current_user.id,
    )

    if is_already_assigned:
        # Return 200 OK for idempotent behavior
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Already assigned as reviewer",
                "submission_id": str(submission_id),
                "reviewer_id": str(current_user.id),
            },
        )

    # Self-assign: assigned_by_id is the same as reviewer_id
    await submission_service.assign_reviewer(
        db=db,
        submission_id=submission_id,
        reviewer_id=current_user.id,
        assigned_by_id=current_user.id,
    )

    return {
        "message": "Successfully assigned as reviewer",
        "submission_id": str(submission_id),
        "reviewer_id": str(current_user.id),
    }


@router.post(
    "/{submission_id}/reviewers/{reviewer_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign a reviewer to a submission",
    description="Assign a reviewer to review a submission (Admin/Super Admin only)",
)
async def assign_reviewer_to_submission(
    submission_id: UUID,
    reviewer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    Assign a reviewer to a submission (requires Admin or Super Admin role).

    - **submission_id**: UUID of the submission
    - **reviewer_id**: UUID of the user to assign as reviewer

    Returns success message with assignment details
    """
    # Check permission: only admins and super admins can assign reviewers
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign reviewers",
        )

    # Verify submission exists
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    # Verify reviewer exists and has appropriate role
    reviewer_stmt = select(User).where(User.id == reviewer_id)
    reviewer_result = await db.execute(reviewer_stmt)
    reviewer = reviewer_result.scalar_one_or_none()

    if not reviewer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {reviewer_id} not found",
        )

    if reviewer.role not in [UserRole.REVIEWER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with reviewer role or higher can be assigned",
        )

    # Assign reviewer
    try:
        await submission_service.assign_reviewer(
            db=db,
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            assigned_by_id=current_user.id,
        )
    except Exception as e:
        # Handle duplicate assignment (IntegrityError from unique constraint)
        if "uq_submission_reviewer" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reviewer is already assigned to this submission",
            ) from e
        raise

    return {
        "message": "Reviewer assigned successfully",
        "submission_id": str(submission_id),
        "reviewer_id": str(reviewer_id),
    }


@router.delete(
    "/{submission_id}/reviewers/{reviewer_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a reviewer from a submission",
    description="Remove a reviewer assignment from a submission (Admin/Super Admin only)",
)
async def remove_reviewer_from_submission(
    submission_id: UUID,
    reviewer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    Remove a reviewer from a submission (requires Admin or Super Admin role).

    - **submission_id**: UUID of the submission
    - **reviewer_id**: UUID of the reviewer to remove

    Returns success message
    """
    # Check permission: only admins and super admins can remove reviewers
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove reviewers",
        )

    # Verify submission exists
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    # Remove reviewer
    removed = await submission_service.remove_reviewer(
        db=db, submission_id=submission_id, reviewer_id=reviewer_id
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reviewer assignment not found",
        )

    return {
        "message": "Reviewer removed successfully",
        "submission_id": str(submission_id),
        "reviewer_id": str(reviewer_id),
    }


@router.get(
    "/{submission_id}/reviewers",
    response_model=list[UserResponse],
    summary="Get reviewers assigned to a submission",
    description="Get all reviewers assigned to a specific submission",
)
async def get_submission_reviewers(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserResponse]:
    """
    Get all reviewers assigned to a submission (requires authentication).

    - **submission_id**: UUID of the submission

    Returns list of User objects representing assigned reviewers

    Access control:
    - Submission owner can view their submission's reviewers
    - Assigned reviewers can view the reviewer list
    - ADMIN, SUPER_ADMIN can view any submission's reviewers
    """
    # Verify submission exists
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    # Check permission: owner OR assigned reviewer OR admin/super_admin
    is_owner = submission.user_id == current_user.id
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

    # Check if current user is an assigned reviewer
    is_assigned_reviewer = False
    if current_user.role == UserRole.REVIEWER:
        stmt = select(SubmissionReviewer).where(
            SubmissionReviewer.submission_id == submission_id,
            SubmissionReviewer.reviewer_id == current_user.id,
        )
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        is_assigned_reviewer = assignment is not None

    if not (is_owner or is_assigned_reviewer or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this submission's reviewers",
        )

    reviewers = await submission_service.get_submission_reviewers(db, submission_id)
    return [UserResponse.model_validate(reviewer) for reviewer in reviewers]
