"""
Correction API Endpoints for EFCSN-compliant corrections system.

Issue #76: Backend: Correction Request Service (TDD)
Issue #77: Backend: Correction Application Logic (TDD)
Issue #78: Backend: Correction API Endpoints (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /corrections - Submit correction request (public, no auth)
- GET /corrections - List all corrections (admin only) [Issue #78]
- GET /corrections/pending - List pending corrections (admin only)
- GET /corrections/public-log - Public corrections log (no auth) [Issue #78]
- GET /corrections/fact-check/{fact_check_id} - Get corrections for fact-check
- GET /corrections/{id} - Get correction by ID
- POST /corrections/{id}/accept - Accept a correction (admin only)
- POST /corrections/{id}/reject - Reject a correction (admin only)
- POST /corrections/{id}/apply - Apply an accepted correction (admin only)
- GET /corrections/history/{fact_check_id} - Get correction history for fact-check

NOTE: Static routes (like /pending, /public-log) MUST be defined BEFORE parameterized
routes (like /{correction_id}) to prevent FastAPI from treating path segments as UUIDs.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.correction import CorrectionStatus, CorrectionType
from app.models.user import User
from app.schemas.correction import (
    CorrectionAllListResponse,
    CorrectionApplicationResponse,
    CorrectionApplyRequest,
    CorrectionCreate,
    CorrectionHistoryResponse,
    CorrectionListResponse,
    CorrectionPendingListResponse,
    CorrectionResponse,
    CorrectionReviewRequest,
    CorrectionSubmitResponse,
    PublicLogCorrectionResponse,
    PublicLogListResponse,
)
from app.services.correction_application_service import (
    CorrectionAlreadyAppliedError,
    CorrectionAlreadyReviewedError,
    CorrectionApplicationService,
    CorrectionNotAcceptedError,
)
from app.services.correction_application_service import (
    CorrectionNotFoundError as ApplicationCorrectionNotFoundError,
)
from app.services.correction_application_service import (
    ValidationError as ApplicationValidationError,
)
from app.services.correction_service import (
    CorrectionService,
    FactCheckNotFoundError,
)

router = APIRouter()


# =============================================================================
# Public Endpoints (No Authentication Required)
# =============================================================================


@router.post(
    "/corrections",
    response_model=CorrectionSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["corrections"],
    summary="Submit correction request",
    description="Submit a public correction request for a fact-check. "
    "No authentication required. Email is optional for receiving updates.",
)
async def submit_correction(
    correction_data: CorrectionCreate,
    db: AsyncSession = Depends(get_db),
) -> CorrectionSubmitResponse:
    """
    Submit a correction request for a published fact-check.

    This is a PUBLIC endpoint - no authentication required.

    The correction will be reviewed by the editorial team within
    7 days (SLA deadline per EFCSN requirements).

    If an email is provided, an acknowledgment will be sent.
    """
    service = CorrectionService(db)

    try:
        correction = await service.submit_request(
            fact_check_id=correction_data.fact_check_id,
            correction_type=correction_data.correction_type,
            request_details=correction_data.request_details,
            requester_email=correction_data.requester_email,
        )

        # Determine if acknowledgment was sent (only if email provided)
        acknowledgment_sent: bool = correction_data.requester_email is not None

        return CorrectionSubmitResponse(
            id=correction.id,
            fact_check_id=correction.fact_check_id,
            correction_type=correction.correction_type,
            status=correction.status,
            requester_email=correction.requester_email,
            sla_deadline=correction.sla_deadline,
            acknowledgment_sent=acknowledgment_sent,
            created_at=correction.created_at,
        )

    except FactCheckNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# =============================================================================
# Admin Endpoints (Authentication Required)
# NOTE: These MUST come BEFORE parameterized routes like /{correction_id}
# =============================================================================


@router.get(
    "/corrections/pending",
    response_model=CorrectionPendingListResponse,
    tags=["corrections"],
    summary="List pending corrections",
    description="List all pending correction requests for triage. Admin only.",
)
async def list_pending_corrections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CorrectionPendingListResponse:
    """
    List all pending corrections for admin triage.

    Returns corrections prioritized by type (substantial first)
    and age (older first).

    Requires admin or super_admin role.
    """
    service = CorrectionService(db)

    # Get prioritized pending corrections
    pending = await service.get_prioritized_pending_corrections()

    # Count overdue corrections
    overdue = await service.get_overdue_corrections()
    overdue_count: int = len(overdue)

    return CorrectionPendingListResponse(
        corrections=[CorrectionResponse.model_validate(c) for c in pending],
        total_count=len(pending),
        overdue_count=overdue_count,
    )


# =============================================================================
# Issue #78: GET /api/v1/corrections (Admin - List All Corrections)
# =============================================================================


@router.get(
    "/corrections",
    response_model=CorrectionAllListResponse,
    tags=["corrections"],
    summary="List all corrections",
    description="List all corrections with optional filtering by status and type. "
    "Admin only. Supports pagination.",
)
async def list_all_corrections(
    status: Optional[CorrectionStatus] = Query(
        None,
        description="Filter by correction status (pending, accepted, rejected)",
    ),
    correction_type: Optional[CorrectionType] = Query(
        None,
        description="Filter by correction type (minor, update, substantial)",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of corrections to return (1-100)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of corrections to skip for pagination",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CorrectionAllListResponse:
    """
    List all corrections with optional filtering and pagination.

    This is an ADMIN-ONLY endpoint for viewing the complete corrections
    list, including all statuses (pending, accepted, rejected).

    Query Parameters:
    - status: Filter by correction status
    - correction_type: Filter by correction type
    - limit: Maximum results per page (default 50, max 100)
    - offset: Number of results to skip

    Requires admin or super_admin role.
    """
    service = CorrectionService(db)

    corrections, total_count = await service.list_all_corrections(
        status=status,
        correction_type=correction_type,
        limit=limit,
        offset=offset,
    )

    return CorrectionAllListResponse(
        corrections=[CorrectionResponse.model_validate(c) for c in corrections],
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


# =============================================================================
# Issue #78: GET /api/v1/corrections/public-log (Public Corrections Log)
# =============================================================================


@router.get(
    "/corrections/public-log",
    response_model=PublicLogListResponse,
    tags=["corrections"],
    summary="Get public corrections log",
    description="Get the public corrections log showing all accepted substantial "
    "and update corrections. EFCSN transparency requirement. No auth required.",
)
async def get_public_corrections_log(
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum number of corrections to return (1-500)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of corrections to skip for pagination",
    ),
    db: AsyncSession = Depends(get_db),
) -> PublicLogListResponse:
    """
    Get the public corrections log for EFCSN transparency.

    This is a PUBLIC endpoint - no authentication required.

    Returns only ACCEPTED corrections of type SUBSTANTIAL or UPDATE.
    MINOR corrections are excluded as they don't require public notice
    per EFCSN standards.

    Privacy Protection:
    - Requester email addresses are NOT included in the response
    - Only correction details and resolution notes are shown

    Ordered by reviewed_at date (newest first).
    """
    service = CorrectionService(db)

    corrections, total_count = await service.get_public_log(
        limit=limit,
        offset=offset,
    )

    # Convert to privacy-aware response (no requester_email)
    public_corrections: list[PublicLogCorrectionResponse] = [
        PublicLogCorrectionResponse(
            id=c.id,
            fact_check_id=c.fact_check_id,
            correction_type=c.correction_type,
            request_details=c.request_details,
            status=c.status,
            reviewed_at=c.reviewed_at,
            resolution_notes=c.resolution_notes,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in corrections
    ]

    return PublicLogListResponse(
        corrections=public_corrections,
        total_count=total_count,
    )


# =============================================================================
# Static Path Endpoints (Must come before parameterized routes)
# =============================================================================


@router.get(
    "/corrections/fact-check/{fact_check_id}",
    response_model=CorrectionListResponse,
    tags=["corrections"],
    summary="Get corrections for fact-check",
    description="Retrieve all correction requests for a specific fact-check.",
)
async def get_corrections_for_fact_check(
    fact_check_id: UUID,
    correction_type: Optional[CorrectionType] = Query(
        None,
        description="Filter by correction type (minor, update, substantial)",
    ),
    db: AsyncSession = Depends(get_db),
) -> CorrectionListResponse:
    """
    Get all corrections for a fact-check.

    Optionally filter by correction_type.
    This is a PUBLIC endpoint - no authentication required.
    """
    service = CorrectionService(db)
    corrections = await service.get_corrections_for_fact_check(
        fact_check_id=fact_check_id,
        correction_type=correction_type,
    )

    return CorrectionListResponse(
        fact_check_id=fact_check_id,
        corrections=[CorrectionResponse.model_validate(c) for c in corrections],
        total_count=len(corrections),
    )


@router.get(
    "/corrections/history/{fact_check_id}",
    response_model=CorrectionHistoryResponse,
    tags=["corrections"],
    summary="Get correction history for fact-check",
    description="Retrieve the full correction application history for a fact-check. "
    "Shows all versions and changes made over time.",
)
async def get_correction_history(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CorrectionHistoryResponse:
    """
    Get correction application history for a fact-check.

    Returns all CorrectionApplication records in version order,
    showing the complete audit trail of changes.

    This is a PUBLIC endpoint - no authentication required.
    """
    service = CorrectionApplicationService(db)
    history = await service.get_correction_history(fact_check_id=fact_check_id)

    return CorrectionHistoryResponse(
        fact_check_id=fact_check_id,
        applications=[CorrectionApplicationResponse.model_validate(app) for app in history],
        total_versions=len(history),
    )


# =============================================================================
# Parameterized Endpoints (Must come LAST to avoid matching static paths)
# =============================================================================


@router.get(
    "/corrections/{correction_id}",
    response_model=CorrectionResponse,
    tags=["corrections"],
    summary="Get correction by ID",
    description="Retrieve a correction request by its ID. Public endpoint.",
)
async def get_correction(
    correction_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CorrectionResponse:
    """
    Get a correction request by ID.

    This is a PUBLIC endpoint - no authentication required.
    """
    service = CorrectionService(db)
    correction = await service.get_correction_by_id(correction_id)

    if correction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correction {correction_id} not found",
        )

    return CorrectionResponse.model_validate(correction)


# =============================================================================
# Issue #77: Correction Review and Application Endpoints (Admin Only)
# =============================================================================


@router.post(
    "/corrections/{correction_id}/accept",
    response_model=CorrectionResponse,
    tags=["corrections"],
    summary="Accept a correction request",
    description="Accept a pending correction request. Admin only. "
    "This marks the correction as accepted and ready to be applied.",
)
async def accept_correction(
    correction_id: UUID,
    review_data: CorrectionReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CorrectionResponse:
    """
    Accept a correction request.

    Updates the correction status to ACCEPTED with resolution notes.
    The correction can then be applied using the /apply endpoint.

    Requires admin or super_admin role.
    """
    service = CorrectionApplicationService(db)

    try:
        correction = await service.accept_correction(
            correction_id=correction_id,
            reviewer_id=current_user.id,
            resolution_notes=review_data.resolution_notes,
        )
        return CorrectionResponse.model_validate(correction)

    except ApplicationCorrectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except CorrectionAlreadyReviewedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except ApplicationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/corrections/{correction_id}/reject",
    response_model=CorrectionResponse,
    tags=["corrections"],
    summary="Reject a correction request",
    description="Reject a pending correction request. Admin only. "
    "Sends rejection email to requester if email was provided.",
)
async def reject_correction(
    correction_id: UUID,
    review_data: CorrectionReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CorrectionResponse:
    """
    Reject a correction request.

    Updates the correction status to REJECTED with resolution notes.
    Sends a rejection email to the requester if they provided an email.

    Requires admin or super_admin role.
    """
    service = CorrectionApplicationService(db)

    try:
        correction = await service.reject_correction(
            correction_id=correction_id,
            reviewer_id=current_user.id,
            resolution_notes=review_data.resolution_notes,
        )
        return CorrectionResponse.model_validate(correction)

    except ApplicationCorrectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except CorrectionAlreadyReviewedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except ApplicationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/corrections/{correction_id}/apply",
    response_model=CorrectionApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["corrections"],
    summary="Apply an accepted correction",
    description="Apply an accepted correction to its fact-check. Admin only. "
    "Creates a versioned record and updates the fact-check content.",
)
async def apply_correction(
    correction_id: UUID,
    apply_data: CorrectionApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CorrectionApplicationResponse:
    """
    Apply an accepted correction to a fact-check.

    Creates a CorrectionApplication record with version tracking,
    preserves the previous state for audit trail, and updates the
    fact-check with the specified changes.

    Correction type handling:
    - MINOR: No public notice required
    - UPDATE: Appends explanatory note
    - SUBSTANTIAL: Adds prominent correction notice

    Requires admin or super_admin role.
    """
    service = CorrectionApplicationService(db)

    try:
        application = await service.apply_correction(
            correction_id=correction_id,
            applied_by_id=current_user.id,
            changes=apply_data.changes,
            changes_summary=apply_data.changes_summary,
        )
        return CorrectionApplicationResponse.model_validate(application)

    except ApplicationCorrectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except CorrectionNotAcceptedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except CorrectionAlreadyAppliedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except ApplicationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
