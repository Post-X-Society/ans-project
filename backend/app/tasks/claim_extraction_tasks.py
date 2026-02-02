"""
Celery tasks for claim extraction using OpenAI GPT-4

Issue #176: LLM-based claim extraction from transcriptions
"""

import asyncio
import logging
from typing import Any

from celery import Task  # type: ignore[import]
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.spotlight import SpotlightContent
from app.schemas.claim import ClaimExtractionRequest
from app.services.llm_claim_extraction_service import LLMClaimExtractionService

logger = logging.getLogger(__name__)


async def _extract_claims_async(submission_id: str, spotlight_content_id: str) -> dict[str, Any]:
    """Async helper to extract claims from transcription

    Args:
        submission_id: UUID of the submission
        spotlight_content_id: UUID of the spotlight content

    Returns:
        Dictionary with success status and extracted claims
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch SpotlightContent with transcription
            stmt = select(SpotlightContent).where(SpotlightContent.id == spotlight_content_id)
            result = await db.execute(stmt)
            spotlight: SpotlightContent | None = result.scalar_one_or_none()

            if not spotlight:
                logger.error(f"SpotlightContent not found: {spotlight_content_id}")
                return {
                    "success": False,
                    "submission_id": submission_id,
                    "error": "SpotlightContent not found",
                }

            if not spotlight.transcription:
                logger.warning(f"No transcription available for {spotlight_content_id}")
                return {
                    "success": False,
                    "submission_id": submission_id,
                    "error": "No transcription available",
                }

            # Extract claims using LLM service
            llm_service = LLMClaimExtractionService(db)
            extraction_request = ClaimExtractionRequest(
                transcription=spotlight.transcription,
                language_hint=spotlight.transcription_language or "en",
                deduplicate=True,
            )

            extraction_result = await llm_service.extract_claims(
                submission_id=submission_id,
                request=extraction_request,
            )

            logger.info(
                f"Extracted {extraction_result.total_claims} claims from submission {submission_id}: "
                f"{extraction_result.new_claims} new, {extraction_result.duplicates_found} duplicates"
            )

            return {
                "success": True,
                "submission_id": submission_id,
                "total_claims": extraction_result.total_claims,
                "new_claims": extraction_result.new_claims,
                "duplicates_found": extraction_result.duplicates_found,
            }

        except Exception as e:
            logger.exception(f"Unexpected error extracting claims from {submission_id}: {e}")
            return {
                "success": False,
                "submission_id": submission_id,
                "error": f"Unexpected error: {str(e)}",
            }


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="app.tasks.claim_extraction_tasks.extract_claims_from_transcription",
)
def extract_claims_from_transcription(
    self: "Task[Any, Any]",
    submission_id: str,
    spotlight_content_id: str,
) -> dict[str, Any]:
    """Celery task to extract claims from a transcribed Spotlight video

    This task is triggered automatically after successful transcription.
    It uses OpenAI GPT-4 to extract factual claims from the transcribed text.

    Args:
        self: Celery task instance (auto-injected by bind=True)
        submission_id: UUID string of the submission
        spotlight_content_id: UUID string of the spotlight content

    Returns:
        Dictionary containing:
        - success: bool - Whether extraction succeeded
        - submission_id: str - Submission UUID
        - total_claims: int - Total number of claims extracted
        - new_claims: int - Number of new claims (not duplicates)
        - duplicates_found: int - Number of duplicate claims found
        - error: str - Error message if failed

    Retry behavior:
        - Max retries: 3
        - Retry delay: 60 seconds
        - Retries on temporary failures (API errors, rate limits)
    """
    logger.info(f"Starting claim extraction for submission: {submission_id}")

    try:
        result: dict[str, Any] = asyncio.run(
            _extract_claims_async(submission_id, spotlight_content_id)
        )

        if result["success"]:
            logger.info(
                f"Claim extraction completed for {submission_id}: "
                f"{result.get('total_claims')} claims extracted"
            )
        else:
            logger.warning(f"Claim extraction failed for {submission_id}: {result.get('error')}")

        return result

    except Exception as e:
        logger.exception(f"Claim extraction task failed for {submission_id}: {e}")
        # Retry on transient errors
        raise self.retry(exc=e) from e
