"""
Database models package
Import all models here so Alembic can discover them
"""
from app.models.base import Base, TimeStampedModel
from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.models.volunteer import Volunteer

__all__ = [
    "Base",
    "TimeStampedModel",
    "User",
    "UserRole",
    "Submission",
    "Claim",
    "FactCheck",
    "Volunteer",
]
