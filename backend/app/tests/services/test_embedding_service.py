"""
Tests for embedding service using OpenAI text-embedding-3-small

Following TDD approach: Tests written FIRST before implementation
Issue #176: LLM-based Claim Extraction - Embedding generation for similarity search

Tests embedding generation and caching using text-embedding-3-small model.
"""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingServiceError,
)


class TestEmbeddingServiceInitialization:
    """Test EmbeddingService initialization"""

    def test_service_initialization_with_api_key(self) -> None:
        """Test service initializes correctly with API key"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
            mock_settings.OPENAI_EMBEDDING_DIMENSIONS = 1536
            service: EmbeddingService = EmbeddingService()
            assert service is not None
            assert isinstance(service, EmbeddingService)

    def test_service_raises_error_without_api_key(self) -> None:
        """Test service raises error when API key is missing"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                EmbeddingService()

    def test_service_uses_configured_model(self) -> None:
        """Test service uses the configured embedding model"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
            mock_settings.OPENAI_EMBEDDING_DIMENSIONS = 3072
            service: EmbeddingService = EmbeddingService()
            assert service.model == "text-embedding-3-large"

    def test_service_has_correct_dimensions(self) -> None:
        """Test service uses correct embedding dimensions"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
            mock_settings.OPENAI_EMBEDDING_DIMENSIONS = 1536
            service: EmbeddingService = EmbeddingService()
            assert service.dimensions == 1536


class TestEmbeddingGeneration:
    """Test EmbeddingService embedding generation"""

    @pytest.fixture
    def embedding_service(self) -> Generator[EmbeddingService, None, None]:
        """Provide EmbeddingService instance with mocked settings"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
            mock_settings.OPENAI_EMBEDDING_DIMENSIONS = 1536
            service: EmbeddingService = EmbeddingService()
            yield service

    @pytest.fixture
    def mock_embedding_response(self) -> list[float]:
        """Provide a mock embedding vector"""
        # Return a 1536-dimensional vector (text-embedding-3-small dimension)
        return [0.1 * (i % 10) for i in range(1536)]

    @pytest.mark.asyncio
    async def test_generate_embedding_for_text(
        self, embedding_service: EmbeddingService, mock_embedding_response: list[float]
    ) -> None:
        """Test generating embedding for text content"""
        # Arrange
        text: str = "Vaccines cause autism according to some studies."

        mock_response: Mock = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding_response)]

        with patch.object(
            embedding_service, "_call_embedding_api", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = mock_embedding_response

            # Act
            embedding: list[float] = await embedding_service.generate_embedding(text)

            # Assert
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_for_dutch_text(
        self, embedding_service: EmbeddingService, mock_embedding_response: list[float]
    ) -> None:
        """Test generating embedding for Dutch text content"""
        # Arrange
        text: str = "Vaccins veroorzaken autisme volgens sommige studies."

        with patch.object(
            embedding_service, "_call_embedding_api", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = mock_embedding_response

            # Act
            embedding: list[float] = await embedding_service.generate_embedding(text)

            # Assert
            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service: EmbeddingService) -> None:
        """Test generating embedding for empty text raises error"""
        # Arrange
        text: str = ""

        # Act & Assert
        with pytest.raises(EmbeddingServiceError, match="empty"):
            await embedding_service.generate_embedding(text)

    @pytest.mark.asyncio
    async def test_generate_embedding_whitespace_only(
        self, embedding_service: EmbeddingService
    ) -> None:
        """Test generating embedding for whitespace-only text raises error"""
        # Arrange
        text: str = "   \n\t  "

        # Act & Assert
        with pytest.raises(EmbeddingServiceError, match="empty"):
            await embedding_service.generate_embedding(text)

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, embedding_service: EmbeddingService) -> None:
        """Test embedding generation handles API errors"""
        # Arrange
        text: str = "Test text for embedding"

        with patch.object(
            embedding_service, "_call_embedding_api", new_callable=AsyncMock
        ) as mock_call:
            mock_call.side_effect = Exception("OpenAI API error")

            # Act & Assert
            with pytest.raises(EmbeddingServiceError, match="Embedding generation failed"):
                await embedding_service.generate_embedding(text)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(
        self, embedding_service: EmbeddingService, mock_embedding_response: list[float]
    ) -> None:
        """Test generating embeddings for multiple texts in batch"""
        # Arrange
        texts: list[str] = [
            "First claim about vaccines",
            "Second claim about climate",
            "Third claim about 5G",
        ]

        with patch.object(
            embedding_service, "_call_embedding_api_batch", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = [mock_embedding_response for _ in texts]

            # Act
            embeddings: list[list[float]] = await embedding_service.generate_embeddings_batch(texts)

            # Assert
            assert len(embeddings) == 3
            assert all(len(e) == 1536 for e in embeddings)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_empty_list(
        self, embedding_service: EmbeddingService
    ) -> None:
        """Test batch embedding with empty list returns empty list"""
        # Arrange
        texts: list[str] = []

        # Act
        embeddings: list[list[float]] = await embedding_service.generate_embeddings_batch(texts)

        # Assert
        assert embeddings == []


class TestEmbeddingNormalization:
    """Test embedding normalization for cosine similarity"""

    @pytest.fixture
    def embedding_service(self) -> Generator[EmbeddingService, None, None]:
        """Provide EmbeddingService instance"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
            mock_settings.OPENAI_EMBEDDING_DIMENSIONS = 1536
            yield EmbeddingService()

    def test_normalize_embedding(self, embedding_service: EmbeddingService) -> None:
        """Test embedding normalization produces unit vector"""
        # Arrange
        embedding: list[float] = [3.0, 4.0, 0.0]  # Should normalize to [0.6, 0.8, 0.0]

        # Act
        normalized: list[float] = embedding_service.normalize_embedding(embedding)

        # Assert
        # Check it's a unit vector (magnitude ≈ 1.0)
        magnitude: float = sum(x**2 for x in normalized) ** 0.5
        assert abs(magnitude - 1.0) < 0.0001

    def test_normalize_embedding_already_normalized(
        self, embedding_service: EmbeddingService
    ) -> None:
        """Test normalizing already normalized embedding"""
        # Arrange - already a unit vector
        embedding: list[float] = [0.6, 0.8, 0.0]

        # Act
        normalized: list[float] = embedding_service.normalize_embedding(embedding)

        # Assert
        magnitude: float = sum(x**2 for x in normalized) ** 0.5
        assert abs(magnitude - 1.0) < 0.0001

    def test_normalize_zero_vector(self, embedding_service: EmbeddingService) -> None:
        """Test normalizing zero vector returns zero vector"""
        # Arrange
        embedding: list[float] = [0.0, 0.0, 0.0]

        # Act
        normalized: list[float] = embedding_service.normalize_embedding(embedding)

        # Assert
        assert normalized == [0.0, 0.0, 0.0]


class TestCosineSimilarity:
    """Test cosine similarity calculations"""

    @pytest.fixture
    def embedding_service(self) -> Generator[EmbeddingService, None, None]:
        """Provide EmbeddingService instance"""
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
            mock_settings.OPENAI_EMBEDDING_DIMENSIONS = 1536
            yield EmbeddingService()

    def test_cosine_similarity_identical_vectors(self, embedding_service: EmbeddingService) -> None:
        """Test cosine similarity of identical vectors is 1.0"""
        # Arrange
        embedding: list[float] = [0.5, 0.5, 0.5, 0.5]

        # Act
        similarity: float = embedding_service.cosine_similarity(embedding, embedding)

        # Assert
        assert abs(similarity - 1.0) < 0.0001

    def test_cosine_similarity_orthogonal_vectors(
        self, embedding_service: EmbeddingService
    ) -> None:
        """Test cosine similarity of orthogonal vectors is 0.0"""
        # Arrange
        embedding1: list[float] = [1.0, 0.0, 0.0, 0.0]
        embedding2: list[float] = [0.0, 1.0, 0.0, 0.0]

        # Act
        similarity: float = embedding_service.cosine_similarity(embedding1, embedding2)

        # Assert
        assert abs(similarity - 0.0) < 0.0001

    def test_cosine_similarity_opposite_vectors(self, embedding_service: EmbeddingService) -> None:
        """Test cosine similarity of opposite vectors is -1.0"""
        # Arrange
        embedding1: list[float] = [1.0, 0.0, 0.0, 0.0]
        embedding2: list[float] = [-1.0, 0.0, 0.0, 0.0]

        # Act
        similarity: float = embedding_service.cosine_similarity(embedding1, embedding2)

        # Assert
        assert abs(similarity - (-1.0)) < 0.0001

    def test_cosine_similarity_similar_vectors(self, embedding_service: EmbeddingService) -> None:
        """Test cosine similarity of similar vectors is high"""
        # Arrange
        embedding1: list[float] = [0.8, 0.1, 0.1, 0.0]
        embedding2: list[float] = [0.7, 0.2, 0.1, 0.0]

        # Act
        similarity: float = embedding_service.cosine_similarity(embedding1, embedding2)

        # Assert - should be high but not 1.0
        assert similarity > 0.9
        assert similarity < 1.0
