"""
Audio extraction service for Snapchat Spotlight videos

Issue #175: Audio Extraction and Whisper Transcription
Uses yt-dlp for downloading audio from Spotlight URLs and FFmpeg for
extracting audio from local video files.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class AudioExtractionError(Exception):
    """Exception raised for audio extraction errors"""

    pass


@dataclass
class AudioExtractionResult:
    """Result of audio extraction"""

    audio_path: str
    format: str
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]


class AudioExtractionService:
    """Service for extracting audio from video files and Spotlight URLs

    This service provides audio extraction functionality for Snapchat Spotlight
    content. It uses FFmpeg for extracting audio from local video files and
    yt-dlp for downloading audio directly from Spotlight URLs.

    Attributes:
        SUPPORTED_FORMATS: List of supported audio output formats
        default_format: Default audio output format (mp3)
        media_dir: Base directory for media files
        audio_dir: Directory for extracted audio files

    Example:
        >>> service = AudioExtractionService()
        >>> result = await service.extract_audio_from_video(
        ...     "/path/to/video.mp4", "spotlight_123"
        ... )
        >>> print(result.audio_path)
        "/app/media/audio/spotlight_123.mp3"
    """

    SUPPORTED_FORMATS: list[str] = ["mp3", "wav", "m4a", "ogg"]

    def __init__(self) -> None:
        """Initialize AudioExtractionService with media directories"""
        self.media_dir: Path = Path(os.getenv("MEDIA_DIR", "/app/media/spotlight_videos"))
        self.audio_dir: Path = self.media_dir / "audio"
        self.default_format: str = "mp3"

        # Create audio directory if it doesn't exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AudioExtractionService initialized with audio_dir: {self.audio_dir}")

    async def extract_audio_from_video(
        self,
        video_path: str,
        spotlight_id: str,
        output_format: Optional[str] = None,
    ) -> AudioExtractionResult:
        """Extract audio from a local video file using FFmpeg

        Args:
            video_path: Path to the source video file
            spotlight_id: Unique identifier for the spotlight content
            output_format: Desired audio format (default: mp3)

        Returns:
            AudioExtractionResult containing the extracted audio path and metadata

        Raises:
            AudioExtractionError: If video file not found or extraction fails
        """
        video_file: Path = Path(video_path)

        # Validate video file exists
        if not video_file.exists():
            raise AudioExtractionError(f"Video file not found: {video_path}")

        # Determine output format
        audio_format: str = output_format or self.default_format
        if audio_format not in self.SUPPORTED_FORMATS:
            raise AudioExtractionError(
                f"Unsupported audio format: {audio_format}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        # Generate output path
        output_path: str = str(self.audio_dir / f"{spotlight_id}.{audio_format}")

        try:
            await self._run_ffmpeg(video_path, output_path, audio_format)
            logger.info(f"Successfully extracted audio from {video_path} to {output_path}")

            # Get file metadata
            audio_file: Path = Path(output_path)
            file_size: Optional[int] = audio_file.stat().st_size if audio_file.exists() else None

            return AudioExtractionResult(
                audio_path=output_path,
                format=audio_format,
                duration_seconds=None,  # Could be extracted from ffprobe if needed
                file_size_bytes=file_size,
            )
        except AudioExtractionError:
            raise
        except Exception as e:
            logger.error(f"Audio extraction failed for {video_path}: {e}")
            raise AudioExtractionError(f"Audio extraction failed: {str(e)}") from e

    async def extract_audio_from_url(
        self,
        spotlight_url: str,
        spotlight_id: str,
        output_format: Optional[str] = None,
    ) -> AudioExtractionResult:
        """Extract audio directly from a Spotlight URL using yt-dlp

        Args:
            spotlight_url: URL of the Snapchat Spotlight content
            spotlight_id: Unique identifier for the spotlight content
            output_format: Desired audio format (default: mp3)

        Returns:
            AudioExtractionResult containing the extracted audio path and metadata

        Raises:
            AudioExtractionError: If URL is invalid or extraction fails
        """
        # Validate URL
        if not self._is_valid_url(spotlight_url):
            raise AudioExtractionError(f"Invalid URL: {spotlight_url}")

        # Determine output format
        audio_format: str = output_format or self.default_format
        if audio_format not in self.SUPPORTED_FORMATS:
            raise AudioExtractionError(
                f"Unsupported audio format: {audio_format}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        # Generate output path
        output_path: str = str(self.audio_dir / f"{spotlight_id}.{audio_format}")

        try:
            await self._run_ytdlp(spotlight_url, output_path, audio_format)
            logger.info(f"Successfully extracted audio from {spotlight_url} to {output_path}")

            # Get file metadata
            audio_file: Path = Path(output_path)
            file_size: Optional[int] = audio_file.stat().st_size if audio_file.exists() else None

            return AudioExtractionResult(
                audio_path=output_path,
                format=audio_format,
                duration_seconds=None,
                file_size_bytes=file_size,
            )
        except AudioExtractionError:
            raise
        except ConnectionError as e:
            logger.error(f"Network error extracting audio from {spotlight_url}: {e}")
            raise AudioExtractionError(f"Network error during audio extraction: {str(e)}") from e
        except Exception as e:
            logger.error(f"Audio extraction failed for {spotlight_url}: {e}")
            raise AudioExtractionError(f"Audio extraction failed: {str(e)}") from e

    async def cleanup_audio_file(self, audio_path: str) -> None:
        """Remove an audio file after processing

        Args:
            audio_path: Path to the audio file to remove

        Note:
            This method does not raise exceptions if the file doesn't exist,
            allowing for safe cleanup in error handling scenarios.
        """
        audio_file: Path = Path(audio_path)
        if audio_file.exists():
            try:
                audio_file.unlink()
                logger.info(f"Cleaned up audio file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup audio file {audio_path}: {e}")

    async def _run_ffmpeg(
        self,
        video_path: str,
        output_path: str,
        audio_format: str,
    ) -> str:
        """Run FFmpeg to extract audio from video

        Args:
            video_path: Path to input video file
            output_path: Path for output audio file
            audio_format: Target audio format

        Returns:
            Path to the extracted audio file

        Raises:
            AudioExtractionError: If FFmpeg process fails
        """
        # Build FFmpeg command
        cmd: list[str] = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",  # No video
            "-acodec",
            self._get_audio_codec(audio_format),
            "-y",  # Overwrite output file
            output_path,
        ]

        logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")

        # Run FFmpeg asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_message: str = stderr.decode() if stderr else "Unknown error"
            raise AudioExtractionError(
                f"FFmpeg failed with exit code {process.returncode}: {error_message}"
            )

        return output_path

    async def _run_ytdlp(
        self,
        url: str,
        output_path: str,
        audio_format: str,
    ) -> str:
        """Run yt-dlp to extract audio from URL

        Args:
            url: Source URL to download from
            output_path: Path for output audio file
            audio_format: Target audio format

        Returns:
            Path to the extracted audio file

        Raises:
            AudioExtractionError: If yt-dlp process fails
        """
        # Build yt-dlp command
        cmd: list[str] = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format",
            audio_format,
            "-o",
            output_path.replace(f".{audio_format}", ".%(ext)s"),
            "--no-playlist",
            url,
        ]

        logger.debug(f"Running yt-dlp command: {' '.join(cmd)}")

        # Run yt-dlp asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_message: str = stderr.decode() if stderr else "Unknown error"
            raise AudioExtractionError(
                f"yt-dlp failed with exit code {process.returncode}: {error_message}"
            )

        return output_path

    def _get_audio_codec(self, audio_format: str) -> str:
        """Get the appropriate audio codec for FFmpeg based on format

        Args:
            audio_format: Target audio format

        Returns:
            FFmpeg audio codec name
        """
        codec_map: dict[str, str] = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "m4a": "aac",
            "ogg": "libvorbis",
        }
        return codec_map.get(audio_format, "libmp3lame")

    def _is_valid_url(self, url: str) -> bool:
        """Validate if a string is a valid URL

        Args:
            url: String to validate

        Returns:
            True if valid URL, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ("http", "https"), result.netloc])
        except Exception:
            return False


# Singleton instance for use across the application
audio_extraction_service: Optional[AudioExtractionService] = None


def get_audio_extraction_service() -> AudioExtractionService:
    """Get or create AudioExtractionService singleton instance

    Returns:
        AudioExtractionService instance
    """
    global audio_extraction_service
    if audio_extraction_service is None:
        audio_extraction_service = AudioExtractionService()
    return audio_extraction_service
