"""
Volunteer model for fact-checker profiles
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User


class Volunteer(TimeStampedModel):
    """Volunteer model for fact-checker profiles and statistics"""

    __tablename__ = "volunteers"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    verified_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0.0 to 1.0

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="volunteer", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Volunteer(id={self.id}, score={self.score}, verified={self.verified_count})>"
