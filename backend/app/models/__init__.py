"""
Database models package
Import all models here so Alembic can discover them
"""

from app.models.analytics_event import AnalyticsEvent
from app.models.base import Base, TimeStampedModel
from app.models.claim import Claim
from app.models.correction import (
    Correction,
    CorrectionApplication,
    CorrectionStatus,
    CorrectionType,
)
from app.models.email_log import EmailLog, EmailStatus
from app.models.email_template import EmailTemplate, EmailTemplateType
from app.models.fact_check import FactCheck
from app.models.fact_check_rating import FactCheckRating
from app.models.peer_review import ApprovalStatus, PeerReview
from app.models.peer_review_trigger import (
    PeerReviewTrigger,
    TriggerType,
    seed_default_triggers,
)
from app.models.rating_definition import RatingDefinition
from app.models.rtbf_request import RTBFRequest, RTBFRequestStatus
from app.models.source import Source, SourceRelevance, SourceType
from app.models.spotlight import SpotlightContent
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.transparency_page import (
    TransparencyPage,
    TransparencyPageVersion,
    seed_transparency_pages,
)
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
    "Correction",
    "CorrectionApplication",
    "CorrectionType",
    "CorrectionStatus",
    "RTBFRequest",
    "RTBFRequestStatus",
    "EmailLog",
    "EmailStatus",
    "EmailTemplate",
    "EmailTemplateType",
    "PeerReview",
    "ApprovalStatus",
    "PeerReviewTrigger",
    "TriggerType",
    "seed_default_triggers",
    "RatingDefinition",
    "Source",
    "SourceType",
    "SourceRelevance",
    "Volunteer",
    "WorkflowState",
    "WorkflowTransition",
    "TransparencyPage",
    "TransparencyPageVersion",
    "seed_transparency_pages",
]
