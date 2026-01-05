"""
Tests for email template service with multilingual support

Following TDD approach: Tests written FIRST before implementation
Issue #95: Email Templates (Multilingual EN/NL)
"""

from typing import Any

import pytest

from app.models.email_template import EmailTemplate, EmailTemplateType
from app.services.email_template_service import EmailTemplateService


class TestEmailTemplateService:
    """Test suite for email template service"""

    @pytest.fixture
    def template_service(self) -> EmailTemplateService:
        """Provide email template service instance"""
        return EmailTemplateService()

    @pytest.mark.asyncio
    async def test_get_template_by_key(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test retrieving template by key"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="submission_received",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Submission Received", "nl": "Inzending Ontvangen"},
            description={
                "en": "Sent when submission is received",
                "nl": "Verzonden wanneer inzending is ontvangen",
            },
            subject={
                "en": "Submission Received - AnsCheckt",
                "nl": "Inzending Ontvangen - AnsCheckt",
            },
            body_text={
                "en": "Thank you for your submission {{submission_id}}",
                "nl": "Bedankt voor uw inzending {{submission_id}}",
            },
            body_html={
                "en": "<p>Thank you for your submission {{submission_id}}</p>",
                "nl": "<p>Bedankt voor uw inzending {{submission_id}}</p>",
            },
            variables={"submission_id": "string", "claim_text": "string"},
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        # Act
        result: EmailTemplate | None = await template_service.get_template(
            db_session, "submission_received"
        )

        # Assert
        assert result is not None
        assert result.template_key == "submission_received"
        assert result.subject["en"] == "Submission Received - AnsCheckt"
        assert result.subject["nl"] == "Inzending Ontvangen - AnsCheckt"

    @pytest.mark.asyncio
    async def test_render_template_english(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test rendering template in English"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="test_template",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Test", "nl": "Test"},
            description={"en": "Test", "nl": "Test"},
            subject={"en": "Hello {{name}}", "nl": "Hallo {{name}}"},
            body_text={
                "en": "Your ID is {{id}}",
                "nl": "Uw ID is {{id}}",
            },
            body_html={
                "en": "<p>Your ID is {{id}}</p>",
                "nl": "<p>Uw ID is {{id}}</p>",
            },
            variables={"name": "string", "id": "string"},
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        context: dict[str, Any] = {"name": "John", "id": "12345"}

        # Act
        subject, body_text, body_html = await template_service.render_template(
            db_session, "test_template", context, language="en"
        )

        # Assert
        assert subject == "Hello John"
        assert body_text == "Your ID is 12345"
        assert body_html == "<p>Your ID is 12345</p>"

    @pytest.mark.asyncio
    async def test_render_template_dutch(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test rendering template in Dutch"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="test_dutch",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Test", "nl": "Test"},
            description={"en": "Test", "nl": "Test"},
            subject={"en": "Status: {{status}}", "nl": "Status: {{status}}"},
            body_text={
                "en": "The status is {{status}}",
                "nl": "De status is {{status}}",
            },
            body_html={
                "en": "<p>The status is {{status}}</p>",
                "nl": "<p>De status is {{status}}</p>",
            },
            variables={"status": "string"},
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        context: dict[str, Any] = {"status": "APPROVED"}

        # Act
        subject, body_text, body_html = await template_service.render_template(
            db_session, "test_dutch", context, language="nl"
        )

        # Assert
        assert subject == "Status: APPROVED"
        assert body_text == "De status is APPROVED"
        assert body_html == "<p>De status is APPROVED</p>"

    @pytest.mark.asyncio
    async def test_list_all_templates(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test listing all active templates"""
        # Arrange - Create 3 templates
        for i in range(3):
            template: EmailTemplate = EmailTemplate(
                template_key=f"template_{i}",
                template_type=EmailTemplateType.SUBMISSION_RECEIVED,
                name={"en": f"Template {i}", "nl": f"Sjabloon {i}"},
                description={"en": "Test", "nl": "Test"},
                subject={"en": "Test", "nl": "Test"},
                body_text={"en": "Test", "nl": "Test"},
                body_html={"en": "Test", "nl": "Test"},
                variables={},
                is_active=True,
            )
            db_session.add(template)
        await db_session.commit()

        # Act
        templates: list[EmailTemplate] = await template_service.list_templates(db_session)

        # Assert
        assert len(templates) >= 3
        assert all(t.is_active for t in templates)

    @pytest.mark.asyncio
    async def test_create_template(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test creating a new template"""
        # Arrange
        template_data: dict[str, Any] = {
            "template_key": "new_template",
            "template_type": EmailTemplateType.REVIEWER_ASSIGNED,
            "name": {"en": "Reviewer Assigned", "nl": "Reviewer Toegewezen"},
            "description": {"en": "Test description", "nl": "Test beschrijving"},
            "subject": {"en": "Subject EN", "nl": "Onderwerp NL"},
            "body_text": {"en": "Body EN", "nl": "Tekst NL"},
            "body_html": {"en": "<p>Body EN</p>", "nl": "<p>Tekst NL</p>"},
            "variables": {"reviewer": "string"},
        }

        # Act
        template: EmailTemplate = await template_service.create_template(
            db_session, **template_data
        )

        # Assert
        assert template.id is not None
        assert template.template_key == "new_template"
        assert template.name["en"] == "Reviewer Assigned"
        assert template.is_active is True
        assert template.version == 1

    @pytest.mark.asyncio
    async def test_update_template_increments_version(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test updating template increments version number"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="version_test",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Version Test", "nl": "Versie Test"},
            description={"en": "Test", "nl": "Test"},
            subject={"en": "Original", "nl": "Origineel"},
            body_text={"en": "Original", "nl": "Origineel"},
            body_html={"en": "Original", "nl": "Origineel"},
            variables={},
            is_active=True,
            version=1,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        # Act
        updated: EmailTemplate = await template_service.update_template(
            db_session,
            "version_test",
            subject={"en": "Updated", "nl": "Bijgewerkt"},
            last_modified_by="admin@anscheckt.nl",
        )

        # Assert
        assert updated.version == 2
        assert updated.subject["en"] == "Updated"
        assert updated.last_modified_by == "admin@anscheckt.nl"

    @pytest.mark.asyncio
    async def test_deactivate_template(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test deactivating a template"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="deactivate_test",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Test", "nl": "Test"},
            description={"en": "Test", "nl": "Test"},
            subject={"en": "Test", "nl": "Test"},
            body_text={"en": "Test", "nl": "Test"},
            body_html={"en": "Test", "nl": "Test"},
            variables={},
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        # Act
        await template_service.deactivate_template(db_session, "deactivate_test")

        # Assert
        result: EmailTemplate | None = await template_service.get_template(
            db_session, "deactivate_test", include_inactive=True
        )
        assert result is not None
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_inactive_template_not_returned_by_default(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test that inactive templates are not returned by default"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="inactive_test",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Test", "nl": "Test"},
            description={"en": "Test", "nl": "Test"},
            subject={"en": "Test", "nl": "Test"},
            body_text={"en": "Test", "nl": "Test"},
            body_html={"en": "Test", "nl": "Test"},
            variables={},
            is_active=False,
        )
        db_session.add(template)
        await db_session.commit()

        # Act
        result: EmailTemplate | None = await template_service.get_template(
            db_session, "inactive_test"
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_render_template_with_missing_variable_raises_error(
        self, template_service: EmailTemplateService, db_session: Any
    ) -> None:
        """Test that rendering with missing required variable raises error"""
        # Arrange
        template: EmailTemplate = EmailTemplate(
            template_key="missing_var_test",
            template_type=EmailTemplateType.SUBMISSION_RECEIVED,
            name={"en": "Test", "nl": "Test"},
            description={"en": "Test", "nl": "Test"},
            subject={"en": "Hello {{required_var}}", "nl": "Hallo {{required_var}}"},
            body_text={"en": "Test", "nl": "Test"},
            body_html={"en": "Test", "nl": "Test"},
            variables={"required_var": "string"},
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="required_var"):
            await template_service.render_template(
                db_session, "missing_var_test", {}, language="en"
            )
