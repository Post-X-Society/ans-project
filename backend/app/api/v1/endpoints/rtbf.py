"""
Right to be Forgotten (RTBF) API endpoints

Issue #92: Backend: Right to be Forgotten Workflow (TDD)
Part of EPIC #53: GDPR & Data Retention Compliance

Implements:
- POST /api/v1/rtbf/requests - Create RTBF request
- GET /api/v1/rtbf/requests/me - Get current user's requests
- GET /api/v1/rtbf/requests - List all requests (admin only)
- POST /api/v1/rtbf/requests/{id}/process - Process request (admin only)
- POST /api/v1/rtbf/requests/{id}/reject - Reject request (admin only)
- GET /api/v1/rtbf/export - Export user data (GDPR Article 20)
- GET /api/v1/rtbf/summary - Get data summary for deletion preview
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.rtbf_request import RTBFRequestStatus
from app.models.user import User
from app.schemas.rtbf import (
    DataExportResponse,
    RTBFRequestCreate,
    RTBFRequestListResponse,
    RTBFRequestProcessResult,
    RTBFRequestRejectInput,
    RTBFRequestResponse,
    UserDataSummary,
)
from app.services.rtbf_service import RTBFService

router = APIRouter(prefix="/rtbf")


@router.post(
    "/requests",
    response_model=RTBFRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create RTBF Request",
    description="Submit a Right to be Forgotten request to delete personal data.",
)
async def create_rtbf_request(
    request_data: RTBFRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RTBFRequestResponse:
    """
    Create a new Right to be Forgotten request.

    This endpoint allows authenticated users to request deletion of their
    personal data in compliance with GDPR Article 17.

    - **reason**: Explanation for why data deletion is requested (required)
    - **date_of_birth**: Optional date of birth for minor detection (auto-approval)
    """
    service: RTBFService = RTBFService(db)
    rtbf_request = await service.create_request(
        user_id=current_user.id,
        reason=request_data.reason,
        date_of_birth=request_data.date_of_birth,
        notification_email=current_user.email,
    )
    return RTBFRequestResponse.model_validate(rtbf_request)


@router.get(
    "/requests/me",
    response_model=list[RTBFRequestResponse],
    summary="Get My RTBF Requests",
    description="Get all RTBF requests submitted by the current user.",
)
async def get_my_rtbf_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RTBFRequestResponse]:
    """
    Get all RTBF requests for the current user.

    Returns a list of all Right to be Forgotten requests submitted by
    the authenticated user, ordered by creation date (newest first).
    """
    service: RTBFService = RTBFService(db)
    requests = await service.get_user_requests(current_user.id)
    return [RTBFRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/requests",
    response_model=RTBFRequestListResponse,
    summary="List All RTBF Requests (Admin)",
    description="List all RTBF requests. Requires admin privileges.",
)
async def list_rtbf_requests(
    status_filter: RTBFRequestStatus | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RTBFRequestListResponse:
    """
    List all RTBF requests (admin only).

    Admin endpoint to view and manage all Right to be Forgotten requests.

    - **status_filter**: Optional filter by request status
    - **limit**: Maximum number of results (default 100)
    - **offset**: Offset for pagination
    """
    service: RTBFService = RTBFService(db)

    requests, total = await service.list_all_requests(
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    # Count by status
    pending_requests = await service.list_pending_requests()
    pending_count: int = len(pending_requests)

    processing_requests, _ = await service.list_all_requests(status=RTBFRequestStatus.PROCESSING)
    processing_count: int = len(processing_requests)

    return RTBFRequestListResponse(
        items=[RTBFRequestResponse.model_validate(r) for r in requests],
        total=total,
        pending_count=pending_count,
        processing_count=processing_count,
    )


@router.get(
    "/requests/{request_id}",
    response_model=RTBFRequestResponse,
    summary="Get RTBF Request",
    description="Get a specific RTBF request by ID.",
)
async def get_rtbf_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RTBFRequestResponse:
    """
    Get a specific RTBF request.

    Users can only view their own requests.
    Admins can view any request.
    """
    service: RTBFService = RTBFService(db)
    rtbf_request = await service.get_request_by_id(request_id)

    if rtbf_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RTBF request {request_id} not found",
        )

    # Check access: user can only see their own, admins can see all
    is_admin: bool = current_user.role.value in ["admin", "super_admin"]
    if rtbf_request.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own RTBF requests",
        )

    return RTBFRequestResponse.model_validate(rtbf_request)


@router.post(
    "/requests/{request_id}/process",
    response_model=RTBFRequestProcessResult,
    summary="Process RTBF Request (Admin)",
    description="Process an RTBF request by deleting/anonymizing user data.",
)
async def process_rtbf_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RTBFRequestProcessResult:
    """
    Process an RTBF request (admin only).

    This endpoint executes the data deletion/anonymization workflow:
    - Unpublished submissions are deleted
    - Published submissions are anonymized (user link removed)
    - User account is anonymized and deactivated

    For minors (age < 18), requests are auto-approved.
    """
    service: RTBFService = RTBFService(db)

    try:
        result: dict[str, Any] = await service.process_request(
            request_id=request_id,
            processed_by_id=admin.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return RTBFRequestProcessResult(**result)


@router.post(
    "/requests/{request_id}/reject",
    response_model=RTBFRequestResponse,
    summary="Reject RTBF Request (Admin)",
    description="Reject an RTBF request with a reason.",
)
async def reject_rtbf_request(
    request_id: UUID,
    rejection_data: RTBFRequestRejectInput,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RTBFRequestResponse:
    """
    Reject an RTBF request (admin only).

    Rejection reasons may include:
    - Legal hold on data
    - Ongoing investigation
    - Public interest exception

    The user will be notified of the rejection with the provided reason.
    """
    service: RTBFService = RTBFService(db)

    try:
        rtbf_request = await service.reject_request(
            request_id=request_id,
            rejection_reason=rejection_data.rejection_reason,
            rejected_by_id=admin.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return RTBFRequestResponse.model_validate(rtbf_request)


@router.get(
    "/export",
    response_model=DataExportResponse,
    summary="Export My Data (GDPR Article 20)",
    description="Export all personal data in a portable format.",
)
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataExportResponse:
    """
    Export user's personal data (GDPR Article 20 - Data Portability).

    Returns all user data in a structured JSON format including:
    - User profile information
    - All submissions
    - Activity history

    This data can be used to transfer to another service.
    """
    service: RTBFService = RTBFService(db)

    try:
        export_data: dict[str, Any] = await service.export_user_data(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return DataExportResponse(**export_data)


@router.get(
    "/summary",
    response_model=UserDataSummary,
    summary="Get My Data Summary",
    description="Get a summary of personal data before deletion.",
)
async def get_my_data_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserDataSummary:
    """
    Get a summary of user's data for deletion preview.

    Shows what data will be deleted or anonymized if an RTBF request
    is processed, including any restrictions or warnings.
    """
    service: RTBFService = RTBFService(db)

    try:
        summary: dict[str, Any] = await service.get_user_data_summary(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return UserDataSummary(**summary)
