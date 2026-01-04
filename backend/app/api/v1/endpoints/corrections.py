"""
Correction API Endpoints for EFCSN-compliant corrections system.

Issue #76: Backend: Correction Request Service (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /corrections - Submit correction request (public, no auth)
- GET /corrections/{id} - Get correction by ID
- GET /corrections/fact-check/{fact_check_id} - Get corrections for fact-check
- GET /corrections/pending - List pending corrections (admin only)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.correction import CorrectionType
from app.models.user import User
from app.schemas.correction import (
    CorrectionCreate,
    CorrectionListResponse,
    CorrectionPendingListResponse,
    CorrectionResponse,
    CorrectionSubmitResponse,
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


# =============================================================================
# Admin Endpoints (Authentication Required)
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
