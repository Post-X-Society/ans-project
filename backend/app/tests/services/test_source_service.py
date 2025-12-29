"""
Tests for Source Service - TDD approach: Write tests FIRST

Issue #70: Backend: Source Management Service (TDD)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

This test module covers:
- Full CRUD functionality for sources
- Automatic citation numbering ([1], [2], [3])
- Source count tracking for fact-checks
- Minimum 2-source validation before publishing
- Credibility scoring (1-5 scale)
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.source import SourceRelevance, SourceType
from app.models.user import User, UserRole


# Helper function to create prerequisite objects for tests
async def create_test_fact_check(db_session: AsyncSession) -> FactCheck:
    """Create a claim and fact_check for testing."""
    claim = Claim(
        content="Test claim content for source testing",
        source="user_submission",
    )
    db_session.add(claim)
    await db_session.flush()

    fact_check = FactCheck(
        claim_id=claim.id,
        verdict="true",
        confidence=0.9,
        reasoning="Test reasoning",
        sources=["https://example.com"],
    )
    db_session.add(fact_check)
    await db_session.commit()
    await db_session.refresh(fact_check)

    return fact_check


async def create_test_user(db_session: AsyncSession, role: UserRole = UserRole.REVIEWER) -> User:
    """Create a test user with specified role."""
    user = User(
        email=f"testuser-{uuid4()}@example.com",
        password_hash="hashed_password",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestSourceServiceCreate:
    """Tests for SourceService.create_source()"""

    @pytest.mark.asyncio
    async def test_create_source_with_required_fields(self, db_session: AsyncSession) -> None:
        """Test creating a source with only required fields."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Primary Evidence Source",
            access_date=date(2025, 12, 28),
        )

        source = await create_source(db_session, source_data)

        assert source.id is not None
        assert isinstance(source.id, UUID)
        assert source.fact_check_id == fact_check.id
        assert source.source_type == SourceType.PRIMARY
        assert source.title == "Primary Evidence Source"
        assert source.access_date == date(2025, 12, 28)
        # Optional fields should be None
        assert source.url is None
        assert source.publication_date is None
        assert source.credibility_score is None
        assert source.relevance is None
        assert source.archived_url is None
        assert source.notes is None

    @pytest.mark.asyncio
    async def test_create_source_with_all_fields(self, db_session: AsyncSession) -> None:
        """Test creating a source with all fields populated."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.ACADEMIC,
            title="Academic Research Paper",
            url="https://academic.example.com/paper/123",
            publication_date=date(2025, 6, 15),
            access_date=date(2025, 12, 28),
            credibility_score=5,
            relevance=SourceRelevance.SUPPORTS,
            archived_url="https://web.archive.org/web/20251228/https://academic.example.com/paper/123",
            notes="Peer-reviewed journal article from reputable source.",
        )

        source = await create_source(db_session, source_data)

        assert source.id is not None
        assert source.source_type == SourceType.ACADEMIC
        assert source.title == "Academic Research Paper"
        assert source.url == "https://academic.example.com/paper/123"
        assert source.publication_date == date(2025, 6, 15)
        assert source.access_date == date(2025, 12, 28)
        assert source.credibility_score == 5
        assert source.relevance == SourceRelevance.SUPPORTS
        assert "web.archive.org" in source.archived_url  # type: ignore[operator]
        assert source.notes == "Peer-reviewed journal article from reputable source."

    @pytest.mark.asyncio
    async def test_create_source_updates_fact_check_sources_count(
        self, db_session: AsyncSession
    ) -> None:
        """Test that creating a source increments the fact_check.sources_count."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)
        assert fact_check.sources_count == 0

        # Create first source
        source_data1 = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source 1",
            access_date=date(2025, 12, 28),
        )
        await create_source(db_session, source_data1)

        await db_session.refresh(fact_check)
        assert fact_check.sources_count == 1

        # Create second source
        source_data2 = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.SECONDARY,
            title="Source 2",
            access_date=date(2025, 12, 28),
        )
        await create_source(db_session, source_data2)

        await db_session.refresh(fact_check)
        assert fact_check.sources_count == 2

    @pytest.mark.asyncio
    async def test_create_source_fact_check_not_found(self, db_session: AsyncSession) -> None:
        """Test that creating a source with invalid fact_check_id raises error."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import SourceValidationError, create_source

        non_existent_id = uuid4()
        source_data = SourceCreate(
            fact_check_id=non_existent_id,
            source_type=SourceType.PRIMARY,
            title="Source",
            access_date=date(2025, 12, 28),
        )

        with pytest.raises(SourceValidationError) as exc_info:
            await create_source(db_session, source_data)

        assert "not found" in str(exc_info.value).lower()


class TestSourceServiceRead:
    """Tests for SourceService read operations."""

    @pytest.mark.asyncio
    async def test_get_source_by_id(self, db_session: AsyncSession) -> None:
        """Test retrieving a source by ID."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source, get_source

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.EXPERT,
            title="Expert Quote",
            access_date=date(2025, 12, 28),
        )
        created_source = await create_source(db_session, source_data)

        retrieved_source = await get_source(db_session, created_source.id)

        assert retrieved_source is not None
        assert retrieved_source.id == created_source.id
        assert retrieved_source.title == "Expert Quote"

    @pytest.mark.asyncio
    async def test_get_source_not_found(self, db_session: AsyncSession) -> None:
        """Test that getting a non-existent source raises error."""
        from app.services.source_service import SourceValidationError, get_source

        with pytest.raises(SourceValidationError) as exc_info:
            await get_source(db_session, uuid4())

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_sources_for_fact_check(self, db_session: AsyncSession) -> None:
        """Test retrieving all sources for a fact-check."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_sources_for_fact_check,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create multiple sources
        for i, source_type in enumerate(
            [SourceType.PRIMARY, SourceType.SECONDARY, SourceType.ACADEMIC]
        ):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        sources = await get_sources_for_fact_check(db_session, fact_check.id)

        assert len(sources) == 3
        assert all(s.fact_check_id == fact_check.id for s in sources)

    @pytest.mark.asyncio
    async def test_get_sources_for_fact_check_empty(self, db_session: AsyncSession) -> None:
        """Test retrieving sources for a fact-check with no sources."""
        from app.services.source_service import get_sources_for_fact_check

        fact_check = await create_test_fact_check(db_session)

        sources = await get_sources_for_fact_check(db_session, fact_check.id)

        assert len(sources) == 0


class TestSourceServiceUpdate:
    """Tests for SourceService.update_source()"""

    @pytest.mark.asyncio
    async def test_update_source_single_field(self, db_session: AsyncSession) -> None:
        """Test updating a single field on a source."""
        from app.schemas.source import SourceCreate, SourceUpdate
        from app.services.source_service import create_source, update_source

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.MEDIA,
            title="Original Title",
            access_date=date(2025, 12, 28),
        )
        source = await create_source(db_session, source_data)

        update_data = SourceUpdate(title="Updated Title")
        updated_source = await update_source(db_session, source.id, update_data)

        assert updated_source.title == "Updated Title"
        assert updated_source.source_type == SourceType.MEDIA  # Unchanged

    @pytest.mark.asyncio
    async def test_update_source_multiple_fields(self, db_session: AsyncSession) -> None:
        """Test updating multiple fields on a source."""
        from app.schemas.source import SourceCreate, SourceUpdate
        from app.services.source_service import create_source, update_source

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.GOVERNMENT,
            title="Government Report",
            access_date=date(2025, 12, 28),
            credibility_score=3,
        )
        source = await create_source(db_session, source_data)

        update_data = SourceUpdate(
            title="Updated Government Report",
            credibility_score=5,
            notes="Verified by official channel",
            relevance=SourceRelevance.SUPPORTS,
        )
        updated_source = await update_source(db_session, source.id, update_data)

        assert updated_source.title == "Updated Government Report"
        assert updated_source.credibility_score == 5
        assert updated_source.notes == "Verified by official channel"
        assert updated_source.relevance == SourceRelevance.SUPPORTS

    @pytest.mark.asyncio
    async def test_update_source_not_found(self, db_session: AsyncSession) -> None:
        """Test that updating a non-existent source raises error."""
        from app.schemas.source import SourceUpdate
        from app.services.source_service import SourceValidationError, update_source

        update_data = SourceUpdate(title="New Title")

        with pytest.raises(SourceValidationError) as exc_info:
            await update_source(db_session, uuid4(), update_data)

        assert "not found" in str(exc_info.value).lower()


class TestSourceServiceDelete:
    """Tests for SourceService.delete_source()"""

    @pytest.mark.asyncio
    async def test_delete_source(self, db_session: AsyncSession) -> None:
        """Test deleting a source."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            SourceValidationError,
            create_source,
            delete_source,
            get_source,
        )

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source to Delete",
            access_date=date(2025, 12, 28),
        )
        source = await create_source(db_session, source_data)
        source_id = source.id

        await delete_source(db_session, source_id)

        # Verify source is deleted
        with pytest.raises(SourceValidationError):
            await get_source(db_session, source_id)

    @pytest.mark.asyncio
    async def test_delete_source_updates_sources_count(self, db_session: AsyncSession) -> None:
        """Test that deleting a source decrements fact_check.sources_count."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source, delete_source

        fact_check = await create_test_fact_check(db_session)

        # Create two sources
        source_data1 = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source 1",
            access_date=date(2025, 12, 28),
        )
        source1 = await create_source(db_session, source_data1)

        source_data2 = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.SECONDARY,
            title="Source 2",
            access_date=date(2025, 12, 28),
        )
        await create_source(db_session, source_data2)

        await db_session.refresh(fact_check)
        assert fact_check.sources_count == 2

        # Delete first source
        await delete_source(db_session, source1.id)

        await db_session.refresh(fact_check)
        assert fact_check.sources_count == 1

    @pytest.mark.asyncio
    async def test_delete_source_not_found(self, db_session: AsyncSession) -> None:
        """Test that deleting a non-existent source raises error."""
        from app.services.source_service import SourceValidationError, delete_source

        with pytest.raises(SourceValidationError) as exc_info:
            await delete_source(db_session, uuid4())

        assert "not found" in str(exc_info.value).lower()


class TestCitationNumbering:
    """Tests for automatic citation numbering system ([1], [2], [3])"""

    @pytest.mark.asyncio
    async def test_get_sources_with_citation_numbers(self, db_session: AsyncSession) -> None:
        """Test that sources are returned with citation numbers."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_sources_with_citations,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create sources in order
        for i, source_type in enumerate(
            [SourceType.PRIMARY, SourceType.SECONDARY, SourceType.ACADEMIC]
        ):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        cited_sources = await get_sources_with_citations(db_session, fact_check.id)

        assert len(cited_sources) == 3
        assert cited_sources[0]["citation_number"] == 1
        assert cited_sources[1]["citation_number"] == 2
        assert cited_sources[2]["citation_number"] == 3

    @pytest.mark.asyncio
    async def test_citation_numbers_by_creation_order(self, db_session: AsyncSession) -> None:
        """Test that citation numbers are assigned by creation order."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_sources_with_citations,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create sources with different types but track order
        types_in_order = [
            SourceType.ACADEMIC,
            SourceType.PRIMARY,
            SourceType.GOVERNMENT,
        ]
        for i, source_type in enumerate(types_in_order):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title=f"Source Order {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        cited_sources = await get_sources_with_citations(db_session, fact_check.id)

        # Verify order matches creation order
        assert cited_sources[0]["source"].source_type == SourceType.ACADEMIC
        assert cited_sources[0]["citation_number"] == 1
        assert cited_sources[1]["source"].source_type == SourceType.PRIMARY
        assert cited_sources[1]["citation_number"] == 2
        assert cited_sources[2]["source"].source_type == SourceType.GOVERNMENT
        assert cited_sources[2]["citation_number"] == 3

    @pytest.mark.asyncio
    async def test_format_citation_string(self, db_session: AsyncSession) -> None:
        """Test formatting a citation string [1], [2], etc."""
        from app.services.source_service import format_citation

        assert format_citation(1) == "[1]"
        assert format_citation(2) == "[2]"
        assert format_citation(10) == "[10]"
        assert format_citation(100) == "[100]"


class TestMinimumSourceValidation:
    """Tests for minimum 2-source validation before publishing."""

    @pytest.mark.asyncio
    async def test_validate_minimum_sources_passes_with_two(self, db_session: AsyncSession) -> None:
        """Test validation passes when fact-check has 2+ sources."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            validate_minimum_sources,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create two sources
        for i in range(2):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        # Should not raise - returns True
        result = await validate_minimum_sources(db_session, fact_check.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_minimum_sources_passes_with_more(
        self, db_session: AsyncSession
    ) -> None:
        """Test validation passes when fact-check has more than 2 sources."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            validate_minimum_sources,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create five sources
        for i in range(5):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        result = await validate_minimum_sources(db_session, fact_check.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_minimum_sources_fails_with_one(self, db_session: AsyncSession) -> None:
        """Test validation fails when fact-check has only 1 source."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            InsufficientSourcesError,
            create_source,
            validate_minimum_sources,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create only one source
        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Only Source",
            access_date=date(2025, 12, 28),
        )
        await create_source(db_session, source_data)

        with pytest.raises(InsufficientSourcesError) as exc_info:
            await validate_minimum_sources(db_session, fact_check.id)

        assert "2" in str(exc_info.value)  # Should mention minimum of 2
        assert "1" in str(exc_info.value)  # Should mention current count

    @pytest.mark.asyncio
    async def test_validate_minimum_sources_fails_with_zero(self, db_session: AsyncSession) -> None:
        """Test validation fails when fact-check has no sources."""
        from app.services.source_service import (
            InsufficientSourcesError,
            validate_minimum_sources,
        )

        fact_check = await create_test_fact_check(db_session)

        with pytest.raises(InsufficientSourcesError) as exc_info:
            await validate_minimum_sources(db_session, fact_check.id)

        assert "2" in str(exc_info.value)  # Should mention minimum of 2
        assert "0" in str(exc_info.value)  # Should mention current count

    @pytest.mark.asyncio
    async def test_get_source_count_for_fact_check(self, db_session: AsyncSession) -> None:
        """Test getting source count for a fact-check."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source, get_source_count

        fact_check = await create_test_fact_check(db_session)

        # Initially zero
        count = await get_source_count(db_session, fact_check.id)
        assert count == 0

        # Add sources
        for i in range(3):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        count = await get_source_count(db_session, fact_check.id)
        assert count == 3


class TestCredibilityScoring:
    """Tests for credibility scoring mechanism (1-5 scale)."""

    @pytest.mark.asyncio
    async def test_create_source_with_valid_credibility_scores(
        self, db_session: AsyncSession
    ) -> None:
        """Test that credibility scores 1-5 are valid."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        for score in [1, 2, 3, 4, 5]:
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source with score {score}",
                access_date=date(2025, 12, 28),
                credibility_score=score,
            )
            source = await create_source(db_session, source_data)
            assert source.credibility_score == score

    @pytest.mark.asyncio
    async def test_create_source_without_credibility_score(self, db_session: AsyncSession) -> None:
        """Test that credibility score is optional."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source without score",
            access_date=date(2025, 12, 28),
        )
        source = await create_source(db_session, source_data)
        assert source.credibility_score is None

    @pytest.mark.asyncio
    async def test_get_average_credibility_score(self, db_session: AsyncSession) -> None:
        """Test calculating average credibility score for a fact-check."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_average_credibility_score,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create sources with scores: 3, 4, 5 -> average = 4.0
        scores = [3, 4, 5]
        for i, score in enumerate(scores):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
                credibility_score=score,
            )
            await create_source(db_session, source_data)

        avg_score = await get_average_credibility_score(db_session, fact_check.id)
        assert avg_score == 4.0

    @pytest.mark.asyncio
    async def test_get_average_credibility_score_ignores_none(
        self, db_session: AsyncSession
    ) -> None:
        """Test that average credibility calculation ignores sources without scores."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_average_credibility_score,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create sources: score 4, score 5, no score -> average = 4.5
        source_with_score_4 = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source with score 4",
            access_date=date(2025, 12, 28),
            credibility_score=4,
        )
        await create_source(db_session, source_with_score_4)

        source_with_score_5 = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source with score 5",
            access_date=date(2025, 12, 28),
            credibility_score=5,
        )
        await create_source(db_session, source_with_score_5)

        source_without_score = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source without score",
            access_date=date(2025, 12, 28),
        )
        await create_source(db_session, source_without_score)

        avg_score = await get_average_credibility_score(db_session, fact_check.id)
        assert avg_score == 4.5

    @pytest.mark.asyncio
    async def test_get_average_credibility_score_no_scores(self, db_session: AsyncSession) -> None:
        """Test average credibility when no sources have scores."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_average_credibility_score,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create sources without scores
        for i in range(2):
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            await create_source(db_session, source_data)

        avg_score = await get_average_credibility_score(db_session, fact_check.id)
        assert avg_score is None

    @pytest.mark.asyncio
    async def test_get_average_credibility_score_no_sources(self, db_session: AsyncSession) -> None:
        """Test average credibility when fact-check has no sources."""
        from app.services.source_service import get_average_credibility_score

        fact_check = await create_test_fact_check(db_session)

        avg_score = await get_average_credibility_score(db_session, fact_check.id)
        assert avg_score is None

    @pytest.mark.asyncio
    async def test_get_sources_by_credibility_score(self, db_session: AsyncSession) -> None:
        """Test filtering sources by minimum credibility score."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import (
            create_source,
            get_sources_by_min_credibility,
        )

        fact_check = await create_test_fact_check(db_session)

        # Create sources with different scores
        for score in [1, 2, 3, 4, 5]:
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source score {score}",
                access_date=date(2025, 12, 28),
                credibility_score=score,
            )
            await create_source(db_session, source_data)

        # Get sources with score >= 4
        high_cred_sources = await get_sources_by_min_credibility(
            db_session, fact_check.id, min_score=4
        )
        assert len(high_cred_sources) == 2  # Scores 4 and 5


class TestSourceServiceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_source_with_long_title(self, db_session: AsyncSession) -> None:
        """Test creating a source with maximum length title (500 chars)."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        long_title = "A" * 500
        source_data = SourceCreate(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title=long_title,
            access_date=date(2025, 12, 28),
        )
        source = await create_source(db_session, source_data)

        assert len(source.title) == 500

    @pytest.mark.asyncio
    async def test_create_source_with_all_source_types(self, db_session: AsyncSession) -> None:
        """Test creating sources with each source type."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        for source_type in SourceType:
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title=f"{source_type.value} source",
                access_date=date(2025, 12, 28),
            )
            source = await create_source(db_session, source_data)
            assert source.source_type == source_type

    @pytest.mark.asyncio
    async def test_create_source_with_all_relevance_types(self, db_session: AsyncSession) -> None:
        """Test creating sources with each relevance type."""
        from app.schemas.source import SourceCreate
        from app.services.source_service import create_source

        fact_check = await create_test_fact_check(db_session)

        for relevance in SourceRelevance:
            source_data = SourceCreate(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source with {relevance.value} relevance",
                access_date=date(2025, 12, 28),
                relevance=relevance,
            )
            source = await create_source(db_session, source_data)
            assert source.relevance == relevance
