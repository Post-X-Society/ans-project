"""
LLM-based claim extraction service for extracting factual claims from text

Issue #176: LLM-based Claim Extraction from Transcriptions and Submitter Comments

This service uses OpenAI GPT-4 to extract verifiable factual claims from:
- Snapchat Spotlight video transcriptions (via Whisper)
- Submitter comments

Supports Dutch (nl) and English (en) language content as required by EFCSN compliance.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClaimExtractionError(Exception):
    """Exception raised for LLM claim extraction errors"""

    pass


@dataclass
class ExtractedClaim:
    """Represents a single extracted claim with metadata"""

    content: str
    confidence: float
    source_type: str  # 'transcription' or 'comment'
    language: str
    reasoning: str = ""
    is_verifiable: bool = True


@dataclass
class ClaimExtractionResult:
    """Result of claim extraction from text"""

    claims: list[ExtractedClaim]
    language: str
    source_text: str
    total_claims_found: int = field(default=0)

    def __post_init__(self) -> None:
        if self.total_claims_found == 0:
            self.total_claims_found = len(self.claims)


# Prompt template for claim extraction
CLAIM_EXTRACTION_PROMPT = """You are a fact-checking assistant specialized in identifying verifiable factual claims.

Analyze the following text and extract all VERIFIABLE FACTUAL CLAIMS that could be fact-checked.

IMPORTANT GUIDELINES:
1. Only extract claims that are OBJECTIVE and VERIFIABLE (not opinions or personal preferences)
2. Focus on claims about facts, events, statistics, scientific statements, or causal relationships
3. Filter out:
   - Personal opinions ("I think this is great")
   - Subjective statements ("This is the best movie ever")
   - Greetings and small talk
   - Questions (unless they contain implicit claims)
4. Each claim should be self-contained and understandable without context
5. Preserve the original language of the claim (Dutch or English)
6. Assign a confidence score (0.0-1.0) based on how clearly the claim is stated

TEXT TO ANALYZE:
{text}

{language_hint}

Respond ONLY with valid JSON in this exact format:
{{
  "claims": [
    {{
      "content": "The exact claim text",
      "confidence": 0.95,
      "is_verifiable": true,
      "reasoning": "Brief explanation of why this is a verifiable claim"
    }}
  ],
  "language": "en or nl",
  "total_claims_found": 1
}}

If no verifiable claims are found, return:
{{
  "claims": [],
  "language": "unknown",
  "total_claims_found": 0
}}
"""

COMBINED_EXTRACTION_PROMPT = """You are a fact-checking assistant specialized in identifying verifiable factual claims.

Analyze the following video transcription AND submitter comment to extract all VERIFIABLE FACTUAL CLAIMS.

IMPORTANT GUIDELINES:
1. Only extract claims that are OBJECTIVE and VERIFIABLE (not opinions or personal preferences)
2. Focus on claims about facts, events, statistics, scientific statements, or causal relationships
3. Consider both the transcription AND the comment - claims may appear in either
4. Filter out opinions, greetings, and subjective statements
5. Each claim should be self-contained and understandable without context
6. Preserve the original language of the claim (Dutch or English)
7. Assign a confidence score (0.0-1.0) based on how clearly the claim is stated

VIDEO TRANSCRIPTION:
{transcription}

SUBMITTER COMMENT:
{comment}

Respond ONLY with valid JSON in this exact format:
{{
  "claims": [
    {{
      "content": "The exact claim text",
      "confidence": 0.95,
      "is_verifiable": true,
      "reasoning": "Brief explanation of why this is a verifiable claim"
    }}
  ],
  "language": "en or nl",
  "total_claims_found": 1
}}
"""


class LLMClaimExtractionService:
    """Service for extracting factual claims from text using GPT-4

    This service uses OpenAI's GPT-4 model to identify and extract verifiable
    factual claims from video transcriptions and user comments. It filters out
    opinions and subjective statements, focusing only on claims that can be
    fact-checked.

    Attributes:
        SUPPORTED_LANGUAGES: List of supported language codes
        model: The GPT model to use for extraction

    Example:
        >>> service = LLMClaimExtractionService()
        >>> result = await service.extract_claims(
        ...     transcription="Vaccines cause autism according to studies.",
        ...     source_type="transcription"
        ... )
        >>> print(result.claims[0].content)
        "Vaccines cause autism"
    """

    SUPPORTED_LANGUAGES: list[str] = ["nl", "en"]

    def __init__(self) -> None:
        """Initialize LLMClaimExtractionService with OpenAI API key

        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please configure it in your .env file."
            )
        self.api_key: str = settings.OPENAI_API_KEY
        self.model: str = settings.OPENAI_GPT_MODEL
        self.max_claims: int = settings.CLAIM_EXTRACTION_MAX_CLAIMS
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazily initialize and return AsyncOpenAI client"""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def extract_claims(
        self,
        transcription: str,
        source_type: str,
        language_hint: Optional[str] = None,
    ) -> ClaimExtractionResult:
        """Extract factual claims from text using GPT-4

        Args:
            transcription: The text content to analyze (transcription or comment)
            source_type: Type of source ('transcription' or 'comment')
            language_hint: Optional language code hint (e.g., 'nl', 'en')

        Returns:
            ClaimExtractionResult containing extracted claims and metadata

        Raises:
            LLMClaimExtractionError: If extraction fails
        """
        # Handle empty input
        if not transcription or not transcription.strip():
            logger.info("Empty transcription provided, returning empty result")
            return ClaimExtractionResult(
                claims=[],
                language="unknown",
                source_text="",
            )

        try:
            # Build language hint for prompt
            hint_text: str = ""
            if language_hint and language_hint in self.SUPPORTED_LANGUAGES:
                hint_text = f"The text is likely in {language_hint.upper()}."

            # Call GPT-4 API
            response: dict[str, Any] = await self._call_gpt_api(
                CLAIM_EXTRACTION_PROMPT.format(
                    text=transcription,
                    language_hint=hint_text,
                )
            )

            # Parse and create claims
            claims: list[ExtractedClaim] = self._parse_claims_response(response, source_type)

            # Limit to max claims
            claims = claims[: self.max_claims]

            result: ClaimExtractionResult = ClaimExtractionResult(
                claims=claims,
                language=response.get("language", "unknown"),
                source_text=transcription,
                total_claims_found=response.get("total_claims_found", len(claims)),
            )

            logger.info(
                f"Extracted {len(claims)} claims from {source_type}, "
                f"language: {result.language}"
            )

            return result

        except LLMClaimExtractionError:
            raise
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            raise LLMClaimExtractionError(f"Claim extraction failed: {str(e)}") from e

    async def extract_claims_combined(
        self,
        transcription: str,
        comment: str,
        language_hint: Optional[str] = None,
    ) -> ClaimExtractionResult:
        """Extract claims from both transcription and comment combined

        Args:
            transcription: Video transcription text
            comment: Submitter comment text
            language_hint: Optional language code hint

        Returns:
            ClaimExtractionResult with claims from both sources

        Raises:
            LLMClaimExtractionError: If extraction fails
        """
        # Handle empty inputs
        if not transcription.strip() and not comment.strip():
            return ClaimExtractionResult(
                claims=[],
                language="unknown",
                source_text="",
            )

        try:
            # Call GPT-4 API with combined prompt
            response: dict[str, Any] = await self._call_gpt_api(
                COMBINED_EXTRACTION_PROMPT.format(
                    transcription=transcription or "(No transcription available)",
                    comment=comment or "(No comment provided)",
                )
            )

            # Parse claims - mark source type as 'combined' for combined extraction
            claims: list[ExtractedClaim] = self._parse_claims_response(response, "combined")

            # Limit to max claims
            claims = claims[: self.max_claims]

            result: ClaimExtractionResult = ClaimExtractionResult(
                claims=claims,
                language=response.get("language", "unknown"),
                source_text=f"{transcription}\n---\n{comment}",
                total_claims_found=response.get("total_claims_found", len(claims)),
            )

            logger.info(
                f"Extracted {len(claims)} claims from combined sources, "
                f"language: {result.language}"
            )

            return result

        except LLMClaimExtractionError:
            raise
        except Exception as e:
            logger.error(f"Combined claim extraction failed: {e}")
            raise LLMClaimExtractionError(f"Claim extraction failed: {str(e)}") from e

    async def _call_gpt_api(self, prompt: str) -> dict[str, Any]:
        """Make the actual API call to OpenAI GPT-4

        Args:
            prompt: The formatted prompt to send

        Returns:
            Parsed JSON response from GPT-4
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a fact-checking AI assistant. "
                        "You identify verifiable factual claims in text. "
                        "Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Low temperature for consistent extraction
            max_tokens=2000,
        )

        content: str = response.choices[0].message.content or "{}"
        return json.loads(content)

    def _parse_claims_response(
        self, response: dict[str, Any], source_type: str
    ) -> list[ExtractedClaim]:
        """Parse GPT-4 response into ExtractedClaim objects

        Args:
            response: Parsed JSON response from GPT-4
            source_type: The source type for the claims

        Returns:
            List of ExtractedClaim objects
        """
        claims: list[ExtractedClaim] = []
        language: str = response.get("language", "unknown")

        for claim_data in response.get("claims", []):
            # Only include verifiable claims
            if not claim_data.get("is_verifiable", True):
                continue

            claim: ExtractedClaim = ExtractedClaim(
                content=claim_data.get("content", ""),
                confidence=float(claim_data.get("confidence", 0.5)),
                source_type=source_type,
                language=language,
                reasoning=claim_data.get("reasoning", ""),
                is_verifiable=True,
            )

            # Validate claim content is not empty
            if claim.content.strip():
                claims.append(claim)

        return claims


# Singleton instance for use across the application
_llm_claim_extraction_service: Optional[LLMClaimExtractionService] = None


def get_llm_claim_extraction_service() -> LLMClaimExtractionService:
    """Get or create LLMClaimExtractionService singleton instance

    Returns:
        LLMClaimExtractionService instance

    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    global _llm_claim_extraction_service
    if _llm_claim_extraction_service is None:
        _llm_claim_extraction_service = LLMClaimExtractionService()
    return _llm_claim_extraction_service
