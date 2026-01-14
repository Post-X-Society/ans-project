"""
Service layer for claim operations

Issue #176: LLM-based Claim Extraction from Transcriptions and Submitter Comments

This service orchestrates claim extraction, embedding generation, and deduplication
for fact-checking submissions. It integrates:
- LLM-based claim extraction using GPT-4
- Vector embeddings using text-embedding-3-small
- Deduplication using pgvector similarity search
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.claim import Claim
from app.services.claim_similarity_service import ClaimSimilarityService
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.llm_claim_extraction_service import (
    ClaimExtractionResult,
    ExtractedClaim,
    LLMClaimExtractionError,
    LLMClaimExtractionService,
)

logger = logging.getLogger(__name__)


@dataclass
class ClaimProcessingResult:
    """Result of processing extracted claims"""

    claims: list[Claim]
    duplicates_found: int
    new_claims_created: int
    errors: list[str]


class ClaimService:
    """Service for extracting, creating, and managing claims

    This service provides the main interface for claim processing in the
    fact-checking workflow. It orchestrates:
    1. LLM-based claim extraction from text
    2. Embedding generation for similarity search
    3. Deduplication using pgvector
    4. Database storage of claims

    Attributes:
        db: Database session
        llm_service: LLM claim extraction service
        embedding_service: Embedding generation service
        similarity_service: Claim similarity/deduplication service

    Example:
        >>> service = ClaimService(db_session)
        >>> result = await service.extract_and_process_claims(
        ...     transcription="Vaccines cause autism according to studies.",
        ...     submission_id=submission_uuid,
        ... )
        >>> print(f"Created {result.new_claims_created} new claims")
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMClaimExtractionService] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ) -> None:
        """Initialize ClaimService

        Args:
            db: Database session for claim operations
            llm_service: Optional LLM service (creates new if not provided)
            embedding_service: Optional embedding service (creates new if not provided)
        """
        self.db: AsyncSession = db
        self._llm_service: Optional[LLMClaimExtractionService] = llm_service
        self._embedding_service: Optional[EmbeddingService] = embedding_service
        self._similarity_service: Optional[ClaimSimilarityService] = None

    @property
    def llm_service(self) -> LLMClaimExtractionService:
        """Lazily initialize LLM service"""
        if self._llm_service is None:
            self._llm_service = LLMClaimExtractionService()
        return self._llm_service

    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazily initialize embedding service"""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def similarity_service(self) -> ClaimSimilarityService:
        """Lazily initialize similarity service"""
        if self._similarity_service is None:
            self._similarity_service = ClaimSimilarityService(self.db)
        return self._similarity_service

    async def extract_and_process_claims(
        self,
        transcription: str,
        submission_id: UUID,
        comment: Optional[str] = None,
        language_hint: Optional[str] = None,
        deduplicate: bool = True,
    ) -> ClaimProcessingResult:
        """Extract claims from text and process them for storage

        This is the main entry point for claim processing. It:
        1. Extracts claims from transcription and optional comment using GPT-4
        2. Generates embeddings for each claim
        3. Checks for duplicates if enabled
        4. Creates new claims or links to existing duplicates

        Args:
            transcription: Video transcription text
            submission_id: UUID of the parent submission
            comment: Optional submitter comment
            language_hint: Optional language code hint ('nl' or 'en')
            deduplicate: Whether to check for and link duplicates

        Returns:
            ClaimProcessingResult with created claims and statistics

        Raises:
            LLMClaimExtractionError: If claim extraction fails
        """
        errors: list[str] = []
        claims: list[Claim] = []
        duplicates_found: int = 0

        try:
            # Step 1: Extract claims using LLM
            if comment:
                extraction_result: ClaimExtractionResult = (
                    await self.llm_service.extract_claims_combined(
                        transcription=transcription,
                        comment=comment,
                        language_hint=language_hint,
                    )
                )
            else:
                extraction_result = await self.llm_service.extract_claims(
                    transcription=transcription,
                    source_type="transcription",
                    language_hint=language_hint,
                )

            logger.info(
                f"Extracted {len(extraction_result.claims)} claims from submission "
                f"{submission_id}, language: {extraction_result.language}"
            )

            # Step 2: Process each extracted claim
            for extracted_claim in extraction_result.claims:
                try:
                    claim, is_duplicate = await self._process_single_claim(
                        extracted_claim=extracted_claim,
                        submission_id=submission_id,
                        deduplicate=deduplicate,
                    )
                    claims.append(claim)
                    if is_duplicate:
                        duplicates_found += 1

                except Exception as e:
                    error_msg: str = f"Failed to process claim: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        except LLMClaimExtractionError as e:
            error_msg = f"LLM extraction failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            raise

        new_claims_created: int = len(claims) - duplicates_found

        logger.info(
            f"Claim processing complete for submission {submission_id}: "
            f"{new_claims_created} new claims, {duplicates_found} duplicates"
        )

        return ClaimProcessingResult(
            claims=claims,
            duplicates_found=duplicates_found,
            new_claims_created=new_claims_created,
            errors=errors,
        )

    async def _process_single_claim(
        self,
        extracted_claim: ExtractedClaim,
        submission_id: UUID,
        deduplicate: bool,
    ) -> tuple[Claim, bool]:
        """Process a single extracted claim

        Generates embedding, checks for duplicates, and creates/retrieves claim.

        Args:
            extracted_claim: The extracted claim from LLM
            submission_id: Parent submission UUID
            deduplicate: Whether to check for duplicates

        Returns:
            Tuple of (Claim object, is_duplicate)
        """
        is_duplicate: bool = False
        embedding: Optional[list[float]] = None

        # Generate embedding for similarity search
        try:
            embedding = await self.embedding_service.generate_embedding(extracted_claim.content)
        except EmbeddingServiceError as e:
            logger.warning(f"Failed to generate embedding: {e}")
            # Continue without embedding - claim can still be created

        # Check for duplicates if enabled and embedding was generated
        if deduplicate and embedding:
            is_dup, existing_claim = await self.similarity_service.is_duplicate(
                embedding=embedding,
            )

            if is_dup and existing_claim:
                # Return the existing claim
                claim: Optional[Claim] = await get_claim(self.db, existing_claim.claim_id)
                if claim:
                    logger.info(
                        f"Found duplicate claim {existing_claim.claim_id} "
                        f"(similarity: {existing_claim.similarity:.2f})"
                    )
                    return claim, True

        # Create new claim
        claim = await create_claim(
            db=self.db,
            content=extracted_claim.content,
            source=str(submission_id),
            embedding=embedding,
        )

        return claim, is_duplicate


# Legacy functions for backward compatibility


async def extract_claims_from_text(content: str) -> list[dict[str, Any]]:
    """
    Extract claims from text using AI.

    This is a legacy function that provides backward compatibility.
    For new code, use ClaimService.extract_and_process_claims() instead.

    Args:
        content: Text content to extract claims from

    Returns:
        List of dictionaries with claim content and confidence scores
    """
    # Check if OpenAI is configured
    if not settings.OPENAI_API_KEY:
        # Fallback to mock implementation when OpenAI is not configured
        logger.warning("OpenAI API key not configured, using mock extraction")
        return _mock_extract_claims(content)

    try:
        llm_service: LLMClaimExtractionService = LLMClaimExtractionService()
        result: ClaimExtractionResult = await llm_service.extract_claims(
            transcription=content,
            source_type="transcription",
        )

        return [
            {
                "content": claim.content,
                "confidence": claim.confidence,
                "language": claim.language,
                "source_type": claim.source_type,
            }
            for claim in result.claims
        ]

    except Exception as e:
        logger.error(f"LLM extraction failed, falling back to mock: {e}")
        return _mock_extract_claims(content)


def _mock_extract_claims(content: str) -> list[dict[str, Any]]:
    """
    Mock claim extraction for testing and fallback.

    Args:
        content: Text content to extract claims from

    Returns:
        List of dictionaries with claim content and confidence scores
    """
    sentences: list[str] = [s.strip() for s in content.split(".") if s.strip()]

    claims: list[dict[str, Any]] = []
    for i, sentence in enumerate(sentences[:3]):
        if len(sentence) > 10:
            claims.append(
                {
                    "content": sentence,
                    "confidence": 0.95 - (i * 0.05),
                    "language": "unknown",
                    "source_type": "transcription",
                }
            )

    if not claims:
        claims.append(
            {
                "content": content,
                "confidence": 0.90,
                "language": "unknown",
                "source_type": "transcription",
            }
        )

    return claims


async def create_claim(
    db: AsyncSession,
    content: str,
    source: str,
    confidence: float = 0.95,
    embedding: Optional[list[float]] = None,
) -> Claim:
    """
    Create a new claim in the database.

    Args:
        db: Database session
        content: Claim content text
        source: Source identifier (e.g., submission ID)
        confidence: Confidence score (0.0-1.0) - currently unused but kept for API
        embedding: Optional embedding vector for similarity search

    Returns:
        Created Claim object
    """
    claim: Claim = Claim(
        content=content,
        source=source,
        embedding=embedding,
    )
    db.add(claim)
    await db.flush()
    return claim


async def get_claim(db: AsyncSession, claim_id: UUID) -> Optional[Claim]:
    """
    Get a claim by ID.

    Args:
        db: Database session
        claim_id: Claim UUID

    Returns:
        Claim if found, None otherwise
    """
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    return result.scalar_one_or_none()


async def link_claim_to_submission(db: AsyncSession, claim_id: UUID, submission_id: UUID) -> None:
    """
    Link a claim to a submission via the junction table.

    Args:
        db: Database session
        claim_id: Claim UUID
        submission_id: Submission UUID
    """
    # The relationship is handled by SQLAlchemy's relationship()
    # We just need to add the claim to the submission's claims list
    # This is done in the submission_service
    pass
