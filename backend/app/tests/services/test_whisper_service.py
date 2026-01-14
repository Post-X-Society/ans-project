"""
Tests for Whisper transcription service

Following TDD approach: Tests written FIRST before implementation
Issue #175: Audio Extraction and Whisper Transcription
"""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.services.whisper_service import (
    TranscriptionResult,
    WhisperService,
    WhisperServiceError,
)


class TestWhisperServiceInitialization:
    """Test WhisperService initialization"""

    def test_whisper_service_initialization_with_api_key(self) -> None:
        """Test WhisperService initializes correctly with API key"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"}):
            service: WhisperService = WhisperService()
            assert service is not None
            assert isinstance(service, WhisperService)

    def test_whisper_service_raises_error_without_api_key(self) -> None:
        """Test WhisperService raises error when API key is missing"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=True):
            with patch("app.services.whisper_service.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = None
                with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                    WhisperService()

    def test_whisper_service_has_supported_languages(self) -> None:
        """Test WhisperService supports Dutch and English"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"}):
            service: WhisperService = WhisperService()
            assert "en" in service.SUPPORTED_LANGUAGES
            assert "nl" in service.SUPPORTED_LANGUAGES


class TestWhisperServiceTranscription:
    """Test WhisperService transcription functionality"""

    @pytest.fixture
    def whisper_service(self) -> Generator[WhisperService, None, None]:
        """Provide WhisperService instance with mocked API key"""
        with patch("app.services.whisper_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_WHISPER_MODEL = "whisper-1"
            service: WhisperService = WhisperService()
            yield service

    @pytest.fixture
    def mock_openai_client(self) -> Generator[Mock, None, None]:
        """Provide mocked OpenAI client"""
        with patch("app.services.whisper_service.OpenAI") as mock:
            mock_instance: Mock = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(
        self, whisper_service: WhisperService, mock_openai_client: Mock
    ) -> None:
        """Test successful audio transcription"""
        # Arrange
        audio_file_path: str = "/tmp/test_audio.mp3"
        expected_text: str = "Dit is een test transcriptie."
        expected_language: str = "nl"

        # Mock the transcription response
        mock_response: Mock = Mock()
        mock_response.text = expected_text
        mock_response.language = expected_language

        with patch("builtins.open", MagicMock()):
            with patch.object(
                whisper_service, "_call_whisper_api", new_callable=AsyncMock
            ) as mock_call:
                mock_call.return_value = TranscriptionResult(
                    text=expected_text,
                    language=expected_language,
                    confidence=0.95,
                )

                # Act
                result: TranscriptionResult = await whisper_service.transcribe_audio(
                    audio_file_path
                )

                # Assert
                assert result.text == expected_text
                assert result.language == expected_language
                assert result.confidence is not None
                assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_language_hint(
        self, whisper_service: WhisperService
    ) -> None:
        """Test transcription with language hint"""
        # Arrange
        audio_file_path: str = "/tmp/test_audio.mp3"
        language_hint: str = "nl"

        with patch.object(
            whisper_service, "_call_whisper_api", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = TranscriptionResult(
                text="Test transcription",
                language="nl",
                confidence=0.92,
            )

            # Act
            result: TranscriptionResult = await whisper_service.transcribe_audio(
                audio_file_path, language_hint=language_hint
            )

            # Assert
            mock_call.assert_called_once()
            # Verify language hint was passed
            assert result.language == "nl"

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self, whisper_service: WhisperService) -> None:
        """Test transcription fails when audio file not found"""
        # Arrange
        non_existent_file: str = "/tmp/non_existent_audio.mp3"

        # Act & Assert
        with pytest.raises(WhisperServiceError, match="Audio file not found"):
            await whisper_service.transcribe_audio(non_existent_file)

    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, whisper_service: WhisperService) -> None:
        """Test transcription handles API errors gracefully"""
        # Arrange
        audio_file_path: str = "/tmp/test_audio.mp3"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(
                whisper_service, "_call_whisper_api", new_callable=AsyncMock
            ) as mock_call:
                mock_call.side_effect = Exception("OpenAI API error")

                # Act & Assert
                with pytest.raises(WhisperServiceError, match="Transcription failed"):
                    await whisper_service.transcribe_audio(audio_file_path)

    @pytest.mark.asyncio
    async def test_transcribe_audio_returns_english(self, whisper_service: WhisperService) -> None:
        """Test transcription correctly identifies English audio"""
        # Arrange
        audio_file_path: str = "/tmp/test_audio_en.mp3"
        expected_text: str = "This is a test transcription in English."

        with patch.object(
            whisper_service, "_call_whisper_api", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = TranscriptionResult(
                text=expected_text,
                language="en",
                confidence=0.98,
            )

            # Act
            result: TranscriptionResult = await whisper_service.transcribe_audio(audio_file_path)

            # Assert
            assert result.language == "en"
            assert result.text == expected_text


class TestTranscriptionResult:
    """Test TranscriptionResult dataclass"""

    def test_transcription_result_creation(self) -> None:
        """Test TranscriptionResult can be created with all fields"""
        result: TranscriptionResult = TranscriptionResult(
            text="Test text",
            language="nl",
            confidence=0.95,
        )
        assert result.text == "Test text"
        assert result.language == "nl"
        assert result.confidence == 0.95

    def test_transcription_result_optional_confidence(self) -> None:
        """Test TranscriptionResult with optional confidence"""
        result: TranscriptionResult = TranscriptionResult(
            text="Test text",
            language="en",
            confidence=None,
        )
        assert result.confidence is None

    def test_transcription_result_empty_text(self) -> None:
        """Test TranscriptionResult with empty text (silent audio)"""
        result: TranscriptionResult = TranscriptionResult(
            text="",
            language="unknown",
            confidence=0.0,
        )
        assert result.text == ""
        assert result.language == "unknown"


class TestWhisperServiceConfiguration:
    """Test WhisperService configuration options"""

    def test_default_model_is_whisper_1(self) -> None:
        """Test default Whisper model is whisper-1"""
        with patch("app.services.whisper_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_WHISPER_MODEL = "whisper-1"
            service: WhisperService = WhisperService()
            assert service.model == "whisper-1"

    def test_custom_model_configuration(self) -> None:
        """Test custom Whisper model can be configured"""
        with patch("app.services.whisper_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_WHISPER_MODEL = "whisper-large-v3"
            service: WhisperService = WhisperService()
            assert service.model == "whisper-large-v3"
