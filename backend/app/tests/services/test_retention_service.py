"""
Tests for data retention service

Issue #91: Data Retention Policies & Auto-Cleanup
Tests written FIRST following TDD approach
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.retention_service import RetentionService
from app.core.config import settings
from app.models.submission import Submission
from app.models.workflow_transition import WorkflowState
from app.models.correction import Correction, CorrectionStatus
from app.models.user import User, UserRole


@pytest.mark.asyncio
class TestRetentionServiceConfiguration:
    """Test that retention service reads configuration correctly"""

    async def test_reads_unpublished_submissions_retention_period(self) -> None:
        """Test that service reads unpublished submissions retention from config"""
        service: RetentionService = RetentionService()
        assert (
            service.unpublished_submissions_days == settings.RETENTION_UNPUBLISHED_SUBMISSIONS_DAYS
        )

    async def test_reads_audit_logs_retention_period(self) -> None:
        """Test that service reads audit logs retention from config"""
        service: RetentionService = RetentionService()
        assert service.audit_logs_days == settings.RETENTION_AUDIT_LOGS_DAYS

    async def test_reads_draft_evidence_retention_period(self) -> None:
        """Test that service reads draft evidence retention from config"""
        service: RetentionService = RetentionService()
        assert service.draft_evidence_days == settings.RETENTION_DRAFT_EVIDENCE_DAYS

    async def test_reads_rejected_claims_retention_period(self) -> None:
        """Test that service reads rejected claims retention from config"""
        service: RetentionService = RetentionService()
        assert service.rejected_claims_days == settings.RETENTION_REJECTED_CLAIMS_DAYS

    async def test_reads_correction_requests_retention_period(self) -> None:
        """Test that service reads correction requests retention from config"""
        service: RetentionService = RetentionService()
        assert service.correction_requests_days == settings.RETENTION_CORRECTION_REQUESTS_DAYS

    async def test_default_values_are_correct(self) -> None:
        """Test that default retention periods match requirements"""
        assert settings.RETENTION_UNPUBLISHED_SUBMISSIONS_DAYS == 90
        assert settings.RETENTION_AUDIT_LOGS_DAYS == 2555  # 7 years
        assert settings.RETENTION_DRAFT_EVIDENCE_DAYS == 730  # 2 years
        assert settings.RETENTION_REJECTED_CLAIMS_DAYS == 365  # 1 year
        assert settings.RETENTION_CORRECTION_REQUESTS_DAYS == 1095  # 3 years
