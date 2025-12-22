"""
Tests for PeerReviewTrigger model - TDD approach: Write tests FIRST
Issue #63: Database Schema for Peer Review Tables
"""

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestPeerReviewTriggerModel:
    """Tests for PeerReviewTrigger model - configures when peer review is required"""

    @pytest.mark.asyncio
    async def test_create_peer_review_trigger(self, db_session: AsyncSession) -> None:
        """Test creating a peer review trigger with all required fields"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election", "vote", "politician"]},
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert trigger.id is not None
        assert isinstance(trigger.id, UUID)
        assert trigger.trigger_type == TriggerType.POLITICAL_KEYWORD
        assert trigger.enabled is True
        assert trigger.threshold_value == {"keywords": ["election", "vote", "politician"]}
        assert isinstance(trigger.created_at, datetime)
        assert isinstance(trigger.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_peer_review_trigger_all_types(self, db_session: AsyncSession) -> None:
        """Test all trigger type values"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        # Test each trigger type
        triggers_data = [
            (TriggerType.POLITICAL_KEYWORD, {"keywords": ["politics", "election"]}),
            (TriggerType.ENGAGEMENT_THRESHOLD, {"min_views": 10000}),
            (TriggerType.SENSITIVE_TOPIC, {"topics": ["health", "safety"]}),
            (TriggerType.HIGH_IMPACT, {"impact_score": 0.8}),
        ]

        for trigger_type, threshold_value in triggers_data:
            trigger = PeerReviewTrigger(
                trigger_type=trigger_type,
                enabled=True,
                threshold_value=threshold_value,
            )
            db_session.add(trigger)
            await db_session.commit()
            await db_session.refresh(trigger)

            assert trigger.trigger_type == trigger_type
            assert trigger.threshold_value == threshold_value

    @pytest.mark.asyncio
    async def test_peer_review_trigger_enabled_default(self, db_session: AsyncSession) -> None:
        """Test that enabled defaults to True"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        # Create trigger without specifying enabled
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            threshold_value={"keywords": ["test"]},
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert trigger.enabled is True

    @pytest.mark.asyncio
    async def test_peer_review_trigger_can_be_disabled(self, db_session: AsyncSession) -> None:
        """Test that triggers can be disabled"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=False,
            threshold_value={"min_views": 5000},
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert trigger.enabled is False

    @pytest.mark.asyncio
    async def test_peer_review_trigger_threshold_value_types(
        self, db_session: AsyncSession
    ) -> None:
        """Test that threshold_value supports various JSON structures"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        # Test with nested structure
        complex_threshold: dict[str, Any] = {
            "keywords": ["election", "vote"],
            "min_occurrences": 3,
            "case_sensitive": False,
            "weight": 1.5,
        }

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value=complex_threshold,
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert trigger.threshold_value == complex_threshold
        assert trigger.threshold_value["keywords"] == ["election", "vote"]
        assert trigger.threshold_value["min_occurrences"] == 3
        assert trigger.threshold_value["case_sensitive"] is False
        assert trigger.threshold_value["weight"] == 1.5

    @pytest.mark.asyncio
    async def test_peer_review_trigger_nullable_threshold(self, db_session: AsyncSession) -> None:
        """Test that threshold_value can be null for simple triggers"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.HIGH_IMPACT,
            enabled=True,
            threshold_value=None,
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert trigger.threshold_value is None

    @pytest.mark.asyncio
    async def test_peer_review_trigger_description(self, db_session: AsyncSession) -> None:
        """Test that triggers can have optional description"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
            description="Trigger peer review for content containing political keywords",
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert (
            trigger.description == "Trigger peer review for content containing political keywords"
        )

    @pytest.mark.asyncio
    async def test_peer_review_trigger_nullable_description(self, db_session: AsyncSession) -> None:
        """Test that description is nullable"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=True,
            threshold_value={"min_views": 1000},
            description=None,
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        assert trigger.description is None

    @pytest.mark.asyncio
    async def test_peer_review_trigger_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of PeerReviewTrigger"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["test"]},
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        repr_str = repr(trigger)
        assert "PeerReviewTrigger" in repr_str
        assert str(trigger.id) in repr_str
        assert "political_keyword" in repr_str
        assert "enabled=True" in repr_str

    @pytest.mark.asyncio
    async def test_multiple_triggers_same_type(self, db_session: AsyncSession) -> None:
        """Test that multiple triggers of the same type can exist"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        trigger1 = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
            description="Primary political keyword trigger",
        )
        trigger2 = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["referendum"]},
            description="Secondary political keyword trigger",
        )
        db_session.add_all([trigger1, trigger2])
        await db_session.commit()

        result = await db_session.execute(
            select(PeerReviewTrigger).where(
                PeerReviewTrigger.trigger_type == TriggerType.POLITICAL_KEYWORD
            )
        )
        triggers = result.scalars().all()
        assert len(triggers) == 2

    @pytest.mark.asyncio
    async def test_query_enabled_triggers(self, db_session: AsyncSession) -> None:
        """Test querying only enabled triggers"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        enabled_trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["enabled"]},
        )
        disabled_trigger = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=False,
            threshold_value={"min_views": 1000},
        )
        db_session.add_all([enabled_trigger, disabled_trigger])
        await db_session.commit()

        result = await db_session.execute(
            select(PeerReviewTrigger).where(PeerReviewTrigger.enabled.is_(True))
        )
        enabled_triggers = result.scalars().all()
        assert len(enabled_triggers) == 1
        assert enabled_triggers[0].trigger_type == TriggerType.POLITICAL_KEYWORD

    @pytest.mark.asyncio
    async def test_query_triggers_by_type(self, db_session: AsyncSession) -> None:
        """Test querying triggers by type"""
        from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType

        political_trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["politics"]},
        )
        engagement_trigger = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=True,
            threshold_value={"min_views": 5000},
        )
        db_session.add_all([political_trigger, engagement_trigger])
        await db_session.commit()

        result = await db_session.execute(
            select(PeerReviewTrigger).where(
                PeerReviewTrigger.trigger_type == TriggerType.ENGAGEMENT_THRESHOLD
            )
        )
        triggers = result.scalars().all()
        assert len(triggers) == 1
        assert triggers[0].threshold_value == {"min_views": 5000}


class TestTriggerTypeEnum:
    """Tests for TriggerType enum values"""

    def test_trigger_type_values(self) -> None:
        """Test that TriggerType has the expected values"""
        from app.models.peer_review_trigger import TriggerType

        assert TriggerType.POLITICAL_KEYWORD.value == "political_keyword"
        assert TriggerType.ENGAGEMENT_THRESHOLD.value == "engagement_threshold"
        assert TriggerType.SENSITIVE_TOPIC.value == "sensitive_topic"
        assert TriggerType.HIGH_IMPACT.value == "high_impact"

    def test_trigger_type_is_string_enum(self) -> None:
        """Test that TriggerType is a string enum"""
        from app.models.peer_review_trigger import TriggerType

        assert issubclass(TriggerType, enum.Enum)
        # Verify values are strings
        for trigger_type in TriggerType:
            assert isinstance(trigger_type.value, str)


class TestDefaultTriggerSeeding:
    """Tests for default trigger seeding functionality"""

    @pytest.mark.asyncio
    async def test_seed_default_triggers(self, db_session: AsyncSession) -> None:
        """Test that default triggers are seeded correctly"""
        from app.models.peer_review_trigger import (
            PeerReviewTrigger,
            TriggerType,
            seed_default_triggers,
        )

        # Seed the default triggers
        await seed_default_triggers(db_session)

        # Query all triggers
        result = await db_session.execute(select(PeerReviewTrigger))
        triggers = result.scalars().all()

        # Should have at least the default triggers
        assert len(triggers) >= 2

        # Check for political keyword trigger
        political_triggers = [
            t for t in triggers if t.trigger_type == TriggerType.POLITICAL_KEYWORD
        ]
        assert len(political_triggers) >= 1
        political = political_triggers[0]
        assert political.enabled is True
        assert "keywords" in political.threshold_value

        # Check for engagement threshold trigger
        engagement_triggers = [
            t for t in triggers if t.trigger_type == TriggerType.ENGAGEMENT_THRESHOLD
        ]
        assert len(engagement_triggers) >= 1
        engagement = engagement_triggers[0]
        assert engagement.enabled is True
        assert (
            "min_views" in engagement.threshold_value or "threshold" in engagement.threshold_value
        )

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(self, db_session: AsyncSession) -> None:
        """Test that seeding multiple times doesn't create duplicates"""
        from app.models.peer_review_trigger import PeerReviewTrigger, seed_default_triggers

        # Seed twice
        await seed_default_triggers(db_session)
        await seed_default_triggers(db_session)

        # Query all triggers
        result = await db_session.execute(select(PeerReviewTrigger))
        triggers = result.scalars().all()

        # Count should be same as after first seed (no duplicates)
        # The actual count depends on how many default triggers we define
        # but it should not double after second call
        await seed_default_triggers(db_session)
        result2 = await db_session.execute(select(PeerReviewTrigger))
        triggers2 = result2.scalars().all()

        assert len(triggers) == len(triggers2)
