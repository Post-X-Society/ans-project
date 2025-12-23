"""
Tests for AnalyticsEvent model - TDD approach: Write tests FIRST

This test module validates the analytics_events table for EFCSN compliance.
The table tracks all analytics events (views, shares, corrections, etc.)
for compliance dashboard metrics.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestAnalyticsEventModel:
    """Tests for AnalyticsEvent model"""

    @pytest.mark.asyncio
    async def test_create_analytics_event(self, db_session: AsyncSession) -> None:
        """Test creating an analytics event with all required fields"""
        from app.models.analytics_event import AnalyticsEvent

        event = AnalyticsEvent(
            event_type="view",
            entity_type="fact_check",
            entity_id=uuid4(),
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        assert event.id is not None
        assert isinstance(event.id, UUID)
        assert event.event_type == "view"
        assert event.entity_type == "fact_check"
        assert event.entity_id is not None
        assert isinstance(event.occurred_at, datetime)
        assert isinstance(event.created_at, datetime)
        assert isinstance(event.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_analytics_event_with_metadata(self, db_session: AsyncSession) -> None:
        """Test creating an analytics event with optional JSONB metadata"""
        from app.models.analytics_event import AnalyticsEvent

        metadata = {
            "user_agent": "Mozilla/5.0",
            "referrer": "https://example.com",
            "ip_country": "NL",
        }

        event = AnalyticsEvent(
            event_type="share",
            entity_type="submission",
            entity_id=uuid4(),
            event_metadata=metadata,
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        assert event.event_metadata is not None
        assert event.event_metadata["user_agent"] == "Mozilla/5.0"
        assert event.event_metadata["referrer"] == "https://example.com"
        assert event.event_metadata["ip_country"] == "NL"

    @pytest.mark.asyncio
    async def test_analytics_event_with_custom_occurred_at(self, db_session: AsyncSession) -> None:
        """Test creating an analytics event with explicit occurred_at timestamp"""
        from app.models.analytics_event import AnalyticsEvent

        custom_time = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        event = AnalyticsEvent(
            event_type="correction_request",
            entity_type="fact_check",
            entity_id=uuid4(),
            occurred_at=custom_time,
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        # SQLite returns timezone-naive datetimes, so compare without tzinfo
        assert event.occurred_at == custom_time.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_analytics_event_types(self, db_session: AsyncSession) -> None:
        """Test creating analytics events with different event types"""
        from app.models.analytics_event import AnalyticsEvent

        event_types = [
            "view",
            "share",
            "correction_request",
            "download",
            "embed",
            "api_access",
        ]

        for event_type in event_types:
            event = AnalyticsEvent(
                event_type=event_type,
                entity_type="fact_check",
                entity_id=uuid4(),
            )
            db_session.add(event)

        await db_session.commit()

        # Verify all events were created
        result = await db_session.execute(select(AnalyticsEvent))
        events = result.scalars().all()
        assert len(events) == len(event_types)

    @pytest.mark.asyncio
    async def test_analytics_event_entity_types(self, db_session: AsyncSession) -> None:
        """Test creating analytics events for different entity types"""
        from app.models.analytics_event import AnalyticsEvent

        entity_types = [
            "fact_check",
            "submission",
            "claim",
            "user",
            "transparency_page",
        ]

        for entity_type in entity_types:
            event = AnalyticsEvent(
                event_type="view",
                entity_type=entity_type,
                entity_id=uuid4(),
            )
            db_session.add(event)

        await db_session.commit()

        # Verify all events were created
        result = await db_session.execute(select(AnalyticsEvent))
        events = result.scalars().all()
        assert len(events) == len(entity_types)

    @pytest.mark.asyncio
    async def test_query_by_entity_type_and_id(self, db_session: AsyncSession) -> None:
        """Test querying analytics events by entity type and entity ID"""
        from app.models.analytics_event import AnalyticsEvent

        target_entity_id = uuid4()
        other_entity_id = uuid4()

        # Create events for target entity
        for _ in range(3):
            event = AnalyticsEvent(
                event_type="view",
                entity_type="fact_check",
                entity_id=target_entity_id,
            )
            db_session.add(event)

        # Create event for other entity
        other_event = AnalyticsEvent(
            event_type="view",
            entity_type="fact_check",
            entity_id=other_entity_id,
        )
        db_session.add(other_event)

        await db_session.commit()

        # Query by entity_id
        result = await db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.entity_id == target_entity_id)
        )
        events = result.scalars().all()
        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_query_by_event_type(self, db_session: AsyncSession) -> None:
        """Test querying analytics events by event type"""
        from app.models.analytics_event import AnalyticsEvent

        # Create view events
        for _ in range(5):
            db_session.add(
                AnalyticsEvent(
                    event_type="view",
                    entity_type="fact_check",
                    entity_id=uuid4(),
                )
            )

        # Create share events
        for _ in range(2):
            db_session.add(
                AnalyticsEvent(
                    event_type="share",
                    entity_type="fact_check",
                    entity_id=uuid4(),
                )
            )

        await db_session.commit()

        # Query views
        result = await db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.event_type == "view")
        )
        view_events = result.scalars().all()
        assert len(view_events) == 5

        # Query shares
        result = await db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.event_type == "share")
        )
        share_events = result.scalars().all()
        assert len(share_events) == 2

    @pytest.mark.asyncio
    async def test_time_series_ordering(self, db_session: AsyncSession) -> None:
        """Test that analytics events can be ordered by occurred_at for time-series"""
        from app.models.analytics_event import AnalyticsEvent

        # Create events with different timestamps
        times = [
            datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
        ]

        for time in times:
            event = AnalyticsEvent(
                event_type="view",
                entity_type="fact_check",
                entity_id=uuid4(),
                occurred_at=time,
            )
            db_session.add(event)

        await db_session.commit()

        # Query ordered by occurred_at ascending
        result = await db_session.execute(
            select(AnalyticsEvent).order_by(AnalyticsEvent.occurred_at.asc())
        )
        events = result.scalars().all()

        assert len(events) == 3
        # SQLite returns timezone-naive datetimes, so compare without tzinfo
        assert events[0].occurred_at == times[0].replace(tzinfo=None)
        assert events[1].occurred_at == times[1].replace(tzinfo=None)
        assert events[2].occurred_at == times[2].replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_analytics_event_repr(self, db_session: AsyncSession) -> None:
        """Test the string representation of an analytics event"""
        from app.models.analytics_event import AnalyticsEvent

        event = AnalyticsEvent(
            event_type="view",
            entity_type="fact_check",
            entity_id=uuid4(),
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        repr_str = repr(event)
        assert "AnalyticsEvent" in repr_str
        assert "view" in repr_str
        assert "fact_check" in repr_str

    @pytest.mark.asyncio
    async def test_metadata_with_nested_structure(self, db_session: AsyncSession) -> None:
        """Test that metadata supports nested JSON structures"""
        from app.models.analytics_event import AnalyticsEvent

        complex_metadata = {
            "user_info": {
                "browser": "Chrome",
                "platform": "Windows",
                "version": "120.0",
            },
            "context": {
                "page": "/fact-checks/123",
                "referrer": "https://google.com",
            },
            "tracking": {
                "session_id": "abc123",
                "page_views": 5,
            },
        }

        event = AnalyticsEvent(
            event_type="view",
            entity_type="fact_check",
            entity_id=uuid4(),
            event_metadata=complex_metadata,
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        assert event.event_metadata is not None
        assert event.event_metadata["user_info"]["browser"] == "Chrome"
        assert event.event_metadata["context"]["page"] == "/fact-checks/123"
        assert event.event_metadata["tracking"]["page_views"] == 5

    @pytest.mark.asyncio
    async def test_null_metadata_allowed(self, db_session: AsyncSession) -> None:
        """Test that metadata can be null/None"""
        from app.models.analytics_event import AnalyticsEvent

        event = AnalyticsEvent(
            event_type="view",
            entity_type="fact_check",
            entity_id=uuid4(),
            event_metadata=None,
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        assert event.event_metadata is None
