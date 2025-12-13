"""
User model for authentication and authorization
"""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.volunteer import Volunteer


class User(TimeStampedModel):
    """User model for storing user authentication data"""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user"
    )  # user, volunteer, admin

    # Relationships
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission", back_populates="user", lazy="selectin"
    )
    volunteer: Mapped["Volunteer | None"] = relationship(
        "Volunteer", back_populates="user", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
