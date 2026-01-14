"""
Embedding service for generating vector embeddings using OpenAI text-embedding-3-small

Issue #176: LLM-based Claim Extraction - Embedding generation for similarity search

This service generates vector embeddings for claim text using OpenAI's
text-embedding-3-small model. These embeddings are used for:
- Deduplication of similar claims
- Similarity search for finding related fact-checks

The embeddings are 1536-dimensional vectors suitable for pgvector storage.
"""

import logging
import math
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Exception raised for embedding service errors"""

    pass


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API

    This service uses OpenAI's text-embedding-3-small model to generate
    vector embeddings for text content. The embeddings are used for
    similarity search and claim deduplication.

    Attributes:
        model: The embedding model to use
        dimensions: Dimensionality of the embeddings

    Example:
        >>> service = EmbeddingService()
        >>> embedding = await service.generate_embedding("Vaccines cause autism")
        >>> print(len(embedding))
        1536
    """

    def __init__(self) -> None:
        """Initialize EmbeddingService with OpenAI API key

        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please configure it in your .env file."
            )
        self.api_key: str = settings.OPENAI_API_KEY
        self.model: str = settings.OPENAI_EMBEDDING_MODEL
        self.dimensions: int = settings.OPENAI_EMBEDDING_DIMENSIONS
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazily initialize and return AsyncOpenAI client"""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text using OpenAI API

        Args:
            text: The text to generate embedding for

        Returns:
            List of floats representing the embedding vector (1536 dimensions)

        Raises:
            EmbeddingServiceError: If text is empty or API call fails
        """
        # Validate input
        if not text or not text.strip():
            raise EmbeddingServiceError("Cannot generate embedding for empty text")

        try:
            embedding: list[float] = await self._call_embedding_api(text.strip())

            logger.debug(
                f"Generated embedding for text ({len(text)} chars), "
                f"dimensions: {len(embedding)}"
            )

            return embedding

        except EmbeddingServiceError:
            raise
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingServiceError(f"Embedding generation failed: {str(e)}") from e

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a single batch request

        This is more efficient than calling generate_embedding multiple times
        as it makes a single API call for all texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            EmbeddingServiceError: If API call fails
        """
        if not texts:
            return []

        # Filter empty texts and track indices
        valid_texts: list[str] = []
        valid_indices: list[int] = []

        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text.strip())
                valid_indices.append(i)

        if not valid_texts:
            return [[] for _ in texts]

        try:
            embeddings: list[list[float]] = await self._call_embedding_api_batch(valid_texts)

            # Reconstruct result with empty vectors for invalid texts
            result: list[list[float]] = [[] for _ in texts]
            for i, embedding in enumerate(embeddings):
                result[valid_indices[i]] = embedding

            logger.info(
                f"Generated {len(embeddings)} embeddings in batch " f"(total texts: {len(texts)})"
            )

            return result

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise EmbeddingServiceError(f"Batch embedding generation failed: {str(e)}") from e

    async def _call_embedding_api(self, text: str) -> list[float]:
        """Make the actual API call to OpenAI embeddings API

        Args:
            text: The text to embed

        Returns:
            The embedding vector
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        return response.data[0].embedding

    async def _call_embedding_api_batch(self, texts: list[str]) -> list[list[float]]:
        """Make batch API call to OpenAI embeddings API

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def normalize_embedding(self, embedding: list[float]) -> list[float]:
        """Normalize embedding to unit vector for cosine similarity

        Normalizing embeddings allows for faster cosine similarity calculation
        using dot product.

        Args:
            embedding: The embedding vector to normalize

        Returns:
            Normalized embedding vector (unit vector)
        """
        magnitude: float = math.sqrt(sum(x**2 for x in embedding))

        if magnitude == 0:
            return embedding

        return [x / magnitude for x in embedding]

    def cosine_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        # Calculate magnitudes
        mag1: float = math.sqrt(sum(x**2 for x in embedding1))
        mag2: float = math.sqrt(sum(x**2 for x in embedding2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        # Calculate dot product
        dot_product: float = sum(a * b for a, b in zip(embedding1, embedding2))

        return dot_product / (mag1 * mag2)


# Singleton instance for use across the application
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create EmbeddingService singleton instance

    Returns:
        EmbeddingService instance

    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
