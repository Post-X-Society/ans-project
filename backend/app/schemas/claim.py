"""
Pydantic schemas for Claim API

Issue #176: LLM-based Claim Extraction from Transcriptions and Submitter Comments
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClaimCreate(BaseModel):
    """Schema for creating a new claim"""

    content: str = Field(..., min_length=1, max_length=1000, description="Claim content")
    source: str = Field(..., min_length=1, max_length=255, description="Source of the claim")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )


class ClaimResponse(BaseModel):
    """Schema for claim response"""

    id: UUID
    content: str
    source: str
    created_at: datetime
    has_embedding: bool = False

    model_config = {"from_attributes": True}


class ClaimExtractResponse(BaseModel):
    """Schema for extracted claim with confidence"""

    claim_id: UUID
    content: str
    confidence: float = Field(..., ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class ClaimExtractionRequest(BaseModel):
    """Request schema for claim extraction endpoint"""

    transcription: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Video transcription or text content to extract claims from",
    )
    comment: Optional[str] = Field(
        None,
        max_length=5000,
        description="Optional submitter comment",
    )
    language_hint: Optional[Literal["en", "nl"]] = Field(
        None,
        description="Optional language hint to improve extraction accuracy",
    )
    deduplicate: bool = Field(
        True,
        description="Whether to check for and link duplicate claims",
    )


class ExtractedClaimSchema(BaseModel):
    """Schema for a single extracted claim"""

    content: str = Field(..., description="The extracted claim text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source_type: str = Field(
        ..., description="Source type: 'transcription', 'comment', or 'combined'"
    )
    language: str = Field(..., description="Detected language code")
    is_duplicate: bool = Field(False, description="Whether this claim is a duplicate")
    existing_claim_id: Optional[UUID] = Field(None, description="ID of existing claim if duplicate")


class ClaimExtractionResponse(BaseModel):
    """Response schema for claim extraction endpoint"""

    submission_id: UUID = Field(..., description="The submission these claims belong to")
    claims: list[ExtractedClaimSchema] = Field(
        default_factory=list, description="List of extracted claims"
    )
    total_claims: int = Field(0, description="Total number of claims extracted")
    new_claims: int = Field(0, description="Number of new claims created")
    duplicates_found: int = Field(0, description="Number of duplicate claims found")
    language: str = Field("unknown", description="Detected language of the content")


class SimilarClaimSchema(BaseModel):
    """Schema for a similar claim found during deduplication"""

    claim_id: UUID = Field(..., description="ID of the similar claim")
    content: str = Field(..., description="Content of the similar claim")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
