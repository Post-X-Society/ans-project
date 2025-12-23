"""
FactCheck model for verified fact-check results
"""

import json
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.fact_check_rating import FactCheckRating
    from app.models.peer_review import PeerReview
    from app.models.source import Source


class StringList(TypeDecorator[list[str]]):
    """Custom type that stores list of strings as JSON in SQLite, ARRAY in PostgreSQL"""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[list[str]], dialect: Dialect) -> Optional[str]:
        if dialect.name == "postgresql":
            return value  # type: ignore[return-value]
        elif value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[list[str]]:
        if dialect.name == "postgresql":
            return value  # type: ignore[return-value]
        elif value is not None:
            result: list[str] = json.loads(value)
            return result
        return None


class FactCheck(TimeStampedModel):
    """FactCheck model for storing verified fact-check results"""

    __tablename__ = "fact_checks"

    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claims.id"), nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # true, false, partially_true, unverified
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[str]] = mapped_column(
        StringList, nullable=False
    )  # URLs to fact-check sources

    # Source count for EFCSN compliance (Issue #69)
    sources_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="fact_checks", lazy="selectin")
    ratings: Mapped[List["FactCheckRating"]] = relationship(
        "FactCheckRating",
        back_populates="fact_check",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    peer_reviews: Mapped[List["PeerReview"]] = relationship(
        "PeerReview",
        back_populates="fact_check",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    source_records: Mapped[List["Source"]] = relationship(
        "Source",
        back_populates="fact_check",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FactCheck(id={self.id}, verdict={self.verdict}, confidence={self.confidence})>"
