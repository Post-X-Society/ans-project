"""
Tests for audio extraction service using yt-dlp

Following TDD approach: Tests written FIRST before implementation
Issue #175: Audio Extraction and Whisper Transcription
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.audio_extraction_service import (
    AudioExtractionError,
    AudioExtractionResult,
    AudioExtractionService,
)


class TestAudioExtractionServiceInitialization:
    """Test AudioExtractionService initialization"""

    def test_audio_extraction_service_initialization(self) -> None:
        """Test AudioExtractionService initializes correctly"""
        with patch("pathlib.Path.mkdir"):
            service: AudioExtractionService = AudioExtractionService()
            assert service is not None
            assert isinstance(service, AudioExtractionService)

    def test_audio_extraction_service_has_media_directory(self) -> None:
        """Test AudioExtractionService has configurable media directory"""
        with patch.dict("os.environ", {"MEDIA_DIR": "/tmp/test_media"}):
            with patch("pathlib.Path.mkdir"):
                service: AudioExtractionService = AudioExtractionService()
                assert service.media_dir is not None

    def test_audio_extraction_service_creates_audio_directory(self) -> None:
        """Test AudioExtractionService creates audio output directory"""
        with patch.dict("os.environ", {"MEDIA_DIR": "/tmp/test_media"}):
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                service: AudioExtractionService = AudioExtractionService()
                # Verify directory creation was called
                assert service.audio_dir is not None
                mock_mkdir.assert_called_once()


class TestAudioExtractionFromVideo:
    """Test audio extraction from video files"""

    @pytest.fixture
    def audio_service(self) -> AudioExtractionService:
        """Provide AudioExtractionService instance"""
        with patch.dict("os.environ", {"MEDIA_DIR": "/tmp/test_media"}):
            with patch("pathlib.Path.mkdir"):
                return AudioExtractionService()

    @pytest.mark.asyncio
    async def test_extract_audio_from_video_file_success(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test successful audio extraction from local video file"""
        # Arrange
        video_path: str = "/tmp/test_video.mp4"
        spotlight_id: str = "test_spotlight_123"
        expected_audio_path: str = f"/tmp/test_media/audio/{spotlight_id}.mp3"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(audio_service, "_run_ffmpeg", new_callable=AsyncMock) as mock_ffmpeg:
                mock_ffmpeg.return_value = expected_audio_path

                # Mock the stat call to return file size
                with patch("pathlib.Path.stat") as mock_stat:
                    mock_stat.return_value.st_size = 1024

                    # Act
                    result: AudioExtractionResult = await audio_service.extract_audio_from_video(
                        video_path=video_path, spotlight_id=spotlight_id
                    )

                    # Assert
                    assert result.audio_path == expected_audio_path
                    assert result.format == "mp3"
                    assert result.file_size_bytes == 1024
                    mock_ffmpeg.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_audio_video_file_not_found(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test audio extraction fails when video file not found"""
        # Arrange
        non_existent_video: str = "/tmp/non_existent_video.mp4"
        spotlight_id: str = "test_spotlight_456"

        # Act & Assert
        with pytest.raises(AudioExtractionError, match="Video file not found"):
            await audio_service.extract_audio_from_video(
                video_path=non_existent_video, spotlight_id=spotlight_id
            )

    @pytest.mark.asyncio
    async def test_extract_audio_ffmpeg_error(self, audio_service: AudioExtractionService) -> None:
        """Test audio extraction handles FFmpeg errors gracefully"""
        # Arrange
        video_path: str = "/tmp/test_video.mp4"
        spotlight_id: str = "test_spotlight_789"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(audio_service, "_run_ffmpeg", new_callable=AsyncMock) as mock_ffmpeg:
                mock_ffmpeg.side_effect = Exception("FFmpeg processing error")

                # Act & Assert
                with pytest.raises(AudioExtractionError, match="Audio extraction failed"):
                    await audio_service.extract_audio_from_video(
                        video_path=video_path, spotlight_id=spotlight_id
                    )


class TestAudioExtractionFromUrl:
    """Test audio extraction from Snapchat Spotlight URLs using yt-dlp"""

    @pytest.fixture
    def audio_service(self) -> AudioExtractionService:
        """Provide AudioExtractionService instance"""
        with patch.dict("os.environ", {"MEDIA_DIR": "/tmp/test_media"}):
            with patch("pathlib.Path.mkdir"):
                return AudioExtractionService()

    @pytest.mark.asyncio
    async def test_extract_audio_from_url_success(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test successful audio extraction from Spotlight URL"""
        # Arrange
        spotlight_url: str = "https://www.snapchat.com/spotlight/test123"
        spotlight_id: str = "test123"
        expected_audio_path: str = f"/tmp/test_media/audio/{spotlight_id}.mp3"

        with patch.object(audio_service, "_run_ytdlp", new_callable=AsyncMock) as mock_ytdlp:
            mock_ytdlp.return_value = expected_audio_path

            # Act
            result: AudioExtractionResult = await audio_service.extract_audio_from_url(
                spotlight_url=spotlight_url, spotlight_id=spotlight_id
            )

            # Assert
            assert result.audio_path == expected_audio_path
            assert result.format == "mp3"
            mock_ytdlp.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_audio_from_url_invalid_url(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test audio extraction fails with invalid URL"""
        # Arrange
        invalid_url: str = "not-a-valid-url"
        spotlight_id: str = "test456"

        # Act & Assert
        with pytest.raises(AudioExtractionError, match="Invalid URL"):
            await audio_service.extract_audio_from_url(
                spotlight_url=invalid_url, spotlight_id=spotlight_id
            )

    @pytest.mark.asyncio
    async def test_extract_audio_from_url_ytdlp_error(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test audio extraction handles yt-dlp errors gracefully"""
        # Arrange
        spotlight_url: str = "https://www.snapchat.com/spotlight/test789"
        spotlight_id: str = "test789"

        with patch.object(audio_service, "_run_ytdlp", new_callable=AsyncMock) as mock_ytdlp:
            mock_ytdlp.side_effect = Exception("yt-dlp download failed")

            # Act & Assert
            with pytest.raises(AudioExtractionError, match="Audio extraction failed"):
                await audio_service.extract_audio_from_url(
                    spotlight_url=spotlight_url, spotlight_id=spotlight_id
                )

    @pytest.mark.asyncio
    async def test_extract_audio_from_url_network_error(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test audio extraction handles network errors"""
        # Arrange
        spotlight_url: str = "https://www.snapchat.com/spotlight/network_error"
        spotlight_id: str = "network_error"

        with patch.object(audio_service, "_run_ytdlp", new_callable=AsyncMock) as mock_ytdlp:
            mock_ytdlp.side_effect = ConnectionError("Network unreachable")

            # Act & Assert
            with pytest.raises(AudioExtractionError):
                await audio_service.extract_audio_from_url(
                    spotlight_url=spotlight_url, spotlight_id=spotlight_id
                )


class TestAudioExtractionResult:
    """Test AudioExtractionResult dataclass"""

    def test_audio_extraction_result_creation(self) -> None:
        """Test AudioExtractionResult can be created with all fields"""
        result: AudioExtractionResult = AudioExtractionResult(
            audio_path="/tmp/audio/test.mp3",
            format="mp3",
            duration_seconds=120.5,
            file_size_bytes=1024000,
        )
        assert result.audio_path == "/tmp/audio/test.mp3"
        assert result.format == "mp3"
        assert result.duration_seconds == 120.5
        assert result.file_size_bytes == 1024000

    def test_audio_extraction_result_optional_fields(self) -> None:
        """Test AudioExtractionResult with optional fields"""
        result: AudioExtractionResult = AudioExtractionResult(
            audio_path="/tmp/audio/test.mp3",
            format="mp3",
            duration_seconds=None,
            file_size_bytes=None,
        )
        assert result.duration_seconds is None
        assert result.file_size_bytes is None


class TestAudioCleanup:
    """Test audio file cleanup functionality"""

    @pytest.fixture
    def audio_service(self) -> AudioExtractionService:
        """Provide AudioExtractionService instance"""
        with patch.dict("os.environ", {"MEDIA_DIR": "/tmp/test_media"}):
            with patch("pathlib.Path.mkdir"):
                return AudioExtractionService()

    @pytest.mark.asyncio
    async def test_cleanup_audio_file(self, audio_service: AudioExtractionService) -> None:
        """Test cleanup removes audio file after processing"""
        # Arrange
        audio_path: str = "/tmp/test_media/audio/test_cleanup.mp3"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.unlink") as mock_unlink:
                # Act
                await audio_service.cleanup_audio_file(audio_path)

                # Assert
                mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_audio_file_not_found(
        self, audio_service: AudioExtractionService
    ) -> None:
        """Test cleanup handles non-existent file gracefully"""
        # Arrange
        audio_path: str = "/tmp/test_media/audio/non_existent.mp3"

        # Act - Should not raise exception
        await audio_service.cleanup_audio_file(audio_path)


class TestSupportedFormats:
    """Test supported audio formats"""

    @pytest.fixture
    def audio_service(self) -> AudioExtractionService:
        """Provide AudioExtractionService instance"""
        with patch.dict("os.environ", {"MEDIA_DIR": "/tmp/test_media"}):
            with patch("pathlib.Path.mkdir"):
                return AudioExtractionService()

    def test_default_output_format_is_mp3(self, audio_service: AudioExtractionService) -> None:
        """Test default audio output format is MP3"""
        assert audio_service.default_format == "mp3"

    def test_supported_formats_include_mp3_wav(self, audio_service: AudioExtractionService) -> None:
        """Test supported formats include common audio formats"""
        supported: list[str] = audio_service.SUPPORTED_FORMATS
        assert "mp3" in supported
        assert "wav" in supported
