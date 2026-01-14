"""
Whisper transcription service for audio-to-text conversion

Issue #175: Audio Extraction and Whisper Transcription
Uses OpenAI Whisper API for transcribing Snapchat Spotlight audio content.

Supports Dutch (nl) and English (en) language transcription as required
by EFCSN compliance (ADR 0005).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhisperServiceError(Exception):
    """Exception raised for Whisper service errors"""

    pass


@dataclass
class TranscriptionResult:
    """Result of audio transcription"""

    text: str
    language: str
    confidence: Optional[float]


class WhisperService:
    """Service for transcribing audio using OpenAI Whisper API

    This service provides audio transcription functionality for Snapchat Spotlight
    videos. It uses the OpenAI Whisper API to convert audio to text, supporting
    multiple languages including Dutch (nl) and English (en).

    Attributes:
        SUPPORTED_LANGUAGES: List of supported language codes
        model: The Whisper model to use for transcription

    Example:
        >>> service = WhisperService()
        >>> result = await service.transcribe_audio("/path/to/audio.mp3")
        >>> print(result.text)
        "Dit is een voorbeeld transcriptie."
    """

    SUPPORTED_LANGUAGES: list[str] = ["nl", "en", "de", "fr", "es"]

    def __init__(self) -> None:
        """Initialize WhisperService with OpenAI API key

        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please configure it in your .env file."
            )
        self.api_key: str = settings.OPENAI_API_KEY
        self.model: str = settings.OPENAI_WHISPER_MODEL
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Lazily initialize and return OpenAI client"""
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    async def transcribe_audio(
        self,
        audio_file_path: str,
        language_hint: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio file to text using OpenAI Whisper API

        Args:
            audio_file_path: Path to the audio file to transcribe
            language_hint: Optional language code hint (e.g., 'nl', 'en')
                          to improve transcription accuracy

        Returns:
            TranscriptionResult containing the transcribed text, detected
            language, and confidence score

        Raises:
            WhisperServiceError: If audio file not found or transcription fails
        """
        # Validate file exists
        audio_path: Path = Path(audio_file_path)
        if not audio_path.exists():
            raise WhisperServiceError(f"Audio file not found: {audio_file_path}")

        try:
            result: TranscriptionResult = await self._call_whisper_api(audio_path, language_hint)
            logger.info(
                f"Successfully transcribed audio: {audio_file_path}, "
                f"language: {result.language}, confidence: {result.confidence}"
            )
            return result
        except WhisperServiceError:
            raise
        except Exception as e:
            logger.error(f"Transcription failed for {audio_file_path}: {e}")
            raise WhisperServiceError(f"Transcription failed: {str(e)}") from e

    async def _call_whisper_api(
        self,
        audio_path: Path,
        language_hint: Optional[str] = None,
    ) -> TranscriptionResult:
        """Make the actual API call to OpenAI Whisper

        Args:
            audio_path: Path to the audio file
            language_hint: Optional language code hint

        Returns:
            TranscriptionResult with transcription data
        """
        with open(audio_path, "rb") as audio_file:
            # Call Whisper API with explicit parameters
            if language_hint and language_hint in self.SUPPORTED_LANGUAGES:
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model,
                    response_format="verbose_json",
                    language=language_hint,
                )
            else:
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model,
                    response_format="verbose_json",
                )

        # Extract results
        text: str = response.text if hasattr(response, "text") else ""
        language: str = (
            response.language if hasattr(response, "language") else language_hint or "unknown"
        )

        # Calculate confidence from segments if available
        confidence: Optional[float] = self._calculate_confidence(response)

        return TranscriptionResult(
            text=text,
            language=language,
            confidence=confidence,
        )

    def _calculate_confidence(self, response: object) -> Optional[float]:
        """Calculate average confidence from transcription segments

        Args:
            response: Whisper API response object

        Returns:
            Average confidence score (0.0-1.0) or None if not available
        """
        if not hasattr(response, "segments"):
            return None

        segments = response.segments
        if not segments:
            return None

        # Calculate weighted average confidence based on segment duration
        total_duration: float = 0.0
        weighted_confidence: float = 0.0

        for segment in segments:
            if hasattr(segment, "no_speech_prob") and hasattr(segment, "end"):
                duration: float = segment.end - getattr(segment, "start", 0)
                # Convert no_speech_prob to speech confidence
                speech_confidence: float = 1.0 - segment.no_speech_prob
                weighted_confidence += speech_confidence * duration
                total_duration += duration

        if total_duration > 0:
            return round(weighted_confidence / total_duration, 4)

        return None


# Singleton instance for use across the application
whisper_service: Optional[WhisperService] = None


def get_whisper_service() -> WhisperService:
    """Get or create WhisperService singleton instance

    Returns:
        WhisperService instance

    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    global whisper_service
    if whisper_service is None:
        whisper_service = WhisperService()
    return whisper_service
