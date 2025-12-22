"""
PeerReviewTrigger model for configuring when peer review is required
Issue #63: Database Schema for Peer Review Tables
"""

import enum
from typing import Any, Optional

from sqlalchemy import Boolean, Enum, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

# Cross-database compatible JSON type
# Uses JSONB for PostgreSQL (production), JSON for SQLite (tests)
JSONType = JSON().with_variant(JSONB, "postgresql")


class TriggerType(str, enum.Enum):
    """Trigger type enumeration for peer review triggers"""

    POLITICAL_KEYWORD = "political_keyword"
    ENGAGEMENT_THRESHOLD = "engagement_threshold"
    SENSITIVE_TOPIC = "sensitive_topic"
    HIGH_IMPACT = "high_impact"


class PeerReviewTrigger(TimeStampedModel):
    """
    PeerReviewTrigger model for configuring when peer review is required.

    This model stores the configuration for automatic peer review triggers.
    When content matches a trigger condition, it will automatically require
    peer review before completion.

    Trigger types:
    - POLITICAL_KEYWORD: Triggers on political keywords in content
    - ENGAGEMENT_THRESHOLD: Triggers when engagement metrics exceed thresholds
    - SENSITIVE_TOPIC: Triggers on sensitive topics (health, safety, etc.)
    - HIGH_IMPACT: Triggers on high-impact content based on scoring

    Attributes:
        trigger_type: Type of trigger (political_keyword, engagement_threshold, etc.)
        enabled: Whether this trigger is currently active
        threshold_value: JSON configuration for the trigger (keywords, thresholds, etc.)
        description: Optional human-readable description of the trigger
    """

    __tablename__ = "peer_review_triggers"

    # Trigger type
    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )

    # Whether this trigger is enabled
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Threshold value (JSON) - contains trigger-specific configuration
    threshold_value: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=True,
    )

    # Optional description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<PeerReviewTrigger(id={self.id}, "
            f"type={self.trigger_type.value}, enabled={self.enabled})>"
        )


# Default triggers to seed
DEFAULT_TRIGGERS: list[dict[str, Any]] = [
    {
        "trigger_type": TriggerType.POLITICAL_KEYWORD,
        "enabled": True,
        "threshold_value": {
            "keywords": [
                "election",
                "vote",
                "politician",
                "referendum",
                "parliament",
                "government",
                "political party",
                "campaign",
                "ballot",
                "democracy",
            ],
            "min_occurrences": 1,
            "case_sensitive": False,
        },
        "description": "Triggers peer review for content containing political keywords",
    },
    {
        "trigger_type": TriggerType.ENGAGEMENT_THRESHOLD,
        "enabled": True,
        "threshold_value": {
            "min_views": 10000,
            "min_shares": 500,
            "min_comments": 100,
        },
        "description": "Triggers peer review for high-engagement content",
    },
    {
        "trigger_type": TriggerType.SENSITIVE_TOPIC,
        "enabled": True,
        "threshold_value": {
            "topics": [
                "health",
                "medicine",
                "vaccination",
                "public safety",
                "emergency",
                "crisis",
            ],
            "severity_threshold": 0.7,
        },
        "description": "Triggers peer review for sensitive health and safety topics",
    },
    {
        "trigger_type": TriggerType.HIGH_IMPACT,
        "enabled": True,
        "threshold_value": {
            "impact_score_threshold": 0.8,
            "viral_potential_threshold": 0.7,
        },
        "description": "Triggers peer review for high-impact content with viral potential",
    },
]


async def seed_default_triggers(session: AsyncSession) -> None:
    """
    Seed the default peer review triggers.

    This function is idempotent - it will only create triggers that don't
    already exist (checked by trigger_type and description combination).

    Args:
        session: The async database session
    """
    for trigger_data in DEFAULT_TRIGGERS:
        # Check if this trigger already exists (by type and description)
        result = await session.execute(
            select(PeerReviewTrigger).where(
                PeerReviewTrigger.trigger_type == trigger_data["trigger_type"],
                PeerReviewTrigger.description == trigger_data["description"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            trigger = PeerReviewTrigger(
                trigger_type=trigger_data["trigger_type"],
                enabled=trigger_data["enabled"],
                threshold_value=trigger_data["threshold_value"],
                description=trigger_data["description"],
            )
            session.add(trigger)

    await session.commit()
