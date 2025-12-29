"""
Tests for PeerReviewService - TDD approach: Write tests FIRST
Issue #64: Backend Peer Review Trigger Service

This service determines when submissions require peer review based on:
1. Political keyword detection (from DB triggers)
2. Health/safety keyword detection (from DB triggers)
3. Engagement threshold validation (>10k views)
4. Manual review initiation
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType
from app.models.submission import Submission
from app.models.user import User, UserRole


class TestPeerReviewServiceTriggerResult:
    """Tests for PeerReviewTriggerResult data class"""

    def test_trigger_result_attributes(self) -> None:
        """Test that PeerReviewTriggerResult has all required attributes"""
        from app.services.peer_review_service import PeerReviewTriggerResult

        result = PeerReviewTriggerResult(
            should_trigger=True,
            triggered_by=[TriggerType.POLITICAL_KEYWORD],
            reasons=["Contains political keywords: election, vote"],
            confidence=0.9,
        )

        assert result.should_trigger is True
        assert TriggerType.POLITICAL_KEYWORD in result.triggered_by
        assert len(result.reasons) == 1
        assert result.confidence == 0.9

    def test_trigger_result_no_trigger(self) -> None:
        """Test PeerReviewTriggerResult when no trigger is matched"""
        from app.services.peer_review_service import PeerReviewTriggerResult

        result = PeerReviewTriggerResult(
            should_trigger=False,
            triggered_by=[],
            reasons=[],
            confidence=0.0,
        )

        assert result.should_trigger is False
        assert len(result.triggered_by) == 0
        assert len(result.reasons) == 0

    def test_trigger_result_multiple_triggers(self) -> None:
        """Test PeerReviewTriggerResult with multiple triggers"""
        from app.services.peer_review_service import PeerReviewTriggerResult

        result = PeerReviewTriggerResult(
            should_trigger=True,
            triggered_by=[
                TriggerType.POLITICAL_KEYWORD,
                TriggerType.ENGAGEMENT_THRESHOLD,
            ],
            reasons=[
                "Contains political keywords: election",
                "Engagement exceeds threshold: 15000 views > 10000",
            ],
            confidence=1.0,
        )

        assert result.should_trigger is True
        assert len(result.triggered_by) == 2
        assert len(result.reasons) == 2


class TestPeerReviewServiceInitialization:
    """Tests for PeerReviewService initialization"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, db_session: AsyncSession) -> None:
        """Test that PeerReviewService initializes correctly"""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        assert service.db == db_session


class TestShouldTriggerReviewPoliticalKeywords:
    """Tests for political keyword detection"""

    @pytest.fixture
    async def political_trigger(self, db_session: AsyncSession) -> PeerReviewTrigger:
        """Create a political keyword trigger for testing"""
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={
                "keywords": [
                    "election",
                    "vote",
                    "politician",
                    "government",
                    "parliament",
                ],
                "min_occurrences": 1,
                "case_sensitive": False,
            },
            description="Political keyword trigger for testing",
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)
        return trigger

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for submissions"""
        user = User(
            email="reviewer@test.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_triggers_on_political_keyword(
        self,
        db_session: AsyncSession,
        political_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is triggered when content contains political keywords"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="This is about the upcoming election and voting reforms.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is True
        assert TriggerType.POLITICAL_KEYWORD in result.triggered_by
        assert any("political" in r.lower() or "keyword" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_no_trigger_without_political_keywords(
        self,
        db_session: AsyncSession,
        political_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is NOT triggered for neutral content"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="The weather today is sunny and warm.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is False
        assert TriggerType.POLITICAL_KEYWORD not in result.triggered_by

    @pytest.mark.asyncio
    async def test_case_insensitive_keyword_matching(
        self,
        db_session: AsyncSession,
        political_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that keyword matching is case-insensitive by default"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="ELECTION results show GOVERNMENT change.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is True
        assert TriggerType.POLITICAL_KEYWORD in result.triggered_by

    @pytest.mark.asyncio
    async def test_disabled_trigger_is_ignored(
        self,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """Test that disabled triggers are not applied"""
        from app.services.peer_review_service import PeerReviewService

        # Create a disabled political trigger
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=False,  # Disabled
            threshold_value={"keywords": ["election"], "min_occurrences": 1},
            description="Disabled trigger",
        )
        db_session.add(trigger)
        await db_session.commit()

        submission = Submission(
            user_id=test_user.id,
            content="The election is coming up next month.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is False


class TestShouldTriggerReviewHealthSafety:
    """Tests for health/safety keyword detection"""

    @pytest.fixture
    async def health_trigger(self, db_session: AsyncSession) -> PeerReviewTrigger:
        """Create a health/safety keyword trigger for testing"""
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.SENSITIVE_TOPIC,
            enabled=True,
            threshold_value={
                "topics": [
                    "vaccine",
                    "vaccination",
                    "covid",
                    "health",
                    "medicine",
                    "treatment",
                    "cure",
                ],
                "severity_threshold": 0.7,
            },
            description="Health and safety topic trigger",
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)
        return trigger

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for submissions"""
        user = User(
            email="reviewer2@test.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_triggers_on_health_keywords(
        self,
        db_session: AsyncSession,
        health_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is triggered for health-related content"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="This vaccine cure claims to treat COVID instantly.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is True
        assert TriggerType.SENSITIVE_TOPIC in result.triggered_by

    @pytest.mark.asyncio
    async def test_no_trigger_without_health_keywords(
        self,
        db_session: AsyncSession,
        health_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is NOT triggered for non-health content"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="The football match ended in a 2-1 victory.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is False
        assert TriggerType.SENSITIVE_TOPIC not in result.triggered_by


class TestShouldTriggerReviewEngagement:
    """Tests for engagement threshold detection (>10k views)"""

    @pytest.fixture
    async def engagement_trigger(self, db_session: AsyncSession) -> PeerReviewTrigger:
        """Create an engagement threshold trigger for testing"""
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=True,
            threshold_value={
                "min_views": 10000,
                "min_shares": 500,
                "min_comments": 100,
            },
            description="Engagement threshold trigger",
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)
        return trigger

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for submissions"""
        user = User(
            email="reviewer3@test.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_triggers_on_high_view_count(
        self,
        db_session: AsyncSession,
        engagement_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is triggered when views exceed threshold"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="Regular content with no sensitive keywords.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        # Pass engagement metrics as optional parameter
        result = await service.should_trigger_review(
            submission,
            engagement_metrics={"views": 15000, "shares": 100, "comments": 50},
        )

        assert result.should_trigger is True
        assert TriggerType.ENGAGEMENT_THRESHOLD in result.triggered_by
        assert any("view" in r.lower() or "engagement" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_no_trigger_below_view_threshold(
        self,
        db_session: AsyncSession,
        engagement_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is NOT triggered when views are below threshold"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="Regular content with no sensitive keywords.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(
            submission,
            engagement_metrics={"views": 5000, "shares": 50, "comments": 10},
        )

        assert TriggerType.ENGAGEMENT_THRESHOLD not in result.triggered_by

    @pytest.mark.asyncio
    async def test_triggers_on_high_share_count(
        self,
        db_session: AsyncSession,
        engagement_trigger: PeerReviewTrigger,
        test_user: User,
    ) -> None:
        """Test that peer review is triggered when shares exceed threshold"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="Regular content with no sensitive keywords.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(
            submission,
            engagement_metrics={"views": 1000, "shares": 600, "comments": 50},
        )

        assert result.should_trigger is True
        assert TriggerType.ENGAGEMENT_THRESHOLD in result.triggered_by


class TestShouldTriggerReviewManual:
    """Tests for manual review initiation"""

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for submissions"""
        user = User(
            email="reviewer4@test.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_respects_manual_peer_review_flag(
        self,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """Test that peer review is triggered when manual flag is set"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="Normal content without any trigger keywords.",
            submission_type="text",
            status="pending",
            requires_peer_review=True,  # Manually flagged
            peer_review_reason="Flagged by editor for additional review",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(submission)

        assert result.should_trigger is True
        assert any("manual" in r.lower() or "flagged" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_flag_manual_review(
        self,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """Test ability to manually flag a submission for peer review"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="Normal content.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        updated = await service.flag_for_manual_review(
            submission,
            reason="Editor requested additional review",
        )

        assert updated.requires_peer_review is True
        assert updated.peer_review_reason == "Editor requested additional review"

        # Check that subsequent calls to should_trigger_review recognize this
        result = await service.should_trigger_review(updated)
        assert result.should_trigger is True


class TestShouldTriggerReviewMultipleTriggers:
    """Tests for combined trigger scenarios"""

    @pytest.fixture
    async def all_triggers(self, db_session: AsyncSession) -> list[PeerReviewTrigger]:
        """Create all types of triggers for testing"""
        triggers = [
            PeerReviewTrigger(
                trigger_type=TriggerType.POLITICAL_KEYWORD,
                enabled=True,
                threshold_value={
                    "keywords": ["election", "government"],
                    "min_occurrences": 1,
                },
            ),
            PeerReviewTrigger(
                trigger_type=TriggerType.SENSITIVE_TOPIC,
                enabled=True,
                threshold_value={
                    "topics": ["vaccine", "health"],
                    "severity_threshold": 0.7,
                },
            ),
            PeerReviewTrigger(
                trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
                enabled=True,
                threshold_value={
                    "min_views": 10000,
                    "min_shares": 500,
                    "min_comments": 100,
                },
            ),
        ]
        for trigger in triggers:
            db_session.add(trigger)
        await db_session.commit()
        return triggers

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for submissions"""
        user = User(
            email="reviewer5@test.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_multiple_triggers_activated(
        self,
        db_session: AsyncSession,
        all_triggers: list[PeerReviewTrigger],
        test_user: User,
    ) -> None:
        """Test that multiple triggers can be activated simultaneously"""
        from app.services.peer_review_service import PeerReviewService

        submission = Submission(
            user_id=test_user.id,
            content="The government announces new vaccine election.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = PeerReviewService(db_session)
        result = await service.should_trigger_review(
            submission,
            engagement_metrics={"views": 20000, "shares": 100, "comments": 50},
        )

        assert result.should_trigger is True
        # Should have all three triggers
        assert TriggerType.POLITICAL_KEYWORD in result.triggered_by
        assert TriggerType.SENSITIVE_TOPIC in result.triggered_by
        assert TriggerType.ENGAGEMENT_THRESHOLD in result.triggered_by
        assert len(result.reasons) >= 3

    @pytest.mark.asyncio
    async def test_confidence_increases_with_multiple_triggers(
        self,
        db_session: AsyncSession,
        all_triggers: list[PeerReviewTrigger],
        test_user: User,
    ) -> None:
        """Test that confidence increases when multiple triggers match"""
        from app.services.peer_review_service import PeerReviewService

        # Single trigger content
        submission1 = Submission(
            user_id=test_user.id,
            content="The election is coming soon.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission1)

        # Multiple trigger content
        submission2 = Submission(
            user_id=test_user.id,
            content="Government announces vaccine election policy.",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission2)
        await db_session.commit()

        service = PeerReviewService(db_session)
        result1 = await service.should_trigger_review(submission1)
        result2 = await service.should_trigger_review(submission2)

        # More triggers should result in higher confidence
        assert result2.confidence >= result1.confidence


class TestGetEnabledTriggers:
    """Tests for retrieving enabled triggers from database"""

    @pytest.mark.asyncio
    async def test_get_enabled_triggers_returns_only_enabled(
        self, db_session: AsyncSession
    ) -> None:
        """Test that only enabled triggers are returned"""
        from app.services.peer_review_service import PeerReviewService

        # Create enabled and disabled triggers
        enabled_trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["test"]},
        )
        disabled_trigger = PeerReviewTrigger(
            trigger_type=TriggerType.SENSITIVE_TOPIC,
            enabled=False,
            threshold_value={"topics": ["test"]},
        )
        db_session.add_all([enabled_trigger, disabled_trigger])
        await db_session.commit()

        service = PeerReviewService(db_session)
        triggers = await service.get_enabled_triggers()

        assert len(triggers) == 1
        assert triggers[0].trigger_type == TriggerType.POLITICAL_KEYWORD

    @pytest.mark.asyncio
    async def test_get_triggers_by_type(self, db_session: AsyncSession) -> None:
        """Test filtering triggers by type"""
        from app.services.peer_review_service import PeerReviewService

        # Create multiple triggers
        political = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
        )
        health = PeerReviewTrigger(
            trigger_type=TriggerType.SENSITIVE_TOPIC,
            enabled=True,
            threshold_value={"topics": ["vaccine"]},
        )
        db_session.add_all([political, health])
        await db_session.commit()

        service = PeerReviewService(db_session)
        triggers = await service.get_enabled_triggers(trigger_type=TriggerType.POLITICAL_KEYWORD)

        assert len(triggers) == 1
        assert triggers[0].trigger_type == TriggerType.POLITICAL_KEYWORD
