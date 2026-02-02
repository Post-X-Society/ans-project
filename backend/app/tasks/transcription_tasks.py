"""
Celery tasks for audio transcription

Issue #175: Audio Extraction and Whisper Transcription
Provides async task processing for extracting audio from Spotlight videos
and transcribing using OpenAI Whisper API.
"""

import asyncio
import logging
from typing import Any, Optional

from celery import Task
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.spotlight import SpotlightContent
from app.services.audio_extraction_service import (
    AudioExtractionError,
    AudioExtractionResult,
    get_audio_extraction_service,
)
from app.services.whisper_service import (
    TranscriptionResult,
    WhisperServiceError,
    get_whisper_service,
)

logger = logging.getLogger(__name__)


async def _transcribe_spotlight_async(
    spotlight_content_id: str,
) -> dict[str, Any]:
    """Async handler for transcribing spotlight content

    This function:
    1. Retrieves the SpotlightContent from database
    2. Extracts audio from the video file (or downloads from URL)
    3. Transcribes the audio using OpenAI Whisper
    4. Updates the SpotlightContent with transcription data

    Args:
        spotlight_content_id: UUID of the SpotlightContent to transcribe

    Returns:
        Dict containing transcription results or error information
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch SpotlightContent
            stmt = select(SpotlightContent).where(SpotlightContent.id == spotlight_content_id)
            result = await db.execute(stmt)
            spotlight: Optional[SpotlightContent] = result.scalar_one_or_none()

            if not spotlight:
                logger.error(f"SpotlightContent not found: {spotlight_content_id}")
                return {
                    "success": False,
                    "spotlight_content_id": spotlight_content_id,
                    "error": "SpotlightContent not found",
                }

            # Get services
            audio_service = get_audio_extraction_service()
            whisper_service = get_whisper_service()

            # Determine audio source - prefer local file, fallback to URL
            audio_path: Optional[str] = None
            extraction_result: Optional[AudioExtractionResult] = None

            try:
                if spotlight.video_local_path:
                    # Extract from local video file
                    extraction_result = await audio_service.extract_audio_from_video(
                        video_path=spotlight.video_local_path,
                        spotlight_id=spotlight.spotlight_id,
                    )
                    audio_path = extraction_result.audio_path
                elif spotlight.video_url:
                    # Download and extract from URL
                    extraction_result = await audio_service.extract_audio_from_url(
                        spotlight_url=spotlight.video_url,
                        spotlight_id=spotlight.spotlight_id,
                    )
                    audio_path = extraction_result.audio_path
                else:
                    return {
                        "success": False,
                        "spotlight_content_id": spotlight_content_id,
                        "error": "No video source available for transcription",
                    }

            except AudioExtractionError as e:
                logger.error(f"Audio extraction failed for {spotlight_content_id}: {e}")
                return {
                    "success": False,
                    "spotlight_content_id": spotlight_content_id,
                    "error": f"Audio extraction failed: {str(e)}",
                }

            # Transcribe the audio
            try:
                transcription: TranscriptionResult = await whisper_service.transcribe_audio(
                    audio_path
                )
            except WhisperServiceError as e:
                logger.error(f"Transcription failed for {spotlight_content_id}: {e}")
                # Cleanup audio file
                if audio_path:
                    await audio_service.cleanup_audio_file(audio_path)
                return {
                    "success": False,
                    "spotlight_content_id": spotlight_content_id,
                    "error": f"OpenAI API error: {str(e)}",
                }

            # Update SpotlightContent with transcription data
            spotlight.transcription = transcription.text
            spotlight.transcription_language = transcription.language
            spotlight.transcription_confidence = transcription.confidence

            await db.commit()
            logger.info(
                f"Successfully transcribed spotlight {spotlight_content_id}: "
                f"language={transcription.language}, "
                f"confidence={transcription.confidence}"
            )

            # Cleanup audio file after successful transcription
            if audio_path:
                await audio_service.cleanup_audio_file(audio_path)

            # Handle empty transcription (no speech detected)
            message: Optional[str] = None
            if not transcription.text.strip():
                message = "No speech detected in audio"

            return {
                "success": True,
                "spotlight_content_id": spotlight_content_id,
                "submission_id": str(spotlight.submission_id),
                "transcription": transcription.text,
                "language": transcription.language,
                "confidence": transcription.confidence,
                "message": message,
            }

        except Exception as e:
            logger.exception(f"Unexpected error transcribing {spotlight_content_id}: {e}")
            return {
                "success": False,
                "spotlight_content_id": spotlight_content_id,
                "error": f"Unexpected error: {str(e)}",
            }


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="app.tasks.transcription_tasks.transcribe_spotlight",
)
def transcribe_spotlight(
    self: "Task[Any, Any]",
    spotlight_content_id: str,
) -> dict[str, Any]:
    """Celery task to transcribe audio from a Spotlight video

    This task extracts audio from a Snapchat Spotlight video and
    transcribes it using OpenAI Whisper API. The transcription is
    stored in the SpotlightContent record.

    Args:
        self: Celery task instance (bound)
        spotlight_content_id: UUID string of the SpotlightContent to transcribe

    Returns:
        Dict containing:
            - success: bool indicating if transcription succeeded
            - spotlight_content_id: The processed content ID
            - transcription: The transcribed text (on success)
            - language: Detected language code (on success)
            - confidence: Transcription confidence score (on success)
            - error: Error message (on failure)

    Retry Logic:
        - Max retries: 3
        - Retry delay: 60 seconds
        - Retries on temporary failures (network errors, rate limits)
    """
    logger.info(f"Starting transcription task for spotlight: {spotlight_content_id}")

    try:
        # Run async handler in event loop
        # Note: Use asyncio.run() instead of manually creating event loop
        # This ensures proper cleanup and avoids event loop conflicts
        result: dict[str, Any] = asyncio.run(_transcribe_spotlight_async(spotlight_content_id))

        # Log result
        if result["success"]:
            logger.info(
                f"Transcription completed for {spotlight_content_id}: "
                f"language={result.get('language')}"
            )

            # Trigger claim extraction after successful transcription
            try:
                from app.tasks.claim_extraction_tasks import extract_claims_from_transcription

                # Get submission_id from result or query database
                submission_id: Optional[str] = result.get("submission_id")
                if not submission_id:
                    # Query database to get submission_id from spotlight_content_id
                    logger.warning(
                        f"No submission_id in result, skipping claim extraction for {spotlight_content_id}"
                    )
                else:
                    logger.info(f"Triggering claim extraction for submission {submission_id}")
                    extract_claims_from_transcription.delay(submission_id, spotlight_content_id)
            except ImportError:
                logger.warning("Claim extraction task not available, skipping")
            except Exception as e:
                logger.error(f"Failed to trigger claim extraction: {e}")
        else:
            logger.warning(
                f"Transcription failed for {spotlight_content_id}: " f"{result.get('error')}"
            )

        return result

    except Exception as e:
        logger.exception(f"Transcription task failed for {spotlight_content_id}: {e}")
        # Retry on transient errors
        raise self.retry(exc=e) from e
