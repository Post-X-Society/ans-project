"""
Tests for Source model - TDD approach: Write tests FIRST
Issue #69: Database Schema: Sources Table
"""

from datetime import date, datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestSourceModel:
    """Tests for Source model"""

    @pytest.mark.asyncio
    async def test_create_source_with_all_fields(self, db_session: AsyncSession) -> None:
        """Test creating a source with all required and optional fields"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceRelevance, SourceType

        # Create prerequisite objects - Claim has content and source fields
        claim = Claim(
            content="Test claim content",
            source="user_submission",
        )
        db_session.add(claim)
        await db_session.flush()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.95,
            reasoning="Test reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.flush()

        # Create source with all fields
        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Primary Source Title",
            url="https://example.com/source",
            publication_date=date(2025, 1, 15),
            access_date=date(2025, 12, 22),
            credibility_score=5,
            relevance=SourceRelevance.SUPPORTS,
            archived_url="https://web.archive.org/example",
            notes="This is a verified primary source.",
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        assert source.id is not None
        assert isinstance(source.id, UUID)
        assert source.fact_check_id == fact_check.id
        assert source.source_type == SourceType.PRIMARY
        assert source.title == "Primary Source Title"
        assert source.url == "https://example.com/source"
        assert source.publication_date == date(2025, 1, 15)
        assert source.access_date == date(2025, 12, 22)
        assert source.credibility_score == 5
        assert source.relevance == SourceRelevance.SUPPORTS
        assert source.archived_url == "https://web.archive.org/example"
        assert source.notes == "This is a verified primary source."
        assert isinstance(source.created_at, datetime)
        assert isinstance(source.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_source_minimal_fields(self, db_session: AsyncSession) -> None:
        """Test creating a source with only required fields"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
            source="user_submission",
        )
        db_session.add(claim)
        await db_session.flush()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.85,
            reasoning="Test reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.flush()

        # Create source with only required fields
        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.SECONDARY,
            title="Secondary Source",
            access_date=date(2025, 12, 22),
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        assert source.id is not None
        assert source.source_type == SourceType.SECONDARY
        assert source.title == "Secondary Source"
        assert source.access_date == date(2025, 12, 22)
        # Optional fields should be None
        assert source.url is None
        assert source.publication_date is None
        assert source.credibility_score is None
        assert source.relevance is None
        assert source.archived_url is None
        assert source.notes is None

    @pytest.mark.asyncio
    async def test_source_types_enum(self, db_session: AsyncSession) -> None:
        """Test all source type enum values"""
        from app.models.source import SourceType

        expected_types = [
            "primary",
            "secondary",
            "expert",
            "media",
            "government",
            "academic",
        ]

        for source_type in SourceType:
            assert source_type.value in expected_types

        assert len(list(SourceType)) == 6

    @pytest.mark.asyncio
    async def test_source_relevance_enum(self, db_session: AsyncSession) -> None:
        """Test all source relevance enum values"""
        from app.models.source import SourceRelevance

        expected_relevance = ["supports", "contradicts", "contextualizes"]

        for relevance in SourceRelevance:
            assert relevance.value in expected_relevance

        assert len(list(SourceRelevance)) == 3

    @pytest.mark.asyncio
    async def test_credibility_score_valid_range(self, db_session: AsyncSession) -> None:
        """Test that credibility_score accepts values 1-5"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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
        await db_session.flush()

        # Test each valid credibility score
        for score in [1, 2, 3, 4, 5]:
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.EXPERT,
                title=f"Source with score {score}",
                access_date=date(2025, 12, 22),
                credibility_score=score,
            )
            db_session.add(source)

        await db_session.commit()

        # Query and verify all sources
        result = await db_session.execute(
            select(Source).where(Source.fact_check_id == fact_check.id)
        )
        sources = result.scalars().all()
        scores = [s.credibility_score for s in sources]

        assert 1 in scores
        assert 2 in scores
        assert 3 in scores
        assert 4 in scores
        assert 5 in scores

    @pytest.mark.asyncio
    async def test_source_relationship_to_fact_check(self, db_session: AsyncSession) -> None:
        """Test that sources have proper relationship with fact_check"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceRelevance, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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
        await db_session.flush()

        # Create multiple sources for the same fact_check
        source1 = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Primary Source",
            access_date=date(2025, 12, 22),
            relevance=SourceRelevance.SUPPORTS,
        )
        source2 = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.SECONDARY,
            title="Secondary Source",
            access_date=date(2025, 12, 22),
            relevance=SourceRelevance.CONTEXTUALIZES,
        )
        db_session.add_all([source1, source2])
        await db_session.commit()

        # Query sources by fact_check_id
        result = await db_session.execute(
            select(Source).where(Source.fact_check_id == fact_check.id)
        )
        sources = result.scalars().all()

        assert len(sources) == 2
        assert any(s.title == "Primary Source" for s in sources)
        assert any(s.title == "Secondary Source" for s in sources)

    @pytest.mark.asyncio
    async def test_source_fact_check_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting a fact_check cascades to sources"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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
        await db_session.flush()

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.MEDIA,
            title="Media Source",
            access_date=date(2025, 12, 22),
        )
        db_session.add(source)
        await db_session.commit()

        source_id = source.id

        # Delete the fact_check
        await db_session.delete(fact_check)
        await db_session.commit()

        # Verify source was deleted
        result = await db_session.execute(select(Source).where(Source.id == source_id))
        deleted_source = result.scalar_one_or_none()
        assert deleted_source is None

    @pytest.mark.asyncio
    async def test_source_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of Source"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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
        await db_session.flush()

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.GOVERNMENT,
            title="Government Source",
            access_date=date(2025, 12, 22),
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        repr_str = repr(source)
        assert "Source" in repr_str
        assert "GOVERNMENT" in repr_str or "government" in repr_str

    @pytest.mark.asyncio
    async def test_query_sources_by_type(self, db_session: AsyncSession) -> None:
        """Test querying sources by source_type"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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
        await db_session.flush()

        # Create sources with different types
        types = [
            SourceType.PRIMARY,
            SourceType.SECONDARY,
            SourceType.ACADEMIC,
            SourceType.ACADEMIC,
        ]
        for source_type in types:
            source = Source(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title=f"{source_type.value.title()} Source",
                access_date=date(2025, 12, 22),
            )
            db_session.add(source)
        await db_session.commit()

        # Query by type
        result = await db_session.execute(
            select(Source).where(Source.source_type == SourceType.ACADEMIC)
        )
        academic_sources = result.scalars().all()

        assert len(academic_sources) == 2

    @pytest.mark.asyncio
    async def test_query_sources_by_relevance(self, db_session: AsyncSession) -> None:
        """Test querying sources by relevance"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.source import Source, SourceRelevance, SourceType

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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
        await db_session.flush()

        # Create sources with different relevance
        relevances = [
            SourceRelevance.SUPPORTS,
            SourceRelevance.SUPPORTS,
            SourceRelevance.CONTRADICTS,
        ]
        for i, relevance in enumerate(relevances):
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 22),
                relevance=relevance,
            )
            db_session.add(source)
        await db_session.commit()

        # Query supporting sources
        result = await db_session.execute(
            select(Source).where(Source.relevance == SourceRelevance.SUPPORTS)
        )
        supporting_sources = result.scalars().all()

        assert len(supporting_sources) == 2


class TestFactCheckSourcesCount:
    """Tests for FactCheck sources_count column"""

    @pytest.mark.asyncio
    async def test_fact_check_sources_count_default(self, db_session: AsyncSession) -> None:
        """Test that sources_count defaults to 0"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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

        assert fact_check.sources_count == 0

    @pytest.mark.asyncio
    async def test_fact_check_sources_count_update(self, db_session: AsyncSession) -> None:
        """Test that sources_count can be updated"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck

        # Create prerequisite objects
        claim = Claim(
            content="Test claim content",
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

        # Update sources_count
        fact_check.sources_count = 5
        await db_session.commit()
        await db_session.refresh(fact_check)

        assert fact_check.sources_count == 5
