"""
Tests for claim similarity service using pgvector

Following TDD approach: Tests written FIRST before implementation
Issue #176: LLM-based Claim Extraction - Deduplication using vector similarity

Tests claim similarity search and deduplication using pgvector cosine similarity.
"""

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.services.claim_similarity_service import (
    ClaimSimilarityService,
    SimilarClaim,
)


class TestClaimSimilarityServiceInitialization:
    """Test ClaimSimilarityService initialization"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, db_session: AsyncSession) -> None:
        """Test service initializes correctly with database session"""
        service: ClaimSimilarityService = ClaimSimilarityService(db_session)
        assert service is not None
        assert isinstance(service, ClaimSimilarityService)

    @pytest.mark.asyncio
    async def test_service_uses_configured_threshold(self, db_session: AsyncSession) -> None:
        """Test service uses configured similarity threshold"""
        with patch("app.services.claim_similarity_service.settings") as mock_settings:
            mock_settings.CLAIM_SIMILARITY_THRESHOLD = 0.90
            service: ClaimSimilarityService = ClaimSimilarityService(db_session)
            assert service.default_threshold == 0.90


class TestSimilarClaim:
    """Test SimilarClaim dataclass"""

    def test_similar_claim_creation(self) -> None:
        """Test SimilarClaim can be created with all fields"""
        claim_id = uuid4()
        similar: SimilarClaim = SimilarClaim(
            claim_id=claim_id,
            content="Vaccines cause autism",
            similarity=0.95,
        )
        assert similar.claim_id == claim_id
        assert similar.content == "Vaccines cause autism"
        assert similar.similarity == 0.95


class TestFindSimilarClaims:
    """Test finding similar claims in database"""

    @pytest.fixture
    def similarity_service(self, db_session: AsyncSession) -> ClaimSimilarityService:
        """Provide ClaimSimilarityService instance"""
        with patch("app.services.claim_similarity_service.settings") as mock_settings:
            mock_settings.CLAIM_SIMILARITY_THRESHOLD = 0.85
            return ClaimSimilarityService(db_session)

    @pytest.fixture
    def mock_embedding(self) -> list[float]:
        """Provide a mock embedding vector"""
        return [0.1 * (i % 10) for i in range(1536)]

    @pytest.fixture
    def mock_similar_embedding(self) -> list[float]:
        """Provide a similar mock embedding vector"""
        # Slightly different from mock_embedding
        return [0.1 * (i % 10) + 0.01 for i in range(1536)]

    @pytest.fixture
    def mock_different_embedding(self) -> list[float]:
        """Provide a different mock embedding vector"""
        # Very different from mock_embedding
        return [0.9 - 0.1 * (i % 10) for i in range(1536)]

    @pytest.mark.asyncio
    async def test_find_similar_claims_returns_matches(
        self,
        similarity_service: ClaimSimilarityService,
        db_session: AsyncSession,
        mock_embedding: list[float],
    ) -> None:
        """Test finding similar claims returns matching claims"""
        # Arrange - Create test claims with embeddings
        claim1: Claim = Claim(
            content="Vaccines cause autism",
            source="test",
            embedding=mock_embedding,
        )
        db_session.add(claim1)
        await db_session.commit()
        await db_session.refresh(claim1)

        # Act - Search with the same embedding (should match perfectly)
        # Note: We mock the database query since SQLite doesn't support pgvector
        with patch.object(
            similarity_service, "_query_similar_claims", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = [
                SimilarClaim(
                    claim_id=claim1.id,
                    content=claim1.content,
                    similarity=0.99,
                )
            ]

            similar: list[SimilarClaim] = await similarity_service.find_similar_claims(
                embedding=mock_embedding,
                threshold=0.85,
                limit=5,
            )

            # Assert
            assert len(similar) >= 1
            assert similar[0].similarity >= 0.85

    @pytest.mark.asyncio
    async def test_find_similar_claims_empty_database(
        self,
        similarity_service: ClaimSimilarityService,
        mock_embedding: list[float],
    ) -> None:
        """Test finding similar claims with empty database"""
        # Act
        with patch.object(
            similarity_service, "_query_similar_claims", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = []

            similar: list[SimilarClaim] = await similarity_service.find_similar_claims(
                embedding=mock_embedding,
            )

            # Assert
            assert len(similar) == 0

    @pytest.mark.asyncio
    async def test_find_similar_claims_respects_threshold(
        self,
        similarity_service: ClaimSimilarityService,
        mock_embedding: list[float],
    ) -> None:
        """Test that only claims above threshold are returned"""
        # Arrange - Create claims with varying similarity
        claim1_id = uuid4()

        with patch.object(
            similarity_service, "_query_similar_claims", new_callable=AsyncMock
        ) as mock_query:
            # Only return claims above the threshold
            mock_query.return_value = [
                SimilarClaim(claim_id=claim1_id, content="Claim 1", similarity=0.95),
            ]

            # Act
            similar: list[SimilarClaim] = await similarity_service.find_similar_claims(
                embedding=mock_embedding,
                threshold=0.90,  # Higher threshold
            )

            # Assert - Only high similarity claims
            assert all(s.similarity >= 0.90 for s in similar)

    @pytest.mark.asyncio
    async def test_find_similar_claims_respects_limit(
        self,
        similarity_service: ClaimSimilarityService,
        mock_embedding: list[float],
    ) -> None:
        """Test that limit parameter is respected"""
        # Arrange
        with patch.object(
            similarity_service, "_query_similar_claims", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = [
                SimilarClaim(claim_id=uuid4(), content=f"Claim {i}", similarity=0.9)
                for i in range(3)
            ]

            # Act
            similar: list[SimilarClaim] = await similarity_service.find_similar_claims(
                embedding=mock_embedding,
                limit=3,
            )

            # Assert
            assert len(similar) <= 3

    @pytest.mark.asyncio
    async def test_find_similar_claims_sorted_by_similarity(
        self,
        similarity_service: ClaimSimilarityService,
        mock_embedding: list[float],
    ) -> None:
        """Test that results are sorted by similarity (highest first)"""
        # Arrange
        with patch.object(
            similarity_service, "_query_similar_claims", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = [
                SimilarClaim(claim_id=uuid4(), content="Most similar", similarity=0.98),
                SimilarClaim(claim_id=uuid4(), content="Less similar", similarity=0.90),
                SimilarClaim(claim_id=uuid4(), content="Least similar", similarity=0.86),
            ]

            # Act
            similar: list[SimilarClaim] = await similarity_service.find_similar_claims(
                embedding=mock_embedding,
            )

            # Assert - Should be sorted by similarity descending
            for i in range(len(similar) - 1):
                assert similar[i].similarity >= similar[i + 1].similarity


class TestDeduplication:
    """Test claim deduplication functionality"""

    @pytest.fixture
    def similarity_service(self, db_session: AsyncSession) -> ClaimSimilarityService:
        """Provide ClaimSimilarityService instance"""
        with patch("app.services.claim_similarity_service.settings") as mock_settings:
            mock_settings.CLAIM_SIMILARITY_THRESHOLD = 0.85
            return ClaimSimilarityService(db_session)

    @pytest.mark.asyncio
    async def test_is_duplicate_returns_true_for_similar_claim(
        self,
        similarity_service: ClaimSimilarityService,
    ) -> None:
        """Test that is_duplicate returns True for highly similar claims"""
        # Arrange
        mock_embedding: list[float] = [0.1] * 1536

        with patch.object(
            similarity_service, "find_similar_claims", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = [
                SimilarClaim(
                    claim_id=uuid4(),
                    content="Almost identical claim",
                    similarity=0.95,
                )
            ]

            # Act
            is_dup, existing_claim = await similarity_service.is_duplicate(
                embedding=mock_embedding,
            )

            # Assert
            assert is_dup is True
            assert existing_claim is not None
            assert existing_claim.similarity >= 0.85

    @pytest.mark.asyncio
    async def test_is_duplicate_returns_false_for_unique_claim(
        self,
        similarity_service: ClaimSimilarityService,
    ) -> None:
        """Test that is_duplicate returns False for unique claims"""
        # Arrange
        mock_embedding: list[float] = [0.1] * 1536

        with patch.object(
            similarity_service, "find_similar_claims", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = []  # No similar claims found

            # Act
            is_dup, existing_claim = await similarity_service.is_duplicate(
                embedding=mock_embedding,
            )

            # Assert
            assert is_dup is False
            assert existing_claim is None

    @pytest.mark.asyncio
    async def test_is_duplicate_with_custom_threshold(
        self,
        similarity_service: ClaimSimilarityService,
    ) -> None:
        """Test is_duplicate with custom threshold"""
        # Arrange
        mock_embedding: list[float] = [0.1] * 1536

        with patch.object(
            similarity_service, "find_similar_claims", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = []

            # Act
            is_dup, _ = await similarity_service.is_duplicate(
                embedding=mock_embedding,
                threshold=0.95,  # Very high threshold
            )

            # Assert - verify threshold was passed
            mock_find.assert_called_once()
            call_args = mock_find.call_args
            assert call_args.kwargs.get("threshold") == 0.95


class TestFindDuplicatesForClaims:
    """Test finding duplicates for multiple claims"""

    @pytest.fixture
    def similarity_service(self, db_session: AsyncSession) -> ClaimSimilarityService:
        """Provide ClaimSimilarityService instance"""
        with patch("app.services.claim_similarity_service.settings") as mock_settings:
            mock_settings.CLAIM_SIMILARITY_THRESHOLD = 0.85
            return ClaimSimilarityService(db_session)

    @pytest.mark.asyncio
    async def test_find_duplicates_for_multiple_claims(
        self,
        similarity_service: ClaimSimilarityService,
    ) -> None:
        """Test finding duplicates for multiple claims at once"""
        # Arrange
        embeddings: list[list[float]] = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536,
        ]
        existing_claim_id = uuid4()

        with patch.object(
            similarity_service, "is_duplicate", new_callable=AsyncMock
        ) as mock_is_dup:
            # First claim is duplicate, others are unique
            mock_is_dup.side_effect = [
                (
                    True,
                    SimilarClaim(claim_id=existing_claim_id, content="Existing", similarity=0.95),
                ),
                (False, None),
                (False, None),
            ]

            # Act
            results: list[tuple[bool, Any]] = await similarity_service.find_duplicates_batch(
                embeddings=embeddings,
            )

            # Assert
            assert len(results) == 3
            assert results[0][0] is True  # First is duplicate
            assert results[1][0] is False  # Second is unique
            assert results[2][0] is False  # Third is unique

    @pytest.mark.asyncio
    async def test_find_duplicates_empty_list(
        self,
        similarity_service: ClaimSimilarityService,
    ) -> None:
        """Test finding duplicates with empty list"""
        # Act
        results: list[tuple[bool, Any]] = await similarity_service.find_duplicates_batch(
            embeddings=[],
        )

        # Assert
        assert results == []
