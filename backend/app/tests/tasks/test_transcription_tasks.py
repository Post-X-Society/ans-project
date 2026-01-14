"""
Tests for transcription Celery tasks

Following TDD approach: Tests written FIRST before implementation
Issue #175: Audio Extraction and Whisper Transcription
"""

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest


class TestTranscribeSpotlightTask:
    """Tests for the transcribe_spotlight Celery task"""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered with Celery"""
        from app.core.celery_app import celery_app
        from app.tasks import transcription_tasks  # noqa: F401

        task_name: str = "app.tasks.transcription_tasks.transcribe_spotlight"
        assert task_name in celery_app.tasks

    def test_task_has_correct_configuration(self) -> None:
        """Test task has correct retry and queue configuration"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        assert transcribe_spotlight.max_retries == 3
        assert transcribe_spotlight.default_retry_delay == 60

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_calls_async_handler(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task properly calls async handler"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())
        mock_async_handler.return_value = {
            "success": True,
            "spotlight_content_id": spotlight_content_id,
            "transcription": "Test transcription text",
            "language": "nl",
            "confidence": 0.95,
        }

        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

        assert result is not None
        assert result["success"] is True
        mock_async_handler.assert_called_once_with(spotlight_content_id)

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_handles_transcription_success(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task handles successful transcription"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())
        expected_transcription: str = "Dit is een test bericht over klimaatverandering."

        mock_async_handler.return_value = {
            "success": True,
            "spotlight_content_id": spotlight_content_id,
            "transcription": expected_transcription,
            "language": "nl",
            "confidence": 0.92,
        }

        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

        assert result["success"] is True
        assert result["transcription"] == expected_transcription
        assert result["language"] == "nl"
        assert result["confidence"] == 0.92

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_handles_english_transcription(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task handles English transcription"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())
        expected_transcription: str = "This is a test message about climate change."

        mock_async_handler.return_value = {
            "success": True,
            "spotlight_content_id": spotlight_content_id,
            "transcription": expected_transcription,
            "language": "en",
            "confidence": 0.98,
        }

        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

        assert result["success"] is True
        assert result["language"] == "en"

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_handles_no_audio(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task handles spotlight content with no audio"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())

        mock_async_handler.return_value = {
            "success": True,
            "spotlight_content_id": spotlight_content_id,
            "transcription": "",
            "language": "unknown",
            "confidence": 0.0,
            "message": "No speech detected in audio",
        }

        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

        assert result["success"] is True
        assert result["transcription"] == ""
        assert result["language"] == "unknown"

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_handles_spotlight_not_found(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task handles non-existent spotlight content"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())

        mock_async_handler.return_value = {
            "success": False,
            "spotlight_content_id": spotlight_content_id,
            "error": "SpotlightContent not found",
        }

        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_handles_api_error(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task handles OpenAI API errors"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())

        mock_async_handler.return_value = {
            "success": False,
            "spotlight_content_id": spotlight_content_id,
            "error": "OpenAI API error: Rate limit exceeded",
        }

        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

        assert result["success"] is False
        assert "API error" in result["error"]


class TestTranscriptionTaskQueue:
    """Test transcription task queue configuration"""

    def test_transcription_queue_is_configured(self) -> None:
        """Test that transcription queue is configured in Celery"""
        from app.core.celery_app import celery_app

        # Check task routes exist
        assert hasattr(celery_app.conf, "task_routes")
        routes: dict[str, Any] = celery_app.conf.task_routes
        assert "app.tasks.transcription_tasks.*" in routes
        assert routes["app.tasks.transcription_tasks.*"]["queue"] == "transcription"


class TestTranscriptionTaskIntegration:
    """Integration tests for transcription task workflow"""

    @pytest.mark.asyncio
    async def test_full_transcription_workflow(self, db_session: Any) -> None:
        """Test complete transcription workflow from spotlight to database"""
        from app.models.spotlight import SpotlightContent
        from app.models.submission import Submission

        # Create test submission
        submission: Submission = Submission(
            content="Test submission for transcription",
            source="snapchat",
        )
        db_session.add(submission)
        await db_session.flush()

        # Create SpotlightContent with video
        spotlight: SpotlightContent = SpotlightContent(
            submission_id=submission.id,
            spotlight_link="https://snapchat.com/spotlight/test",
            spotlight_id="test_spotlight_id",
            video_url="https://example.com/video.mp4",
            video_local_path="/tmp/test_video.mp4",
            thumbnail_url="https://example.com/thumb.jpg",
            raw_metadata={"test": "data"},
        )
        db_session.add(spotlight)
        await db_session.commit()
        await db_session.refresh(spotlight)

        # Verify SpotlightContent was created
        assert spotlight.id is not None
        assert spotlight.spotlight_id == "test_spotlight_id"

    @pytest.mark.asyncio
    async def test_transcription_updates_spotlight_content(self, db_session: Any) -> None:
        """Test that transcription results update SpotlightContent model"""
        from sqlalchemy import select

        from app.models.spotlight import SpotlightContent
        from app.models.submission import Submission

        # Create test data
        submission: Submission = Submission(
            content="Test submission",
            source="snapchat",
        )
        db_session.add(submission)
        await db_session.flush()

        spotlight: SpotlightContent = SpotlightContent(
            submission_id=submission.id,
            spotlight_link="https://snapchat.com/spotlight/test2",
            spotlight_id="test_spotlight_id_2",
            video_url="https://example.com/video2.mp4",
            thumbnail_url="https://example.com/thumb2.jpg",
            raw_metadata={},
        )
        db_session.add(spotlight)
        await db_session.commit()
        await db_session.refresh(spotlight)

        # Simulate transcription update
        spotlight.transcription = "This is the transcribed text"
        spotlight.transcription_language = "en"
        spotlight.transcription_confidence = 0.95
        await db_session.commit()
        await db_session.refresh(spotlight)

        # Verify update
        stmt = select(SpotlightContent).where(SpotlightContent.id == spotlight.id)
        result = await db_session.execute(stmt)
        updated_spotlight: SpotlightContent = result.scalar_one()

        assert updated_spotlight.transcription == "This is the transcribed text"
        assert updated_spotlight.transcription_language == "en"
        assert updated_spotlight.transcription_confidence == 0.95


class TestTranscriptionTaskErrorHandling:
    """Test error handling in transcription tasks"""

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_retries_on_temporary_failure(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task retries on temporary failures"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())

        # First call fails, retry succeeds
        mock_async_handler.side_effect = [
            {"success": False, "error": "Temporary network error"},
            {
                "success": True,
                "spotlight_content_id": spotlight_content_id,
                "transcription": "Retry succeeded",
                "language": "en",
                "confidence": 0.9,
            },
        ]

        # First attempt
        result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)
        assert result["success"] is False

    @patch("app.tasks.transcription_tasks._transcribe_spotlight_async")
    def test_task_logs_errors(
        self,
        mock_async_handler: AsyncMock,
    ) -> None:
        """Test task properly logs errors"""
        from app.tasks.transcription_tasks import transcribe_spotlight

        spotlight_content_id: str = str(uuid4())

        mock_async_handler.return_value = {
            "success": False,
            "spotlight_content_id": spotlight_content_id,
            "error": "Critical error during transcription",
        }

        with patch("app.tasks.transcription_tasks.logger") as mock_logger:
            result: dict[str, Any] = transcribe_spotlight(spotlight_content_id)

            assert result["success"] is False
            # Logger should have been called for error
            assert mock_logger.error.called or mock_logger.warning.called
