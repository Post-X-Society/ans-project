"""
Tests for LLM-based claim extraction service

Following TDD approach: Tests written FIRST before implementation
Issue #176: LLM-based Claim Extraction from Transcriptions and Submitter Comments

Tests claim extraction using GPT-4 for Dutch and English content.
"""

import json
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# These imports will fail until we implement the service (TDD red phase)
from app.services.llm_claim_extraction_service import (
    ClaimExtractionResult,
    ExtractedClaim,
    LLMClaimExtractionError,
    LLMClaimExtractionService,
)


class TestLLMClaimExtractionServiceInitialization:
    """Test LLMClaimExtractionService initialization"""

    def test_service_initialization_with_api_key(self) -> None:
        """Test service initializes correctly with API key"""
        with patch("app.services.llm_claim_extraction_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_GPT_MODEL = "gpt-4-turbo-preview"
            mock_settings.CLAIM_EXTRACTION_MAX_CLAIMS = 10
            service: LLMClaimExtractionService = LLMClaimExtractionService()
            assert service is not None
            assert isinstance(service, LLMClaimExtractionService)

    def test_service_raises_error_without_api_key(self) -> None:
        """Test service raises error when API key is missing"""
        with patch("app.services.llm_claim_extraction_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.OPENAI_GPT_MODEL = "gpt-4-turbo-preview"
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                LLMClaimExtractionService()

    def test_service_uses_configured_model(self) -> None:
        """Test service uses the configured GPT model"""
        with patch("app.services.llm_claim_extraction_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_GPT_MODEL = "gpt-4o"
            mock_settings.CLAIM_EXTRACTION_MAX_CLAIMS = 10
            service: LLMClaimExtractionService = LLMClaimExtractionService()
            assert service.model == "gpt-4o"


class TestExtractedClaim:
    """Test ExtractedClaim dataclass"""

    def test_extracted_claim_creation(self) -> None:
        """Test ExtractedClaim can be created with all fields"""
        claim: ExtractedClaim = ExtractedClaim(
            content="The Earth is flat",
            confidence=0.95,
            source_type="transcription",
            language="en",
        )
        assert claim.content == "The Earth is flat"
        assert claim.confidence == 0.95
        assert claim.source_type == "transcription"
        assert claim.language == "en"

    def test_extracted_claim_dutch_content(self) -> None:
        """Test ExtractedClaim with Dutch content"""
        claim: ExtractedClaim = ExtractedClaim(
            content="De aarde is plat",
            confidence=0.92,
            source_type="transcription",
            language="nl",
        )
        assert claim.language == "nl"
        assert "aarde" in claim.content


class TestLLMClaimExtractionService:
    """Test LLMClaimExtractionService extraction functionality"""

    @pytest.fixture
    def llm_service(self) -> Generator[LLMClaimExtractionService, None, None]:
        """Provide LLMClaimExtractionService instance with mocked settings"""
        with patch("app.services.llm_claim_extraction_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_GPT_MODEL = "gpt-4-turbo-preview"
            mock_settings.CLAIM_EXTRACTION_MAX_CLAIMS = 10
            service: LLMClaimExtractionService = LLMClaimExtractionService()
            yield service

    @pytest.fixture
    def mock_openai_response(self) -> dict[str, Any]:
        """Provide a mock GPT-4 response for claim extraction"""
        return {
            "claims": [
                {
                    "content": "Vaccines cause autism",
                    "confidence": 0.95,
                    "is_verifiable": True,
                    "reasoning": "This is a specific factual claim that can be verified",
                },
                {
                    "content": "5G towers spread disease",
                    "confidence": 0.88,
                    "is_verifiable": True,
                    "reasoning": "This is a causal claim that can be fact-checked",
                },
            ],
            "language": "en",
            "total_claims_found": 2,
        }

    @pytest.fixture
    def mock_dutch_openai_response(self) -> dict[str, Any]:
        """Provide a mock GPT-4 response for Dutch claim extraction"""
        return {
            "claims": [
                {
                    "content": "Vaccins veroorzaken autisme",
                    "confidence": 0.94,
                    "is_verifiable": True,
                    "reasoning": "Dit is een specifieke feitelijke bewering",
                },
            ],
            "language": "nl",
            "total_claims_found": 1,
        }

    @pytest.mark.asyncio
    async def test_extract_claims_from_english_text(
        self, llm_service: LLMClaimExtractionService, mock_openai_response: dict[str, Any]
    ) -> None:
        """Test extracting claims from English transcription"""
        # Arrange
        transcription: str = (
            "I heard that vaccines cause autism. Also, 5G towers spread disease. "
            "This video is really informative."
        )

        mock_completion: Mock = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_openai_response)))
        ]

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=transcription,
                source_type="transcription",
            )

            # Assert
            assert len(result.claims) == 2
            assert result.language == "en"
            assert result.claims[0].content == "Vaccines cause autism"
            assert result.claims[0].confidence >= 0.0
            assert result.claims[0].confidence <= 1.0
            assert result.claims[0].source_type == "transcription"

    @pytest.mark.asyncio
    async def test_extract_claims_from_dutch_text(
        self, llm_service: LLMClaimExtractionService, mock_dutch_openai_response: dict[str, Any]
    ) -> None:
        """Test extracting claims from Dutch transcription"""
        # Arrange
        transcription: str = (
            "Ik hoorde dat vaccins autisme veroorzaken. " "Deze video is echt informatief."
        )

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_dutch_openai_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=transcription,
                source_type="transcription",
                language_hint="nl",
            )

            # Assert
            assert len(result.claims) == 1
            assert result.language == "nl"
            assert "vaccins" in result.claims[0].content.lower()

    @pytest.mark.asyncio
    async def test_extract_claims_from_comment(
        self, llm_service: LLMClaimExtractionService, mock_openai_response: dict[str, Any]
    ) -> None:
        """Test extracting claims from submitter comment"""
        # Arrange
        comment: str = "Please check if vaccines really cause autism"

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=comment,
                source_type="comment",
            )

            # Assert
            assert all(c.source_type == "comment" for c in result.claims)

    @pytest.mark.asyncio
    async def test_extract_claims_combined_transcription_and_comment(
        self, llm_service: LLMClaimExtractionService
    ) -> None:
        """Test extracting claims from both transcription and comment"""
        # Arrange
        transcription: str = "Vaccines cause autism according to this study."
        comment: str = "I also want you to check if 5G is dangerous."

        mock_response: dict[str, Any] = {
            "claims": [
                {
                    "content": "Vaccines cause autism",
                    "confidence": 0.95,
                    "is_verifiable": True,
                    "reasoning": "From transcription",
                },
                {
                    "content": "5G is dangerous",
                    "confidence": 0.88,
                    "is_verifiable": True,
                    "reasoning": "From comment",
                },
            ],
            "language": "en",
            "total_claims_found": 2,
        }

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims_combined(
                transcription=transcription,
                comment=comment,
            )

            # Assert
            assert len(result.claims) == 2

    @pytest.mark.asyncio
    async def test_extract_claims_filters_opinions(
        self, llm_service: LLMClaimExtractionService
    ) -> None:
        """Test that opinions are filtered out, only verifiable claims returned"""
        # Arrange
        transcription: str = "I think this movie is great. But vaccines definitely cause autism."

        # Only the factual claim should be returned
        mock_response: dict[str, Any] = {
            "claims": [
                {
                    "content": "Vaccines cause autism",
                    "confidence": 0.92,
                    "is_verifiable": True,
                    "reasoning": "Factual claim",
                },
            ],
            "language": "en",
            "total_claims_found": 1,
        }

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=transcription,
                source_type="transcription",
            )

            # Assert - opinion should be filtered out
            assert len(result.claims) == 1
            assert "movie is great" not in result.claims[0].content.lower()

    @pytest.mark.asyncio
    async def test_extract_claims_empty_transcription(
        self, llm_service: LLMClaimExtractionService
    ) -> None:
        """Test extraction handles empty transcription"""
        # Arrange
        transcription: str = ""

        # Act
        result: ClaimExtractionResult = await llm_service.extract_claims(
            transcription=transcription,
            source_type="transcription",
        )

        # Assert
        assert len(result.claims) == 0
        assert result.language == "unknown"

    @pytest.mark.asyncio
    async def test_extract_claims_no_verifiable_claims(
        self, llm_service: LLMClaimExtractionService
    ) -> None:
        """Test extraction when no verifiable claims found"""
        # Arrange
        transcription: str = "This is just a fun video about my day."

        mock_response: dict[str, Any] = {
            "claims": [],
            "language": "en",
            "total_claims_found": 0,
        }

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=transcription,
                source_type="transcription",
            )

            # Assert
            assert len(result.claims) == 0

    @pytest.mark.asyncio
    async def test_extract_claims_respects_max_claims_limit(
        self, llm_service: LLMClaimExtractionService
    ) -> None:
        """Test extraction respects maximum claims limit"""
        # Arrange
        transcription: str = "Many claims here..."

        # Mock response with more claims than limit
        mock_response: dict[str, Any] = {
            "claims": [
                {"content": f"Claim {i}", "confidence": 0.9, "is_verifiable": True}
                for i in range(15)  # More than max_claims (10)
            ],
            "language": "en",
            "total_claims_found": 15,
        }

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=transcription,
                source_type="transcription",
            )

            # Assert - should be limited to max_claims
            assert len(result.claims) <= 10

    @pytest.mark.asyncio
    async def test_extract_claims_api_error_handling(
        self, llm_service: LLMClaimExtractionService
    ) -> None:
        """Test extraction handles API errors gracefully"""
        # Arrange
        transcription: str = "Test transcription"

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("OpenAI API error")

            # Act & Assert
            with pytest.raises(LLMClaimExtractionError, match="Claim extraction failed"):
                await llm_service.extract_claims(
                    transcription=transcription,
                    source_type="transcription",
                )

    @pytest.mark.asyncio
    async def test_extract_claims_returns_confidence_scores(
        self, llm_service: LLMClaimExtractionService, mock_openai_response: dict[str, Any]
    ) -> None:
        """Test that extracted claims include confidence scores"""
        # Arrange
        transcription: str = "Test transcription with claims"

        with patch.object(llm_service, "_call_gpt_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response

            # Act
            result: ClaimExtractionResult = await llm_service.extract_claims(
                transcription=transcription,
                source_type="transcription",
            )

            # Assert
            for claim in result.claims:
                assert hasattr(claim, "confidence")
                assert 0.0 <= claim.confidence <= 1.0


class TestClaimExtractionResult:
    """Test ClaimExtractionResult dataclass"""

    def test_result_creation(self) -> None:
        """Test ClaimExtractionResult can be created"""
        claims: list[ExtractedClaim] = [
            ExtractedClaim(
                content="Test claim",
                confidence=0.9,
                source_type="transcription",
                language="en",
            )
        ]
        result: ClaimExtractionResult = ClaimExtractionResult(
            claims=claims,
            language="en",
            source_text="Original text",
        )
        assert len(result.claims) == 1
        assert result.language == "en"
        assert result.source_text == "Original text"

    def test_result_empty_claims(self) -> None:
        """Test ClaimExtractionResult with no claims"""
        result: ClaimExtractionResult = ClaimExtractionResult(
            claims=[],
            language="en",
            source_text="No claims here",
        )
        assert len(result.claims) == 0
