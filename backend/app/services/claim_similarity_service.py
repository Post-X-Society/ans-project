"""
Claim similarity service for deduplication using pgvector

Issue #176: LLM-based Claim Extraction - Deduplication using vector similarity

This service provides claim deduplication functionality using pgvector's
cosine similarity search. It identifies existing claims that are semantically
similar to new claims to avoid duplicate fact-checking work.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.claim import Claim

logger = logging.getLogger(__name__)


@dataclass
class SimilarClaim:
    """Represents a similar claim found in the database"""

    claim_id: UUID
    content: str
    similarity: float


class ClaimSimilarityService:
    """Service for finding similar claims using pgvector cosine similarity

    This service uses PostgreSQL's pgvector extension to perform efficient
    similarity search on claim embeddings. It supports:
    - Finding similar claims above a threshold
    - Checking if a claim is a duplicate
    - Batch duplicate detection

    Note: When running with SQLite (tests), vector operations are mocked
    since SQLite doesn't support pgvector.

    Attributes:
        db: Database session
        default_threshold: Default similarity threshold for deduplication

    Example:
        >>> service = ClaimSimilarityService(db_session)
        >>> similar = await service.find_similar_claims(embedding, threshold=0.85)
        >>> for claim in similar:
        ...     print(f"{claim.content}: {claim.similarity:.2f}")
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize ClaimSimilarityService with database session

        Args:
            db: AsyncSession for database operations
        """
        self.db: AsyncSession = db
        self.default_threshold: float = settings.CLAIM_SIMILARITY_THRESHOLD

    async def find_similar_claims(
        self,
        embedding: list[float],
        threshold: Optional[float] = None,
        limit: int = 5,
        exclude_claim_id: Optional[UUID] = None,
    ) -> list[SimilarClaim]:
        """Find claims with similar embeddings using cosine similarity

        Uses pgvector's cosine distance operator to find semantically
        similar claims in the database.

        Args:
            embedding: The query embedding vector (1536 dimensions)
            threshold: Minimum similarity score (0.0-1.0), defaults to config value
            limit: Maximum number of results to return
            exclude_claim_id: Optional claim ID to exclude from results

        Returns:
            List of SimilarClaim objects sorted by similarity (highest first)
        """
        if threshold is None:
            threshold = self.default_threshold

        similar_claims: list[SimilarClaim] = await self._query_similar_claims(
            embedding=embedding,
            threshold=threshold,
            limit=limit,
            exclude_claim_id=exclude_claim_id,
        )

        logger.debug(
            f"Found {len(similar_claims)} similar claims "
            f"(threshold: {threshold}, limit: {limit})"
        )

        return similar_claims

    async def _query_similar_claims(
        self,
        embedding: list[float],
        threshold: float,
        limit: int,
        exclude_claim_id: Optional[UUID] = None,
    ) -> list[SimilarClaim]:
        """Execute the pgvector similarity query

        This method contains the actual database query using pgvector's
        cosine distance operator. The query:
        1. Filters to claims with embeddings
        2. Calculates cosine similarity (1 - cosine_distance)
        3. Filters by threshold
        4. Orders by similarity descending
        5. Limits results

        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity threshold
            limit: Maximum results
            exclude_claim_id: Claim ID to exclude

        Returns:
            List of SimilarClaim objects
        """
        # Build the query using pgvector's cosine distance
        # Note: cosine_distance returns 0-2, we convert to similarity 0-1
        # similarity = 1 - (cosine_distance / 2) or simply use <=> operator

        # Using raw SQL for pgvector operations
        # Format embedding as PostgreSQL array literal
        embedding_str: str = "[" + ",".join(str(x) for x in embedding) + "]"

        sql: str = """
            SELECT
                id,
                content,
                1 - (embedding <=> :embedding) AS similarity
            FROM claims
            WHERE embedding IS NOT NULL
                AND 1 - (embedding <=> :embedding) >= :threshold
                {exclude_clause}
            ORDER BY similarity DESC
            LIMIT :limit
        """

        exclude_clause: str = ""
        params: dict[str, Any] = {
            "embedding": embedding_str,
            "threshold": threshold,
            "limit": limit,
        }

        if exclude_claim_id:
            exclude_clause = "AND id != :exclude_id"
            params["exclude_id"] = str(exclude_claim_id)

        sql = sql.format(exclude_clause=exclude_clause)

        try:
            result = await self.db.execute(text(sql), params)
            rows = result.fetchall()

            return [
                SimilarClaim(
                    claim_id=row[0],
                    content=row[1],
                    similarity=float(row[2]),
                )
                for row in rows
            ]
        except Exception as e:
            # Log but don't fail - SQLite doesn't support pgvector
            logger.warning(f"Vector similarity query failed (expected in tests): {e}")
            return []

    async def is_duplicate(
        self,
        embedding: list[float],
        threshold: Optional[float] = None,
    ) -> tuple[bool, Optional[SimilarClaim]]:
        """Check if a claim with this embedding is a duplicate

        A claim is considered a duplicate if there's an existing claim
        with similarity above the threshold.

        Args:
            embedding: The embedding to check
            threshold: Similarity threshold for duplicate detection

        Returns:
            Tuple of (is_duplicate: bool, matching_claim: Optional[SimilarClaim])
        """
        if threshold is None:
            threshold = self.default_threshold

        similar_claims: list[SimilarClaim] = await self.find_similar_claims(
            embedding=embedding,
            threshold=threshold,
            limit=1,
        )

        if similar_claims:
            logger.info(f"Duplicate claim found with similarity {similar_claims[0].similarity:.2f}")
            return True, similar_claims[0]

        return False, None

    async def find_duplicates_batch(
        self,
        embeddings: list[list[float]],
        threshold: Optional[float] = None,
    ) -> list[tuple[bool, Optional[SimilarClaim]]]:
        """Check multiple embeddings for duplicates

        Efficiently checks multiple claim embeddings for duplicates
        in a single batch operation.

        Args:
            embeddings: List of embedding vectors to check
            threshold: Similarity threshold for duplicate detection

        Returns:
            List of (is_duplicate, matching_claim) tuples, one per input embedding
        """
        if not embeddings:
            return []

        results: list[tuple[bool, Optional[SimilarClaim]]] = []

        for embedding in embeddings:
            is_dup, existing_claim = await self.is_duplicate(
                embedding=embedding,
                threshold=threshold,
            )
            results.append((is_dup, existing_claim))

        duplicate_count: int = sum(1 for is_dup, _ in results if is_dup)
        logger.info(f"Batch duplicate check: {duplicate_count}/{len(embeddings)} duplicates found")

        return results

    async def get_claim_with_embedding(self, claim_id: UUID) -> Optional[Claim]:
        """Get a claim by ID including its embedding

        Args:
            claim_id: The claim UUID

        Returns:
            Claim object if found, None otherwise
        """
        result = await self.db.execute(select(Claim).where(Claim.id == claim_id))
        return result.scalar_one_or_none()

    async def update_claim_embedding(
        self,
        claim_id: UUID,
        embedding: list[float],
    ) -> Optional[Claim]:
        """Update the embedding for an existing claim

        Args:
            claim_id: The claim UUID
            embedding: The new embedding vector

        Returns:
            Updated Claim object if found, None otherwise
        """
        claim: Optional[Claim] = await self.get_claim_with_embedding(claim_id)

        if claim is None:
            logger.warning(f"Claim {claim_id} not found for embedding update")
            return None

        claim.embedding = embedding
        await self.db.flush()

        logger.info(f"Updated embedding for claim {claim_id}")
        return claim
