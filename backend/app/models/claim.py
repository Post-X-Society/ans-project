"""
Claim model for extracted claims with vector embeddings
"""
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.fact_check import FactCheck


class Claim(TimeStampedModel):
    """Claim model for storing extracted claims with embeddings for similarity search"""

    __tablename__ = "claims"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # Where claim came from
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True
    )  # text-embedding-3-small dimension

    # Relationships
    fact_checks: Mapped[list["FactCheck"]] = relationship(
        "FactCheck", back_populates="claim", lazy="selectin"
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Claim(id={self.id}, content='{content_preview}')>"
