"""
PeerReviewService for managing peer review workflows.

Issue #64: Backend Peer Review Trigger Service
Issue #65: Backend Peer Review Consensus Logic (TDD)

This service implements:
- Automated detection logic for peer review triggers (Issue #64)
- Peer review submission and consensus checking (Issue #65)
- Self-review prevention mechanism
- 7-day timeout with automatic escalation
- Reviewer notifications

EFCSN requirements for peer review:
- Political/controversial claims
- Health/safety misinformation
- Claims with high engagement (>10k views)
- Manual flagging by editors
- Unanimous approval for publication
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fact_check import FactCheck
from app.models.peer_review import ApprovalStatus, PeerReview
from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType
from app.models.submission import Submission
from app.models.user import User

# ==============================================================================
# CUSTOM EXCEPTIONS
# ==============================================================================


class PeerReviewServiceError(Exception):
    """Base exception for Peer Review Service errors."""

    pass


class PeerReviewNotFoundError(PeerReviewServiceError):
    """Raised when a peer review or related entity is not found."""

    pass


class SelfReviewNotAllowedError(PeerReviewServiceError):
    """Raised when a user attempts to review their own fact check."""

    pass


# ==============================================================================
# DATA CLASSES FOR RESULTS
# ==============================================================================


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


@dataclass
class ConsensusResult:
    """
    Result of consensus check for peer reviews.

    Attributes:
        consensus_reached: Whether all reviews are complete (no pending)
        approved: Whether all reviews are approved (unanimous)
        total_reviews: Total number of peer reviews
        approved_count: Number of approved reviews
        rejected_count: Number of rejected reviews
        pending_count: Number of pending reviews
        needs_more_reviewers: True if below minimum reviewer threshold
    """

    consensus_reached: bool
    approved: bool = False
    total_reviews: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    needs_more_reviewers: bool = False


@dataclass
class EscalationResult:
    """
    Result of review escalation.

    Attributes:
        escalated: Whether escalation was successful
        escalated_to_id: UUID of the user review was escalated to
        error: Error message if escalation failed
    """

    escalated: bool
    escalated_to_id: Optional[UUID] = None
    error: Optional[str] = None


@dataclass
class BulkEscalationResult:
    """
    Result of bulk review escalation.

    Attributes:
        escalated_count: Number of reviews successfully escalated
        failed_count: Number of reviews that failed to escalate
        errors: List of error messages for failed escalations
    """

    escalated_count: int = 0
    failed_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class NotificationResult:
    """
    Result of sending a single notification.

    Attributes:
        attempted: Whether notification was attempted
        sent: Whether notification was sent successfully
        reviewer_email: Email address of the reviewer
        error: Error message if notification failed
    """

    attempted: bool
    sent: bool = False
    reviewer_email: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BulkNotificationResult:
    """
    Result of bulk notification sending.

    Attributes:
        notification_count: Number of notifications attempted
        sent_count: Number of notifications sent successfully
        notified_emails: List of email addresses notified
        errors: List of error messages for failed notifications
    """

    notification_count: int = 0
    sent_count: int = 0
    notified_emails: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


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

    # ==========================================================================
    # CONSENSUS LOGIC METHODS (Issue #65)
    # ==========================================================================

    async def submit_peer_review(
        self,
        fact_check_id: UUID,
        reviewer_id: UUID,
        approved: bool,
        comments: Optional[str] = None,
        author_id: Optional[UUID] = None,
    ) -> PeerReview:
        """
        Submit a peer review decision for a fact check.

        Creates a new peer review or updates an existing one if the reviewer
        has already submitted. Implements self-review prevention when author_id
        is provided.

        Args:
            fact_check_id: UUID of the fact check being reviewed
            reviewer_id: UUID of the user submitting the review
            approved: True for approval, False for rejection
            comments: Optional comments from the reviewer
            author_id: Optional UUID of the fact check author (for self-review check)

        Returns:
            The created or updated PeerReview

        Raises:
            PeerReviewNotFoundError: If fact check doesn't exist
            SelfReviewNotAllowedError: If reviewer is the author
        """
        # Self-review prevention
        if author_id is not None and author_id == reviewer_id:
            raise SelfReviewNotAllowedError(
                f"User {reviewer_id} cannot review their own fact check"
            )

        # Verify fact check exists
        fact_check = await self._get_fact_check(fact_check_id)
        if fact_check is None:
            raise PeerReviewNotFoundError(f"Fact check {fact_check_id} not found")

        # Check if reviewer already has a review for this fact check
        existing_review = await self._get_existing_review(fact_check_id, reviewer_id)

        if existing_review:
            # Update existing review
            existing_review.approval_status = (
                ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            )
            existing_review.comments = comments
            await self.db.commit()
            await self.db.refresh(existing_review)
            return existing_review

        # Create new review
        review = PeerReview(
            fact_check_id=fact_check_id,
            reviewer_id=reviewer_id,
            approval_status=(ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED),
            comments=comments,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)

        return review

    async def check_consensus(
        self,
        fact_check_id: UUID,
        min_reviewers: int = 1,
    ) -> ConsensusResult:
        """
        Check if consensus has been reached on a fact check.

        Consensus requires:
        1. All assigned reviewers have submitted their decision (no pending)
        2. All reviewers have approved (unanimous approval)
        3. Minimum number of reviewers have participated

        Args:
            fact_check_id: UUID of the fact check to check
            min_reviewers: Minimum number of reviewers required (default: 1)

        Returns:
            ConsensusResult with consensus status and vote counts
        """
        reviews = await self.get_reviews_for_fact_check(fact_check_id)

        if not reviews:
            return ConsensusResult(
                consensus_reached=False,
                approved=False,
                total_reviews=0,
                needs_more_reviewers=True,
            )

        # Count statuses
        approved_count = sum(1 for r in reviews if r.approval_status == ApprovalStatus.APPROVED)
        rejected_count = sum(1 for r in reviews if r.approval_status == ApprovalStatus.REJECTED)
        pending_count = sum(1 for r in reviews if r.approval_status == ApprovalStatus.PENDING)

        total_reviews = len(reviews)

        # Check if we need more reviewers
        needs_more_reviewers = total_reviews < min_reviewers

        # Consensus is reached when all reviews are complete (no pending)
        consensus_reached = pending_count == 0 and not needs_more_reviewers

        # Approved only if unanimous and all submitted
        approved = consensus_reached and rejected_count == 0 and approved_count > 0

        return ConsensusResult(
            consensus_reached=consensus_reached,
            approved=approved,
            total_reviews=total_reviews,
            approved_count=approved_count,
            rejected_count=rejected_count,
            pending_count=pending_count,
            needs_more_reviewers=needs_more_reviewers,
        )

    async def get_reviews_for_fact_check(
        self,
        fact_check_id: UUID,
    ) -> list[PeerReview]:
        """
        Get all peer reviews for a fact check.

        Args:
            fact_check_id: UUID of the fact check

        Returns:
            List of PeerReview objects
        """
        stmt = select(PeerReview).where(PeerReview.fact_check_id == fact_check_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def assign_reviewers(
        self,
        fact_check_id: UUID,
        reviewer_ids: list[UUID],
    ) -> list[PeerReview]:
        """
        Assign reviewers to a fact check by creating pending review records.

        If a reviewer is already assigned, their existing review is returned
        (no duplicates are created).

        Args:
            fact_check_id: UUID of the fact check
            reviewer_ids: List of user UUIDs to assign as reviewers

        Returns:
            List of created or existing PeerReview objects

        Raises:
            PeerReviewNotFoundError: If fact check doesn't exist
        """
        # Verify fact check exists
        fact_check = await self._get_fact_check(fact_check_id)
        if fact_check is None:
            raise PeerReviewNotFoundError(f"Fact check {fact_check_id} not found")

        reviews: list[PeerReview] = []

        for reviewer_id in reviewer_ids:
            # Check for existing assignment
            existing = await self._get_existing_review(fact_check_id, reviewer_id)

            if existing:
                reviews.append(existing)
            else:
                # Create new pending review
                review = PeerReview(
                    fact_check_id=fact_check_id,
                    reviewer_id=reviewer_id,
                    approval_status=ApprovalStatus.PENDING,
                )
                self.db.add(review)
                reviews.append(review)

        await self.db.commit()

        # Refresh all reviews
        for review in reviews:
            await self.db.refresh(review)

        return reviews

    # ==========================================================================
    # TIMEOUT AND ESCALATION METHODS (Issue #65)
    # ==========================================================================

    async def get_overdue_reviews(
        self,
        days: int = 7,
    ) -> list[PeerReview]:
        """
        Get all pending peer reviews that are overdue.

        A review is overdue if it has been pending for more than the specified
        number of days.

        Args:
            days: Number of days after which a pending review is considered overdue

        Returns:
            List of overdue PeerReview objects
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(PeerReview)
            .where(PeerReview.approval_status == ApprovalStatus.PENDING)
            .where(PeerReview.created_at <= cutoff)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def escalate_overdue_review(
        self,
        review_id: UUID,
        escalate_to_id: UUID,
        reason: str,
    ) -> EscalationResult:
        """
        Escalate an overdue review to another user (typically an admin).

        This reassigns the review to the escalation target and records
        the reason for escalation.

        Args:
            review_id: UUID of the review to escalate
            escalate_to_id: UUID of the user to escalate to
            reason: Reason for the escalation

        Returns:
            EscalationResult with escalation status
        """
        # Get the review
        stmt = select(PeerReview).where(PeerReview.id == review_id)
        result = await self.db.execute(stmt)
        review = result.scalar_one_or_none()

        if review is None:
            return EscalationResult(
                escalated=False,
                error=f"Review {review_id} not found",
            )

        # Update the review with escalation info
        # Store the original reviewer in comments for audit trail
        escalation_note = f"ESCALATED: {reason}. Original reviewer: {review.reviewer_id}"
        if review.comments:
            review.comments = f"{review.comments}\n\n{escalation_note}"
        else:
            review.comments = escalation_note

        # Reassign to escalation target
        review.reviewer_id = escalate_to_id

        await self.db.commit()
        await self.db.refresh(review)

        return EscalationResult(
            escalated=True,
            escalated_to_id=escalate_to_id,
        )

    async def bulk_escalate_overdue(
        self,
        escalate_to_id: UUID,
        days: int = 7,
    ) -> BulkEscalationResult:
        """
        Escalate all overdue reviews to a specified user.

        Args:
            escalate_to_id: UUID of the user to escalate all reviews to
            days: Number of days threshold for considering a review overdue

        Returns:
            BulkEscalationResult with counts and any errors
        """
        overdue_reviews = await self.get_overdue_reviews(days=days)

        result = BulkEscalationResult()

        for review in overdue_reviews:
            escalation = await self.escalate_overdue_review(
                review_id=review.id,
                escalate_to_id=escalate_to_id,
                reason=f"Review overdue by more than {days} days",
            )

            if escalation.escalated:
                result.escalated_count += 1
            else:
                result.failed_count += 1
                if escalation.error:
                    result.errors.append(escalation.error)

        return result

    # ==========================================================================
    # NOTIFICATION METHODS (Issue #65)
    # ==========================================================================

    async def send_pending_review_notification(
        self,
        review_id: UUID,
    ) -> NotificationResult:
        """
        Send a notification to a reviewer about their pending review.

        Args:
            review_id: UUID of the pending review

        Returns:
            NotificationResult with notification status
        """
        from app.services.email_service import EmailService

        # Get the review with reviewer info
        stmt = select(PeerReview).where(PeerReview.id == review_id)
        result = await self.db.execute(stmt)
        review = result.scalar_one_or_none()

        if review is None:
            return NotificationResult(
                attempted=False,
                error=f"Review {review_id} not found",
            )

        # Get the reviewer
        reviewer_stmt = select(User).where(User.id == review.reviewer_id)
        reviewer_result = await self.db.execute(reviewer_stmt)
        reviewer = reviewer_result.scalar_one_or_none()

        if reviewer is None:
            return NotificationResult(
                attempted=False,
                error=f"Reviewer {review.reviewer_id} not found",
            )

        # Attempt to send email
        email_service = EmailService()

        subject = "[AnsCheckt] Peer Review Pending - Action Required"
        body_html = """
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Peer Review Pending</h2>
            <p>You have a pending peer review awaiting your decision.</p>
            <p>Please log in to the AnsCheckt platform to complete your review.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from AnsCheckt.
            </p>
        </body>
        </html>
        """

        sent = email_service.send_email(
            to_email=reviewer.email,
            subject=subject,
            body_html=body_html,
        )

        return NotificationResult(
            attempted=True,
            sent=sent,
            reviewer_email=reviewer.email,
            error=None if sent else "Failed to send email",
        )

    async def notify_pending_reviewers(
        self,
        fact_check_id: UUID,
    ) -> BulkNotificationResult:
        """
        Send notifications to all pending reviewers for a fact check.

        Only notifies reviewers with PENDING status.

        Args:
            fact_check_id: UUID of the fact check

        Returns:
            BulkNotificationResult with notification counts
        """
        # Get all pending reviews for this fact check
        stmt = (
            select(PeerReview)
            .where(PeerReview.fact_check_id == fact_check_id)
            .where(PeerReview.approval_status == ApprovalStatus.PENDING)
        )
        result = await self.db.execute(stmt)
        pending_reviews = list(result.scalars().all())

        bulk_result = BulkNotificationResult()
        bulk_result.notification_count = len(pending_reviews)

        for review in pending_reviews:
            notification = await self.send_pending_review_notification(review.id)

            if notification.sent:
                bulk_result.sent_count += 1
                if notification.reviewer_email:
                    bulk_result.notified_emails.append(notification.reviewer_email)
            elif notification.error:
                bulk_result.errors.append(notification.error)

        return bulk_result

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    async def _get_fact_check(self, fact_check_id: UUID) -> Optional[FactCheck]:
        """Get a fact check by ID."""
        stmt = select(FactCheck).where(FactCheck.id == fact_check_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_existing_review(
        self,
        fact_check_id: UUID,
        reviewer_id: UUID,
    ) -> Optional[PeerReview]:
        """Get an existing review by fact check and reviewer."""
        stmt = (
            select(PeerReview)
            .where(PeerReview.fact_check_id == fact_check_id)
            .where(PeerReview.reviewer_id == reviewer_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
