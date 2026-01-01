"""
Peer Review API Endpoints for EFCSN-compliant multi-tier approval.

Issue #66: Backend: Peer Review API Endpoints (TDD)
EPIC #48: Multi-Tier Approval & Peer Review
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /peer-review/{fact_check_id}/initiate - Start peer review process
- POST /peer-review/{fact_check_id}/submit - Submit review decision
- GET /peer-review/{fact_check_id}/status - Get review status/consensus
- GET /peer-review/pending - Get current user's pending reviews
- PATCH /peer-review/triggers - Update trigger configuration (admin only)
- GET /peer-review/triggers - List trigger configurations (admin only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin, require_reviewer
from app.models.peer_review import ApprovalStatus, PeerReview
from app.models.peer_review_trigger import PeerReviewTrigger
from app.models.user import User
from app.schemas.peer_review import (
    PeerReviewInitiate,
    PeerReviewInitiateResponse,
    PeerReviewResponse,
    PeerReviewStatusResponse,
    PeerReviewSubmit,
    PendingReviewItem,
    PendingReviewsResponse,
    TriggerListResponse,
    TriggerResponse,
    TriggerUpdate,
)
from app.services.peer_review_service import (
    PeerReviewNotFoundError,
    PeerReviewService,
)

router = APIRouter(prefix="/peer-review", tags=["peer-review"])


# =============================================================================
# Peer Review Initiation
# =============================================================================


@router.post(
    "/{fact_check_id}/initiate",
    response_model=PeerReviewInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate peer review",
    description="Assign reviewers to a fact-check for peer review. Requires admin role.",
)
async def initiate_peer_review(
    fact_check_id: UUID,
    data: PeerReviewInitiate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PeerReviewInitiateResponse:
    """
    Initiate peer review by assigning reviewers to a fact-check.

    Creates pending review records for each specified reviewer.
    Requires admin or super_admin role.
    """
    if not data.reviewer_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one reviewer must be specified",
        )

    service = PeerReviewService(db)

    try:
        reviews = await service.assign_reviewers(
            fact_check_id=fact_check_id,
            reviewer_ids=data.reviewer_ids,
        )
    except PeerReviewNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return PeerReviewInitiateResponse(
        fact_check_id=fact_check_id,
        reviews_created=len(reviews),
        reviews=[PeerReviewResponse.model_validate(r) for r in reviews],
    )


# =============================================================================
# Peer Review Submission
# =============================================================================


@router.post(
    "/{fact_check_id}/submit",
    response_model=PeerReviewResponse,
    summary="Submit peer review decision",
    description="Submit approval or rejection for a fact-check. Requires reviewer role or higher.",
)
async def submit_peer_review(
    fact_check_id: UUID,
    data: PeerReviewSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> PeerReviewResponse:
    """
    Submit a peer review decision for a fact-check.

    The current user must be assigned as a reviewer for this fact-check.
    Requires reviewer, admin, or super_admin role.
    """
    service = PeerReviewService(db)

    try:
        review = await service.submit_peer_review(
            fact_check_id=fact_check_id,
            reviewer_id=current_user.id,
            approved=data.approved,
            comments=data.comments,
        )
    except PeerReviewNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return PeerReviewResponse.model_validate(review)


# =============================================================================
# Peer Review Status
# =============================================================================


@router.get(
    "/{fact_check_id}/status",
    response_model=PeerReviewStatusResponse,
    summary="Get peer review status",
    description="Get the consensus status of peer reviews for a fact-check.",
)
async def get_peer_review_status(
    fact_check_id: UUID,
    min_reviewers: int = Query(
        default=1,
        ge=1,
        le=10,
        description="Minimum number of reviewers required for consensus",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> PeerReviewStatusResponse:
    """
    Get the peer review status and consensus for a fact-check.

    Returns counts of approved, rejected, and pending reviews,
    and whether consensus has been reached.
    """
    service = PeerReviewService(db)

    consensus = await service.check_consensus(
        fact_check_id=fact_check_id,
        min_reviewers=min_reviewers,
    )

    reviews = await service.get_reviews_for_fact_check(fact_check_id)

    return PeerReviewStatusResponse(
        fact_check_id=fact_check_id,
        consensus_reached=consensus.consensus_reached,
        approved=consensus.approved,
        total_reviews=consensus.total_reviews,
        approved_count=consensus.approved_count,
        rejected_count=consensus.rejected_count,
        pending_count=consensus.pending_count,
        needs_more_reviewers=consensus.needs_more_reviewers,
        reviews=[PeerReviewResponse.model_validate(r) for r in reviews],
    )


# =============================================================================
# Pending Reviews
# =============================================================================


@router.get(
    "/pending",
    response_model=PendingReviewsResponse,
    summary="Get pending reviews",
    description="Get the current user's pending peer reviews.",
)
async def get_pending_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> PendingReviewsResponse:
    """
    Get all pending peer reviews assigned to the current user.

    Returns only reviews with PENDING status.
    Requires reviewer, admin, or super_admin role.
    """
    stmt = (
        select(PeerReview)
        .where(PeerReview.reviewer_id == current_user.id)
        .where(PeerReview.approval_status == ApprovalStatus.PENDING)
        .order_by(PeerReview.created_at.desc())
    )

    result = await db.execute(stmt)
    reviews = list(result.scalars().all())

    return PendingReviewsResponse(
        reviewer_id=current_user.id,
        total_count=len(reviews),
        reviews=[PendingReviewItem.model_validate(r) for r in reviews],
    )


# =============================================================================
# Trigger Configuration
# =============================================================================


@router.get(
    "/triggers",
    response_model=TriggerListResponse,
    summary="List peer review triggers",
    description="Get all peer review trigger configurations. Requires admin role.",
)
async def get_triggers(
    enabled_only: bool = Query(
        default=False,
        description="If true, only return enabled triggers",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TriggerListResponse:
    """
    Get all peer review trigger configurations.

    Optionally filter to only enabled triggers.
    Requires admin or super_admin role.
    """
    stmt = select(PeerReviewTrigger)

    if enabled_only:
        stmt = stmt.where(PeerReviewTrigger.enabled.is_(True))

    stmt = stmt.order_by(PeerReviewTrigger.trigger_type)

    result = await db.execute(stmt)
    triggers = list(result.scalars().all())

    return TriggerListResponse(
        total_count=len(triggers),
        triggers=[TriggerResponse.model_validate(t) for t in triggers],
    )


@router.patch(
    "/triggers",
    response_model=TriggerResponse,
    summary="Update peer review trigger",
    description="Update a peer review trigger configuration. Requires admin role.",
)
async def update_trigger(
    data: TriggerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TriggerResponse:
    """
    Update a peer review trigger configuration.

    Only provided fields will be updated.
    Requires admin or super_admin role.
    """
    # Get the trigger
    stmt = select(PeerReviewTrigger).where(PeerReviewTrigger.id == data.trigger_id)
    result = await db.execute(stmt)
    trigger = result.scalar_one_or_none()

    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger {data.trigger_id} not found",
        )

    # Update provided fields
    if data.enabled is not None:
        trigger.enabled = data.enabled

    if data.threshold_value is not None:
        trigger.threshold_value = data.threshold_value

    if data.description is not None:
        trigger.description = data.description

    await db.commit()
    await db.refresh(trigger)

    return TriggerResponse.model_validate(trigger)
