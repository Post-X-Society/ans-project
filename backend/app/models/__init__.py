"""
Database models package
Import all models here so Alembic can discover them
"""

from app.models.analytics_event import AnalyticsEvent
from app.models.base import Base, TimeStampedModel
from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.fact_check_rating import FactCheckRating
from app.models.peer_review import ApprovalStatus, PeerReview
from app.models.peer_review_trigger import (
    PeerReviewTrigger,
    TriggerType,
    seed_default_triggers,
)
from app.models.rating_definition import RatingDefinition
from app.models.spotlight import SpotlightContent
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole
from app.models.volunteer import Volunteer
from app.models.workflow_transition import WorkflowState, WorkflowTransition

__all__ = [
    "AnalyticsEvent",
    "Base",
    "TimeStampedModel",
    "User",
    "UserRole",
    "Submission",
    "SubmissionReviewer",
    "SpotlightContent",
    "Claim",
    "FactCheck",
    "FactCheckRating",
    "PeerReview",
    "ApprovalStatus",
    "PeerReviewTrigger",
    "TriggerType",
    "seed_default_triggers",
    "RatingDefinition",
    "Volunteer",
    "WorkflowState",
    "WorkflowTransition",
]
