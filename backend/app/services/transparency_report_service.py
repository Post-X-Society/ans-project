"""
TransparencyReportService for generating and managing monthly transparency reports.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

This service implements:
- Automated monthly transparency report generation
- PDF and CSV export functionality
- Email distribution to administrators
- Public-facing report publication
"""

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transparency_report import TransparencyReport
from app.models.user import User, UserRole
from app.services.analytics_service import AnalyticsService
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

# Type alias for report ID (can be UUID or string)
ReportId = Union[UUID, str]


# ==============================================================================
# CONSTANTS
# ==============================================================================

MONTH_NAMES: dict[int, dict[str, str]] = {
    1: {"en": "January", "nl": "Januari"},
    2: {"en": "February", "nl": "Februari"},
    3: {"en": "March", "nl": "Maart"},
    4: {"en": "April", "nl": "April"},
    5: {"en": "May", "nl": "Mei"},
    6: {"en": "June", "nl": "Juni"},
    7: {"en": "July", "nl": "Juli"},
    8: {"en": "August", "nl": "Augustus"},
    9: {"en": "September", "nl": "September"},
    10: {"en": "October", "nl": "Oktober"},
    11: {"en": "November", "nl": "November"},
    12: {"en": "December", "nl": "December"},
}


# ==============================================================================
# SERVICE CLASS
# ==============================================================================


class TransparencyReportService:
    """
    Service for generating and managing monthly transparency reports.

    Provides:
    - Report generation with analytics data
    - PDF and CSV export
    - Publication management
    - Email distribution to admins
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the transparency report service.

        Args:
            db: Async database session
        """
        self.db = db
        self.analytics_service = AnalyticsService(db)

    # ==========================================================================
    # REPORT GENERATION
    # ==========================================================================

    async def generate_monthly_report(
        self,
        year: int,
        month: int,
        force_regenerate: bool = False,
    ) -> TransparencyReport:
        """
        Generate a monthly transparency report.

        Args:
            year: Report year
            month: Report month (1-12)
            force_regenerate: If True, regenerate even if report exists

        Returns:
            The generated TransparencyReport
        """
        # Check if report already exists
        existing_report: Optional[TransparencyReport] = await self.get_report_by_month(year, month)

        if existing_report and not force_regenerate:
            logger.info(f"Report for {year}-{month:02d} already exists")
            return existing_report

        # Generate report data from analytics service
        report_data: dict[str, Any] = await self._generate_report_data(year, month)

        # Generate multilingual title and summary
        month_name: dict[str, str] = MONTH_NAMES.get(month, {"en": str(month), "nl": str(month)})
        title: dict[str, str] = {
            "en": f"Monthly Transparency Report - {month_name['en']} {year}",
            "nl": f"Maandelijks Transparantierapport - {month_name['nl']} {year}",
        }
        summary: dict[str, str] = await self._generate_summary(report_data)

        now: datetime = datetime.now(timezone.utc)

        if existing_report and force_regenerate:
            # Update existing report
            existing_report.report_data = report_data
            existing_report.title = title
            existing_report.summary = summary
            existing_report.generated_at = now
            await self.db.commit()
            await self.db.refresh(existing_report)
            logger.info(f"Regenerated report for {year}-{month:02d}")
            return existing_report

        # Create new report
        report: TransparencyReport = TransparencyReport(
            year=year,
            month=month,
            report_data=report_data,
            title=title,
            summary=summary,
            generated_at=now,
            is_published=False,
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        logger.info(f"Generated new report for {year}-{month:02d}")
        return report

    async def _generate_report_data(self, year: int, month: int) -> dict[str, Any]:
        """
        Generate report data by collecting all analytics metrics.

        Args:
            year: Report year
            month: Report month

        Returns:
            Dictionary containing all report metrics
        """
        # Get all analytics data
        monthly_fact_checks: dict[str, Any] = (
            await self.analytics_service.get_monthly_fact_check_counts(months=12)
        )
        time_to_publication: dict[str, Any] = (
            await self.analytics_service.get_time_to_publication_metrics()
        )
        rating_distribution: dict[str, Any] = await self.analytics_service.get_rating_distribution()
        source_quality: dict[str, Any] = await self.analytics_service.get_source_quality_metrics()
        correction_rate: dict[str, Any] = await self.analytics_service.get_correction_rate_metrics()
        efcsn_compliance: dict[str, Any] = await self.analytics_service.get_efcsn_compliance()

        # Convert datetime objects to ISO strings for JSON serialization
        if efcsn_compliance.get("last_checked"):
            efcsn_compliance["last_checked"] = efcsn_compliance["last_checked"].isoformat()

        return {
            "report_period": {
                "year": year,
                "month": month,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "monthly_fact_checks": monthly_fact_checks,
            "time_to_publication": time_to_publication,
            "rating_distribution": rating_distribution,
            "source_quality": source_quality,
            "correction_rate": correction_rate,
            "efcsn_compliance": efcsn_compliance,
        }

    async def _generate_summary(self, report_data: dict[str, Any]) -> dict[str, str]:
        """
        Generate multilingual summary from report data.

        Args:
            report_data: The full report data

        Returns:
            Dictionary with English and Dutch summaries
        """
        # Extract key metrics
        monthly_data: dict[str, Any] = report_data.get("monthly_fact_checks", {})
        total_fc: int = monthly_data.get("total_count", 0)
        avg_fc: float = monthly_data.get("average_per_month", 0.0)

        compliance_data: dict[str, Any] = report_data.get("efcsn_compliance", {})
        compliance_status: str = compliance_data.get("overall_status", "unknown")
        compliance_score: float = compliance_data.get("compliance_score", 0.0)

        correction_data: dict[str, Any] = report_data.get("correction_rate", {})
        correction_rate: float = correction_data.get("correction_rate", 0.0)

        # Generate English summary
        en_summary: str = (
            f"This month's transparency report shows {total_fc} fact-checks published "
            f"(average {avg_fc:.1f}/month). EFCSN compliance status: {compliance_status} "
            f"({compliance_score:.0f}%). Correction rate: {correction_rate:.2%}."
        )

        # Generate Dutch summary
        status_nl: dict[str, str] = {
            "compliant": "conform",
            "at_risk": "risico",
            "non_compliant": "niet-conform",
            "unknown": "onbekend",
        }
        nl_status: str = status_nl.get(compliance_status, compliance_status)

        nl_summary: str = (
            f"Dit maandelijkse transparantierapport toont {total_fc} gepubliceerde "
            f"factchecks (gemiddeld {avg_fc:.1f}/maand). EFCSN-nalevingsstatus: {nl_status} "
            f"({compliance_score:.0f}%). Correctiepercentage: {correction_rate:.2%}."
        )

        return {"en": en_summary, "nl": nl_summary}

    # ==========================================================================
    # REPORT RETRIEVAL
    # ==========================================================================

    async def get_report_by_id(self, report_id: ReportId) -> Optional[TransparencyReport]:
        """
        Get a report by its ID.

        Args:
            report_id: The report's UUID

        Returns:
            The report if found, None otherwise
        """
        stmt = select(TransparencyReport).where(TransparencyReport.id == str(report_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_report_by_month(self, year: int, month: int) -> Optional[TransparencyReport]:
        """
        Get a report by year and month.

        Args:
            year: Report year
            month: Report month

        Returns:
            The report if found, None otherwise
        """
        stmt = select(TransparencyReport).where(
            TransparencyReport.year == year,
            TransparencyReport.month == month,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        published_only: bool = True,
        limit: int = 24,
    ) -> list[TransparencyReport]:
        """
        List transparency reports.

        Args:
            published_only: If True, only return published reports
            limit: Maximum number of reports to return

        Returns:
            List of TransparencyReport objects
        """
        stmt = select(TransparencyReport).order_by(
            TransparencyReport.year.desc(),
            TransparencyReport.month.desc(),
        )

        if published_only:
            stmt = stmt.where(TransparencyReport.is_published.is_(True))

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ==========================================================================
    # PUBLISHING
    # ==========================================================================

    async def publish_report(self, report_id: ReportId) -> TransparencyReport:
        """
        Publish a transparency report.

        Args:
            report_id: The report's UUID

        Returns:
            The updated report

        Raises:
            ValueError: If report not found
        """
        report: Optional[TransparencyReport] = await self.get_report_by_id(report_id)

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        report.is_published = True
        report.published_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(report)

        logger.info(f"Published report {report_id}")
        return report

    async def unpublish_report(self, report_id: ReportId) -> TransparencyReport:
        """
        Unpublish a transparency report.

        Args:
            report_id: The report's UUID

        Returns:
            The updated report

        Raises:
            ValueError: If report not found
        """
        report: Optional[TransparencyReport] = await self.get_report_by_id(report_id)

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        report.is_published = False

        await self.db.commit()
        await self.db.refresh(report)

        logger.info(f"Unpublished report {report_id}")
        return report

    # ==========================================================================
    # EXPORT - CSV
    # ==========================================================================

    async def export_to_csv(self, report_id: ReportId) -> str:
        """
        Export a report to CSV format.

        Args:
            report_id: The report's UUID

        Returns:
            CSV string content

        Raises:
            ValueError: If report not found
        """
        report: Optional[TransparencyReport] = await self.get_report_by_id(report_id)

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Metric", "Value", "Details"])

        # Report period info
        writer.writerow(["Report Period", f"{report.year}-{report.month:02d}", ""])
        writer.writerow(["Generated At", report.generated_at.isoformat(), ""])
        writer.writerow([])

        # Monthly fact-checks
        monthly_data: dict[str, Any] = report.report_data.get("monthly_fact_checks", {})
        writer.writerow(["MONTHLY FACT-CHECKS", "", ""])
        writer.writerow(["Total Count", monthly_data.get("total_count", 0), ""])
        writer.writerow(["Average Per Month", monthly_data.get("average_per_month", 0), ""])
        writer.writerow([])

        # Rating distribution
        rating_data: dict[str, Any] = report.report_data.get("rating_distribution", {})
        writer.writerow(["RATING DISTRIBUTION", "", ""])
        for rating in rating_data.get("ratings", []):
            writer.writerow(
                [
                    rating.get("rating", ""),
                    rating.get("count", 0),
                    f"{rating.get('percentage', 0):.1f}%",
                ]
            )
        writer.writerow([])

        # Source quality
        source_data: dict[str, Any] = report.report_data.get("source_quality", {})
        writer.writerow(["SOURCE QUALITY METRICS", "", ""])
        writer.writerow(
            [
                "Average Sources Per Fact-Check",
                source_data.get("average_sources_per_fact_check", 0),
                "",
            ]
        )
        writer.writerow(
            [
                "Average Credibility Score",
                source_data.get("average_credibility_score", 0),
                "Scale: 1-5",
            ]
        )
        writer.writerow(["Total Sources", source_data.get("total_sources", 0), ""])
        writer.writerow([])

        # Correction rate
        correction_data: dict[str, Any] = report.report_data.get("correction_rate", {})
        writer.writerow(["CORRECTION METRICS", "", ""])
        writer.writerow(["Total Corrections", correction_data.get("total_corrections", 0), ""])
        writer.writerow(
            ["Corrections Accepted", correction_data.get("corrections_accepted", 0), ""]
        )
        writer.writerow(
            ["Corrections Rejected", correction_data.get("corrections_rejected", 0), ""]
        )
        writer.writerow(
            [
                "Correction Rate",
                f"{correction_data.get('correction_rate', 0):.2%}",
                "Corrections per fact-check",
            ]
        )
        writer.writerow([])

        # EFCSN Compliance
        compliance_data: dict[str, Any] = report.report_data.get("efcsn_compliance", {})
        writer.writerow(["EFCSN COMPLIANCE", "", ""])
        writer.writerow(["Overall Status", compliance_data.get("overall_status", ""), ""])
        writer.writerow(
            [
                "Compliance Score",
                f"{compliance_data.get('compliance_score', 0):.1f}%",
                "",
            ]
        )

        for item in compliance_data.get("checklist", []):
            writer.writerow(
                [
                    item.get("requirement", ""),
                    item.get("status", ""),
                    item.get("details", ""),
                ]
            )

        return output.getvalue()

    # ==========================================================================
    # EXPORT - PDF
    # ==========================================================================

    async def export_to_pdf(self, report_id: ReportId) -> bytes:
        """
        Export a report to PDF format.

        Uses a simple PDF generation approach that doesn't require
        external dependencies like wkhtmltopdf or weasyprint.

        Args:
            report_id: The report's UUID

        Returns:
            PDF bytes content

        Raises:
            ValueError: If report not found
        """
        report: Optional[TransparencyReport] = await self.get_report_by_id(report_id)

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        # Generate PDF using simple text-based approach
        # For a production system, consider using reportlab or weasyprint
        pdf_content: bytes = self._generate_simple_pdf(report)

        return pdf_content

    def _generate_simple_pdf(self, report: TransparencyReport) -> bytes:
        """
        Generate a simple PDF document from report data.

        This is a basic implementation using reportlab if available,
        or a simple text-based PDF otherwise.

        Args:
            report: The TransparencyReport to convert

        Returns:
            PDF bytes
        """
        import importlib.util

        # Check if reportlab is available
        if importlib.util.find_spec("reportlab") is not None:
            return self._generate_reportlab_pdf(report)
        else:
            # Fall back to minimal PDF if reportlab not available
            return self._generate_minimal_pdf(report)

    def _generate_reportlab_pdf(self, report: TransparencyReport) -> bytes:
        """Generate PDF using reportlab library."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements: list[Any] = []

        # Title
        title: str = report.title.get("en", f"Report {report.year}-{report.month:02d}")
        elements.append(Paragraph(title, styles["Heading1"]))
        elements.append(Spacer(1, 0.5 * cm))

        # Summary
        summary: str = report.summary.get("en", "")
        elements.append(Paragraph(summary, styles["Normal"]))
        elements.append(Spacer(1, 1 * cm))

        # Key Metrics Table
        elements.append(Paragraph("Key Metrics", styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * cm))

        monthly_data: dict[str, Any] = report.report_data.get("monthly_fact_checks", {})
        compliance_data: dict[str, Any] = report.report_data.get("efcsn_compliance", {})
        correction_data: dict[str, Any] = report.report_data.get("correction_rate", {})

        metrics_data: list[list[str]] = [
            ["Metric", "Value"],
            ["Total Fact-Checks", str(monthly_data.get("total_count", 0))],
            ["Average Per Month", f"{monthly_data.get('average_per_month', 0):.1f}"],
            ["EFCSN Compliance", compliance_data.get("overall_status", "N/A")],
            ["Compliance Score", f"{compliance_data.get('compliance_score', 0):.1f}%"],
            ["Total Corrections", str(correction_data.get("total_corrections", 0))],
        ]

        table = Table(metrics_data, colWidths=[10 * cm, 5 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 1 * cm))

        # Rating Distribution
        rating_data: dict[str, Any] = report.report_data.get("rating_distribution", {})
        if rating_data.get("ratings"):
            elements.append(Paragraph("Rating Distribution", styles["Heading2"]))
            elements.append(Spacer(1, 0.3 * cm))

            rating_rows: list[list[str]] = [["Rating", "Count", "Percentage"]]
            for rating in rating_data.get("ratings", []):
                rating_rows.append(
                    [
                        str(rating.get("rating", "")),
                        str(rating.get("count", 0)),
                        f"{rating.get('percentage', 0):.1f}%",
                    ]
                )

            rating_table = Table(rating_rows, colWidths=[6 * cm, 4 * cm, 5 * cm])
            rating_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(rating_table)
            elements.append(Spacer(1, 1 * cm))

        # EFCSN Compliance Checklist
        if compliance_data.get("checklist"):
            elements.append(Paragraph("EFCSN Compliance Checklist", styles["Heading2"]))
            elements.append(Spacer(1, 0.3 * cm))

            checklist_rows: list[list[str]] = [["Requirement", "Status", "Details"]]
            for item in compliance_data.get("checklist", []):
                checklist_rows.append(
                    [
                        str(item.get("requirement", "")),
                        str(item.get("status", "")),
                        str(item.get("details", "")),
                    ]
                )

            checklist_table = Table(checklist_rows, colWidths=[5 * cm, 3 * cm, 7 * cm])
            checklist_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(checklist_table)

        # Footer
        elements.append(Spacer(1, 2 * cm))
        footer_text: str = f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}"
        elements.append(Paragraph(footer_text, styles["Normal"]))

        doc.build(elements)
        return buffer.getvalue()

    def _generate_minimal_pdf(self, report: TransparencyReport) -> bytes:
        """
        Generate a minimal PDF without external dependencies.

        This creates a basic PDF 1.4 document manually.
        """
        title: str = report.title.get("en", f"Report {report.year}-{report.month:02d}")
        summary: str = report.summary.get("en", "")

        # Basic PDF structure
        pdf_content: str = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 500 >>
stream
BT
/F1 18 Tf
50 750 Td
({title}) Tj
/F1 12 Tf
0 -30 Td
({summary[:100]}...) Tj
0 -20 Td
(Report Period: {report.year}-{report.month:02d}) Tj
0 -20 Td
(Generated: {report.generated_at.strftime('%Y-%m-%d')}) Tj
0 -30 Td
(For full details, please view the CSV export.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000819 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
896
%%EOF"""

        return pdf_content.encode("latin-1")

    # ==========================================================================
    # EMAIL DISTRIBUTION
    # ==========================================================================

    async def send_report_to_admins(self, report_id: ReportId) -> dict[str, Any]:
        """
        Send report notification to all admin users.

        Args:
            report_id: The report's UUID

        Returns:
            Dictionary with email sending results

        Raises:
            ValueError: If report not found
        """
        report: Optional[TransparencyReport] = await self.get_report_by_id(report_id)

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        # Get all admin and super_admin users
        stmt = select(User).where(
            User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]),
            User.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        admins: list[User] = list(result.scalars().all())

        if not admins:
            logger.warning("No admin users found to send report to")
            return {"emails_queued": 0, "pdf_generated": True, "csv_generated": True}

        # Generate email content
        title: str = report.title.get("en", f"Report {report.year}-{report.month:02d}")
        summary: str = report.summary.get("en", "")

        subject: str = f"[AnsCheckt] Monthly Transparency Report - {report.year}/{report.month:02d}"

        body_html: str = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>{title}</h2>
            <p>{summary}</p>

            <h3>Key Highlights</h3>
            <ul>
                <li>Total Fact-Checks: {report.report_data.get('monthly_fact_checks', {}).get('total_count', 0)}</li>
                <li>EFCSN Compliance: {report.report_data.get('efcsn_compliance', {}).get('overall_status', 'N/A')}</li>
                <li>Compliance Score: {report.report_data.get('efcsn_compliance', {}).get('compliance_score', 0):.1f}%</li>
            </ul>

            <p>You can download the full report in PDF or CSV format from the admin dashboard.</p>

            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                This is an automated message from AnsCheckt.
                Report ID: {report.id}
            </p>
        </body>
        </html>
        """

        body_text: str = f"""
{title}

{summary}

Key Highlights:
- Total Fact-Checks: {report.report_data.get('monthly_fact_checks', {}).get('total_count', 0)}
- EFCSN Compliance: {report.report_data.get('efcsn_compliance', {}).get('overall_status', 'N/A')}
- Compliance Score: {report.report_data.get('efcsn_compliance', {}).get('compliance_score', 0):.1f}%

You can download the full report in PDF or CSV format from the admin dashboard.

---
This is an automated message from AnsCheckt.
Report ID: {report.id}
        """

        # Queue emails for all admins
        emails_queued: int = 0
        for admin in admins:
            try:
                email_service.queue_email(
                    to_email=admin.email,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    template="monthly_transparency_report",
                )
                emails_queued += 1
            except Exception as e:
                logger.error(f"Failed to queue email for {admin.email}: {e}")

        logger.info(f"Queued {emails_queued} emails for report {report_id}")

        return {
            "emails_queued": emails_queued,
            "pdf_generated": True,
            "csv_generated": True,
            "report_id": str(report_id),
        }
