"""
API endpoints for transparency reports.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Provides endpoints for:
- Public: List and view published reports
- Public: Export reports as PDF/CSV
- Admin: Generate, publish, unpublish reports
- Admin: Send email notifications
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.transparency_report import (
    TransparencyReportEmailResult,
    TransparencyReportGenerate,
    TransparencyReportListResponse,
    TransparencyReportResponse,
    TriggerReportGeneration,
    TriggerReportResponse,
)
from app.services.transparency_report_service import TransparencyReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports/transparency", tags=["transparency-reports"])


# ==============================================================================
# PUBLIC ENDPOINTS
# ==============================================================================


@router.get(
    "",
    response_model=TransparencyReportListResponse,
    summary="List published transparency reports",
    description="Returns a list of all published transparency reports (public access).",
)
async def list_published_reports(
    db: AsyncSession = Depends(get_db),
    limit: int = 24,
) -> TransparencyReportListResponse:
    """
    List all published transparency reports.

    This is a public endpoint - no authentication required.
    """
    service: TransparencyReportService = TransparencyReportService(db)
    reports = await service.list_reports(published_only=True, limit=limit)

    return TransparencyReportListResponse(
        reports=[
            {
                "id": r.id,
                "year": r.year,
                "month": r.month,
                "title": r.title,
                "summary": r.summary,
                "is_published": r.is_published,
                "generated_at": r.generated_at,
                "published_at": r.published_at,
                "created_at": r.created_at,
            }
            for r in reports
        ],
        total=len(reports),
    )


@router.get(
    "/{report_id}",
    response_model=TransparencyReportResponse,
    summary="Get a published transparency report",
    description="Returns a specific published transparency report by ID.",
)
async def get_published_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TransparencyReportResponse:
    """
    Get a specific published transparency report.

    This is a public endpoint - only published reports are accessible.
    """
    service: TransparencyReportService = TransparencyReportService(db)
    report = await service.get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return TransparencyReportResponse(
        id=report.id,
        year=report.year,
        month=report.month,
        title=report.title,
        summary=report.summary,
        report_data=report.report_data,
        is_published=report.is_published,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
    )


@router.get(
    "/{report_id}/csv",
    summary="Export published report as CSV",
    description="Download a published transparency report in CSV format.",
)
async def export_report_csv(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Export a published report as CSV.

    This is a public endpoint - only published reports can be exported.
    """
    service: TransparencyReportService = TransparencyReportService(db)
    report = await service.get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    csv_content: str = await service.export_to_csv(report_id)

    filename: str = f"transparency_report_{report.year}_{report.month:02d}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{report_id}/pdf",
    summary="Export published report as PDF",
    description="Download a published transparency report in PDF format.",
)
async def export_report_pdf(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Export a published report as PDF.

    This is a public endpoint - only published reports can be exported.
    """
    service: TransparencyReportService = TransparencyReportService(db)
    report = await service.get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    pdf_content: bytes = await service.export_to_pdf(report_id)

    filename: str = f"transparency_report_{report.year}_{report.month:02d}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==============================================================================
# ADMIN ENDPOINTS
# ==============================================================================


@router.get(
    "/admin/all",
    response_model=TransparencyReportListResponse,
    summary="List all transparency reports (admin)",
    description="Returns all reports including unpublished (admin only).",
)
async def admin_list_all_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = 50,
) -> TransparencyReportListResponse:
    """
    List all transparency reports including unpublished.

    Requires admin authentication.
    """
    service: TransparencyReportService = TransparencyReportService(db)
    reports = await service.list_reports(published_only=False, limit=limit)

    return TransparencyReportListResponse(
        reports=[
            {
                "id": r.id,
                "year": r.year,
                "month": r.month,
                "title": r.title,
                "summary": r.summary,
                "is_published": r.is_published,
                "generated_at": r.generated_at,
                "published_at": r.published_at,
                "created_at": r.created_at,
            }
            for r in reports
        ],
        total=len(reports),
    )


@router.post(
    "/generate",
    response_model=TransparencyReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a transparency report (admin)",
    description="Generate a new transparency report for a specific month.",
)
async def generate_report(
    request: TransparencyReportGenerate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TransparencyReportResponse:
    """
    Generate a transparency report for a specific month.

    Requires admin authentication.
    """
    service: TransparencyReportService = TransparencyReportService(db)

    report = await service.generate_monthly_report(
        year=request.year,
        month=request.month,
        force_regenerate=request.force_regenerate,
    )

    logger.info(
        f"Admin {current_user.email} generated report for {request.year}-{request.month:02d}"
    )

    return TransparencyReportResponse(
        id=report.id,
        year=report.year,
        month=report.month,
        title=report.title,
        summary=report.summary,
        report_data=report.report_data,
        is_published=report.is_published,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
    )


@router.patch(
    "/{report_id}/publish",
    response_model=TransparencyReportResponse,
    summary="Publish a transparency report (admin)",
    description="Make a transparency report publicly visible.",
)
async def publish_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TransparencyReportResponse:
    """
    Publish a transparency report.

    Requires admin authentication.
    """
    service: TransparencyReportService = TransparencyReportService(db)

    try:
        report = await service.publish_report(report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    logger.info(f"Admin {current_user.email} published report {report_id}")

    return TransparencyReportResponse(
        id=report.id,
        year=report.year,
        month=report.month,
        title=report.title,
        summary=report.summary,
        report_data=report.report_data,
        is_published=report.is_published,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
    )


@router.patch(
    "/{report_id}/unpublish",
    response_model=TransparencyReportResponse,
    summary="Unpublish a transparency report (admin)",
    description="Remove a transparency report from public visibility.",
)
async def unpublish_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TransparencyReportResponse:
    """
    Unpublish a transparency report.

    Requires admin authentication.
    """
    service: TransparencyReportService = TransparencyReportService(db)

    try:
        report = await service.unpublish_report(report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    logger.info(f"Admin {current_user.email} unpublished report {report_id}")

    return TransparencyReportResponse(
        id=report.id,
        year=report.year,
        month=report.month,
        title=report.title,
        summary=report.summary,
        report_data=report.report_data,
        is_published=report.is_published,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
    )


@router.post(
    "/{report_id}/send-email",
    response_model=TransparencyReportEmailResult,
    summary="Send report email to admins (admin)",
    description="Send email notification about a report to all admin users.",
)
async def send_report_email(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TransparencyReportEmailResult:
    """
    Send report email notifications to all admin users.

    Requires admin authentication.
    """
    service: TransparencyReportService = TransparencyReportService(db)

    try:
        result: dict[str, Any] = await service.send_report_to_admins(report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    logger.info(f"Admin {current_user.email} sent report {report_id} to admins")

    return TransparencyReportEmailResult(
        emails_queued=result.get("emails_queued", 0),
        pdf_generated=result.get("pdf_generated", True),
        csv_generated=result.get("csv_generated", True),
        report_id=str(report_id),
    )


@router.post(
    "/trigger",
    response_model=TriggerReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger report generation via Celery (admin)",
    description="Queue a report generation task for async processing.",
)
async def trigger_report_generation(
    request: TriggerReportGeneration,
    current_user: User = Depends(require_admin),
) -> TriggerReportResponse:
    """
    Trigger report generation via Celery task.

    This queues the task for asynchronous processing.
    Requires admin authentication.
    """
    from app.tasks.report_tasks import generate_monthly_report_task

    task = generate_monthly_report_task.delay(
        year=request.year,
        month=request.month,
        auto_publish=request.auto_publish,
        notify_admins=request.notify_admins,
    )

    logger.info(f"Admin {current_user.email} triggered report generation task {task.id}")

    return TriggerReportResponse(
        task_id=str(task.id),
        message="Report generation task queued successfully",
    )
