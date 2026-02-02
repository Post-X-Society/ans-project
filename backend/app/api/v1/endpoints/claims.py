"""
Claims API endpoints

Issue #176: LLM-based Claim Extraction from Transcriptions and Submitter Comments

This module provides API endpoints for:
- Extracting claims from text using LLM
- Finding similar claims using vector similarity
- Managing claim extraction for submissions
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.submission import Submission
from app.models.user import User
from app.schemas.claim import (
    ClaimCreate,
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    ClaimResponse,
    ExtractedClaimSchema,
    SimilarClaimSchema,
)
from app.services.claim_service import ClaimService, get_claim
from app.services.claim_similarity_service import ClaimSimilarityService
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.llm_claim_extraction_service import LLMClaimExtractionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/submissions/{submission_id}/claims/extract",
    response_model=ClaimExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract claims from submission",
    description=(
        "Extract factual claims from a submission's transcription and optional comment "
        "using GPT-4. Claims are deduplicated against existing claims using vector similarity."
    ),
)
async def extract_claims_for_submission(
    submission_id: UUID,
    request: ClaimExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClaimExtractionResponse:
    """Extract claims from submission content

    This endpoint:
    1. Extracts verifiable factual claims from transcription and comment
    2. Generates embeddings for similarity search
    3. Deduplicates against existing claims
    4. Links claims to the submission

    Requires: Reviewer or Admin role
    """
    # Verify submission exists
    submission: Submission | None = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    try:
        # Initialize claim service
        claim_service: ClaimService = ClaimService(db)

        # Extract and process claims
        result = await claim_service.extract_and_process_claims(
            transcription=request.transcription,
            submission_id=submission_id,
            comment=request.comment,
            language_hint=request.language_hint,
            deduplicate=request.deduplicate,
        )

        # Build response with extracted claims
        extracted_claims: list[ExtractedClaimSchema] = []
        for claim in result.claims:
            # Determine if this is a duplicate
            is_dup: bool = claim.source != str(submission_id)

            extracted_claims.append(
                ExtractedClaimSchema(
                    content=claim.content,
                    confidence=0.95,  # Default confidence
                    source_type="transcription",
                    language="unknown",
                    is_duplicate=is_dup,
                    existing_claim_id=claim.id if is_dup else None,
                )
            )

        # Link claims to submission
        for claim in result.claims:
            if claim not in submission.claims:
                submission.claims.append(claim)

        await db.commit()

        logger.info(
            f"Extracted {len(extracted_claims)} claims for submission {submission_id} "
            f"(user: {current_user.email})"
        )

        return ClaimExtractionResponse(
            submission_id=submission_id,
            claims=extracted_claims,
            total_claims=len(extracted_claims),
            new_claims=result.new_claims_created,
            duplicates_found=result.duplicates_found,
            language="unknown",
        )

    except LLMClaimExtractionError as e:
        logger.error(f"Claim extraction failed for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Claim extraction service unavailable: {str(e)}",
        ) from e


@router.post(
    "/submissions/{submission_id}/claims",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add a claim to a submission",
    description=(
        "Manually create and link a single claim to a submission. "
        "This is useful when automatic extraction fails or misses claims. "
        "Requires Reviewer, Admin, or Super Admin role."
    ),
)
async def create_claim_for_submission(
    submission_id: UUID,
    claim_data: ClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClaimResponse:
    """Manually create a claim and link it to a submission

    This endpoint:
    1. Creates a new claim with the provided content
    2. Generates an embedding for similarity search
    3. Links the claim to the submission

    Requires: Reviewer, Admin, or Super Admin role
    """
    # Check user has permission (reviewer, admin, or super_admin)
    from app.models.user import UserRole

    if current_user.role not in [UserRole.REVIEWER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers and admins can manually add claims",
        )

    # Verify submission exists
    submission: Submission | None = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    try:
        # Initialize embedding service
        embedding_service: EmbeddingService = EmbeddingService()

        # Generate embedding for the claim
        embedding: list[float] = await embedding_service.generate_embedding(claim_data.content)

        # Create claim using claim service
        from app.models.claim import Claim

        claim = Claim(
            content=claim_data.content,
            source=claim_data.source,
            embedding=embedding,
        )

        db.add(claim)
        await db.flush()

        # Link claim to submission
        if claim not in submission.claims:
            submission.claims.append(claim)

        await db.commit()
        await db.refresh(claim)

        logger.info(
            f"Manually created claim {claim.id} for submission {submission_id} "
            f"(user: {current_user.email})"
        )

        return ClaimResponse(
            id=claim.id,
            content=claim.content,
            source=claim.source,
            created_at=claim.created_at,
            has_embedding=claim.embedding is not None,
        )

    except EmbeddingServiceError as e:
        logger.error(f"Embedding generation failed for manual claim: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Failed to create manual claim for submission {submission_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create claim: {str(e)}",
        ) from e


@router.get(
    "/claims/{claim_id}",
    response_model=ClaimResponse,
    summary="Get claim by ID",
)
async def get_claim_by_id(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a claim by its ID"""
    claim = await get_claim(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    return ClaimResponse(
        id=claim.id,
        content=claim.content,
        source=claim.source,
        created_at=claim.created_at,
        has_embedding=claim.embedding is not None,
    )


@router.post(
    "/claims/{claim_id}/similar",
    response_model=list[SimilarClaimSchema],
    summary="Find similar claims",
    description="Find claims similar to the given claim using vector similarity search.",
)
async def find_similar_claims(
    claim_id: UUID,
    threshold: float = 0.85,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SimilarClaimSchema]:
    """Find claims similar to a given claim

    Uses pgvector cosine similarity to find semantically similar claims.
    Requires the claim to have an embedding generated.
    """
    # Get the claim
    claim = await get_claim(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    if claim.embedding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim does not have an embedding. Cannot perform similarity search.",
        )

    # Find similar claims
    similarity_service: ClaimSimilarityService = ClaimSimilarityService(db)
    similar_claims = await similarity_service.find_similar_claims(
        embedding=list(claim.embedding),
        threshold=threshold,
        limit=limit,
        exclude_claim_id=claim_id,
    )

    return [
        SimilarClaimSchema(
            claim_id=sc.claim_id,
            content=sc.content,
            similarity=sc.similarity,
        )
        for sc in similar_claims
    ]


@router.post(
    "/claims/generate-embedding",
    response_model=dict[str, Any],
    summary="Generate embedding for text",
    description="Generate a vector embedding for the given text. Useful for testing.",
)
async def generate_embedding(
    text: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate an embedding for text content

    This is a utility endpoint for testing embedding generation.
    Returns the embedding dimensions and a sample of values.
    """
    try:
        embedding_service: EmbeddingService = EmbeddingService()
        embedding: list[float] = await embedding_service.generate_embedding(text)

        return {
            "text_length": len(text),
            "embedding_dimensions": len(embedding),
            "embedding_sample": embedding[:10],  # First 10 values for inspection
            "status": "success",
        }

    except EmbeddingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding generation failed: {str(e)}",
        ) from e
