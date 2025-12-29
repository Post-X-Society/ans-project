"""
PeerReviewService for determining when submissions require peer review.
Issue #64: Backend Peer Review Trigger Service

This service implements automated detection logic that identifies when
substantial claims warrant peer review validation per EFCSN requirements.

Trigger types:
- Political keyword detection (from DB triggers)
- Health/safety keyword detection (from DB triggers)
- Engagement threshold validation (>10k views)
- Manual review initiation
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType
from app.models.submission import Submission


@dataclass
class PeerReviewTriggerResult:
    """
    Result of peer review trigger evaluation.

    Attributes:
        should_trigger: Whether peer review should be triggered
        triggered_by: List of trigger types that matched
        reasons: Human-readable reasons for the trigger
        confidence: Confidence score (0.0 to 1.0) based on number of triggers
    """

    should_trigger: bool
    triggered_by: list[TriggerType] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0


class PeerReviewService:
    """
    Service for managing peer review trigger logic.

    This service evaluates submissions against configurable triggers stored
    in the database and determines whether peer review is required.

    EFCSN requirements for peer review:
    - Political/controversial claims
    - Health/safety misinformation
    - Claims with high engagement (>10k views)
    - Manual flagging by editors
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the peer review service.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_enabled_triggers(
        self,
        trigger_type: Optional[TriggerType] = None,
    ) -> list[PeerReviewTrigger]:
        """
        Get all enabled triggers from the database.

        Args:
            trigger_type: Optional filter for specific trigger type

        Returns:
            List of enabled PeerReviewTrigger records
        """
        query = select(PeerReviewTrigger).where(PeerReviewTrigger.enabled.is_(True))

        if trigger_type is not None:
            query = query.where(PeerReviewTrigger.trigger_type == trigger_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def should_trigger_review(
        self,
        submission: Submission,
        engagement_metrics: Optional[dict[str, Any]] = None,
    ) -> PeerReviewTriggerResult:
        """
        Evaluate whether a submission requires peer review.

        This method checks the submission against all enabled triggers:
        1. Political keywords (POLITICAL_KEYWORD trigger type)
        2. Health/safety keywords (SENSITIVE_TOPIC trigger type)
        3. Engagement thresholds (ENGAGEMENT_THRESHOLD trigger type)
        4. Manual review flag (submission.requires_peer_review)

        Args:
            submission: The submission to evaluate
            engagement_metrics: Optional dict with 'views', 'shares', 'comments'

        Returns:
            PeerReviewTriggerResult with trigger evaluation results
        """
        triggered_by: list[TriggerType] = []
        reasons: list[str] = []

        # Check if manually flagged
        self._check_manual_flag(submission, triggered_by, reasons)

        # Get all enabled triggers and process them
        triggers = await self.get_enabled_triggers()
        self._process_triggers(triggers, submission, engagement_metrics, triggered_by, reasons)

        # Calculate confidence based on number of triggers
        should_trigger = len(triggered_by) > 0
        confidence = min(1.0, len(triggered_by) * 0.3) if should_trigger else 0.0

        return PeerReviewTriggerResult(
            should_trigger=should_trigger,
            triggered_by=triggered_by,
            reasons=reasons,
            confidence=confidence,
        )

    def _check_manual_flag(
        self,
        submission: Submission,
        triggered_by: list[TriggerType],
        reasons: list[str],
    ) -> None:
        """Check if submission is manually flagged for peer review."""
        if submission.requires_peer_review:
            triggered_by.append(TriggerType.HIGH_IMPACT)
            reason = "Manually flagged for peer review"
            if submission.peer_review_reason:
                reason = f"{reason}: {submission.peer_review_reason}"
            reasons.append(reason)

    def _process_triggers(
        self,
        triggers: list[PeerReviewTrigger],
        submission: Submission,
        engagement_metrics: Optional[dict[str, Any]],
        triggered_by: list[TriggerType],
        reasons: list[str],
    ) -> None:
        """Process all enabled triggers against the submission."""
        for trigger in triggers:
            result = self._evaluate_single_trigger(trigger, submission, engagement_metrics)
            if result:
                triggered_by.append(trigger.trigger_type)
                reasons.append(result)

    def _evaluate_single_trigger(
        self,
        trigger: PeerReviewTrigger,
        submission: Submission,
        engagement_metrics: Optional[dict[str, Any]],
    ) -> Optional[str]:
        """Evaluate a single trigger against the submission."""
        if trigger.trigger_type == TriggerType.POLITICAL_KEYWORD:
            return self._check_keyword_trigger(submission, trigger)
        elif trigger.trigger_type == TriggerType.SENSITIVE_TOPIC:
            return self._check_sensitive_topic_trigger(submission, trigger)
        elif trigger.trigger_type == TriggerType.ENGAGEMENT_THRESHOLD:
            if engagement_metrics:
                return self._check_engagement_trigger(engagement_metrics, trigger)
        return None

    def _check_keyword_trigger(
        self,
        submission: Submission,
        trigger: PeerReviewTrigger,
    ) -> Optional[str]:
        """
        Check if submission content matches political keyword trigger.

        Args:
            submission: The submission to check
            trigger: The keyword trigger configuration

        Returns:
            Reason string if triggered, None otherwise
        """
        if trigger.threshold_value is None:
            return None

        keywords = trigger.threshold_value.get("keywords", [])
        min_occurrences = trigger.threshold_value.get("min_occurrences", 1)
        case_sensitive = trigger.threshold_value.get("case_sensitive", False)

        content = submission.content
        if not case_sensitive:
            content = content.lower()
            keywords = [k.lower() for k in keywords]

        matched_keywords: list[str] = []
        for keyword in keywords:
            if keyword in content:
                matched_keywords.append(keyword)

        if len(matched_keywords) >= min_occurrences:
            return f"Contains political keywords: {', '.join(matched_keywords)}"

        return None

    def _check_sensitive_topic_trigger(
        self,
        submission: Submission,
        trigger: PeerReviewTrigger,
    ) -> Optional[str]:
        """
        Check if submission content matches sensitive topic trigger.

        Args:
            submission: The submission to check
            trigger: The sensitive topic trigger configuration

        Returns:
            Reason string if triggered, None otherwise
        """
        if trigger.threshold_value is None:
            return None

        topics = trigger.threshold_value.get("topics", [])
        content = submission.content.lower()

        matched_topics: list[str] = []
        for topic in topics:
            if topic.lower() in content:
                matched_topics.append(topic)

        if matched_topics:
            return f"Contains sensitive health/safety topics: {', '.join(matched_topics)}"

        return None

    def _check_engagement_trigger(
        self,
        engagement_metrics: dict[str, Any],
        trigger: PeerReviewTrigger,
    ) -> Optional[str]:
        """
        Check if engagement metrics exceed threshold trigger.

        Args:
            engagement_metrics: Dict with 'views', 'shares', 'comments'
            trigger: The engagement threshold trigger configuration

        Returns:
            Reason string if triggered, None otherwise
        """
        if trigger.threshold_value is None:
            return None

        min_views = trigger.threshold_value.get("min_views", 10000)
        min_shares = trigger.threshold_value.get("min_shares", 500)
        min_comments = trigger.threshold_value.get("min_comments", 100)

        views = engagement_metrics.get("views", 0)
        shares = engagement_metrics.get("shares", 0)
        comments = engagement_metrics.get("comments", 0)

        exceeded_thresholds: list[str] = []

        if views >= min_views:
            exceeded_thresholds.append(f"{views} views (threshold: {min_views})")

        if shares >= min_shares:
            exceeded_thresholds.append(f"{shares} shares (threshold: {min_shares})")

        if comments >= min_comments:
            exceeded_thresholds.append(f"{comments} comments (threshold: {min_comments})")

        if exceeded_thresholds:
            return f"Engagement exceeds thresholds: {', '.join(exceeded_thresholds)}"

        return None

    async def flag_for_manual_review(
        self,
        submission: Submission,
        reason: str,
    ) -> Submission:
        """
        Manually flag a submission for peer review.

        This is used when an editor wants to require peer review
        regardless of automatic trigger detection.

        Args:
            submission: The submission to flag
            reason: The reason for requiring peer review

        Returns:
            Updated submission with peer review flag set
        """
        submission.requires_peer_review = True
        submission.peer_review_reason = reason

        await self.db.commit()
        await self.db.refresh(submission)

        return submission
