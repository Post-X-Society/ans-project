"""
Spotlight model for Snapchat Spotlight content metadata
"""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.submission import Submission


class SpotlightContent(TimeStampedModel):
    """Model for storing Snapchat Spotlight content metadata and video info"""

    __tablename__ = "spotlight_contents"

    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("submissions.id"), nullable=False, unique=True, index=True
    )
    spotlight_link: Mapped[str] = mapped_column(String(500), nullable=False)
    spotlight_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Video metadata
    video_url: Mapped[str] = mapped_column(Text, nullable=False)
    video_local_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Creator metadata
    creator_username: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    creator_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    creator_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Engagement stats
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    share_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    boost_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommend_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Upload timestamp
    upload_timestamp: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Raw API response
    raw_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="spotlight_content", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SpotlightContent(id={self.id}, spotlight_id={self.spotlight_id})>"
