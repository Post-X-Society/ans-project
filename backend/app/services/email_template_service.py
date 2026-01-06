"""
Email template service for database-backed multilingual templates

Issue #95: Email Templates (Multilingual EN/NL)
ADR 0004: Multilingual Support
ADR 0005: EFCSN Compliance Architecture

Provides CRUD operations and rendering for database-stored email templates
"""

from typing import Any, Optional

from jinja2 import Template, TemplateSyntaxError, UndefinedError  # type: ignore[import-not-found]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_template import EmailTemplate, EmailTemplateType


class EmailTemplateService:
    """Service for managing and rendering email templates"""

    async def get_template(
        self,
        db: AsyncSession,
        template_key: str,
        include_inactive: bool = False,
    ) -> Optional[EmailTemplate]:
        """
        Get email template by key

        Args:
            db: Database session
            template_key: Unique template identifier
            include_inactive: Whether to include inactive templates

        Returns:
            EmailTemplate if found, None otherwise
        """
        stmt = select(EmailTemplate).where(EmailTemplate.template_key == template_key)

        if not include_inactive:
            stmt = stmt.where(EmailTemplate.is_active == True)  # noqa: E712

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        db: AsyncSession,
        include_inactive: bool = False,
        template_type: Optional[EmailTemplateType] = None,
    ) -> list[EmailTemplate]:
        """
        List all email templates

        Args:
            db: Database session
            include_inactive: Whether to include inactive templates
            template_type: Filter by template type

        Returns:
            List of EmailTemplate objects
        """
        stmt = select(EmailTemplate)

        if not include_inactive:
            stmt = stmt.where(EmailTemplate.is_active == True)  # noqa: E712

        if template_type:
            stmt = stmt.where(EmailTemplate.template_type == template_type)

        stmt = stmt.order_by(EmailTemplate.template_key)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_template(
        self,
        db: AsyncSession,
        template_key: str,
        template_type: EmailTemplateType,
        name: dict[str, str],
        description: dict[str, str],
        subject: dict[str, str],
        body_text: dict[str, str],
        body_html: dict[str, str],
        variables: dict[str, str],
        is_active: bool = True,
        last_modified_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> EmailTemplate:
        """
        Create a new email template

        Args:
            db: Database session
            template_key: Unique template identifier
            template_type: Template type from enum
            name: Multilingual template name
            description: Multilingual description
            subject: Multilingual subject line (supports Jinja2)
            body_text: Multilingual plain text body (supports Jinja2)
            body_html: Multilingual HTML body (supports Jinja2)
            variables: Available template variables
            is_active: Whether template is active
            last_modified_by: User who created the template
            notes: Internal notes

        Returns:
            Created EmailTemplate object

        Raises:
            ValueError: If template_key already exists
        """
        # Check if template already exists
        existing = await self.get_template(db, template_key, include_inactive=True)
        if existing:
            raise ValueError(f"Template with key '{template_key}' already exists")

        # Validate Jinja2 syntax
        self._validate_template_syntax(subject)
        self._validate_template_syntax(body_text)
        self._validate_template_syntax(body_html)

        template = EmailTemplate(
            template_key=template_key,
            template_type=template_type,
            name=name,
            description=description,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            variables=variables,
            is_active=is_active,
            version=1,
            last_modified_by=last_modified_by,
            notes=notes,
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        return template

    async def update_template(
        self,
        db: AsyncSession,
        template_key: str,
        name: Optional[dict[str, str]] = None,
        description: Optional[dict[str, str]] = None,
        subject: Optional[dict[str, str]] = None,
        body_text: Optional[dict[str, str]] = None,
        body_html: Optional[dict[str, str]] = None,
        variables: Optional[dict[str, str]] = None,
        is_active: Optional[bool] = None,
        last_modified_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> EmailTemplate:
        """
        Update an existing email template

        Args:
            db: Database session
            template_key: Template identifier to update
            name: Updated multilingual name
            description: Updated multilingual description
            subject: Updated multilingual subject
            body_text: Updated multilingual plain text body
            body_html: Updated multilingual HTML body
            variables: Updated available variables
            is_active: Updated active status
            last_modified_by: User making the update
            notes: Updated internal notes

        Returns:
            Updated EmailTemplate object

        Raises:
            ValueError: If template not found
        """
        template = await self.get_template(db, template_key, include_inactive=True)
        if not template:
            raise ValueError(f"Template with key '{template_key}' not found")

        # Validate Jinja2 syntax if updating templates
        self._validate_template_updates(subject, body_text, body_html)

        # Update fields using helper method
        self._apply_template_updates(
            template,
            name=name,
            description=description,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            variables=variables,
            is_active=is_active,
            last_modified_by=last_modified_by,
            notes=notes,
        )

        # Increment version
        template.version += 1

        await db.commit()
        await db.refresh(template)

        return template

    def _validate_template_updates(
        self,
        subject: Optional[dict[str, str]],
        body_text: Optional[dict[str, str]],
        body_html: Optional[dict[str, str]],
    ) -> None:
        """Validate Jinja2 syntax for template updates"""
        if subject:
            self._validate_template_syntax(subject)
        if body_text:
            self._validate_template_syntax(body_text)
        if body_html:
            self._validate_template_syntax(body_html)

    def _apply_template_updates(
        self,
        template: EmailTemplate,
        name: Optional[dict[str, str]],
        description: Optional[dict[str, str]],
        subject: Optional[dict[str, str]],
        body_text: Optional[dict[str, str]],
        body_html: Optional[dict[str, str]],
        variables: Optional[dict[str, str]],
        is_active: Optional[bool],
        last_modified_by: Optional[str],
        notes: Optional[str],
    ) -> None:
        """Apply updates to template fields"""
        updates = {
            "name": name,
            "description": description,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "variables": variables,
            "is_active": is_active,
            "last_modified_by": last_modified_by,
            "notes": notes,
        }

        for field, value in updates.items():
            if value is not None:
                setattr(template, field, value)

    async def deactivate_template(self, db: AsyncSession, template_key: str) -> EmailTemplate:
        """
        Deactivate an email template

        Args:
            db: Database session
            template_key: Template identifier to deactivate

        Returns:
            Deactivated EmailTemplate object

        Raises:
            ValueError: If template not found
        """
        return await self.update_template(db, template_key, is_active=False)

    async def render_template(
        self,
        db: AsyncSession,
        template_key: str,
        context: dict[str, Any],
        language: str = "en",
    ) -> tuple[str, str, str]:
        """
        Render email template with context variables

        Args:
            db: Database session
            template_key: Template identifier to render
            context: Template variables
            language: Language code (en, nl)

        Returns:
            Tuple of (subject, body_text, body_html)

        Raises:
            ValueError: If template not found or required variables missing
        """
        template = await self.get_template(db, template_key)
        if not template:
            raise ValueError(f"Active template with key '{template_key}' not found")

        # Validate language
        if language not in template.subject:
            raise ValueError(f"Language '{language}' not available for template '{template_key}'")

        # Validate required variables
        missing_vars = set(template.variables.keys()) - set(context.keys())
        if missing_vars:
            raise ValueError(
                f"Missing required variables for template '{template_key}': "
                f"{', '.join(missing_vars)}"
            )

        # Render templates
        try:
            subject_template = Template(template.subject[language])
            subject = subject_template.render(**context)

            text_template = Template(template.body_text[language])
            body_text = text_template.render(**context)

            html_template = Template(template.body_html[language])
            body_html = html_template.render(**context)

            return subject, body_text, body_html

        except UndefinedError as e:
            raise ValueError(f"Template rendering error: {e}") from e

    def _validate_template_syntax(self, template_dict: dict[str, str]) -> None:
        """
        Validate Jinja2 template syntax for all languages

        Args:
            template_dict: Dictionary of language code to template string

        Raises:
            ValueError: If template syntax is invalid
        """
        for lang, template_str in template_dict.items():
            try:
                Template(template_str)
            except TemplateSyntaxError as e:
                raise ValueError(f"Invalid template syntax for language '{lang}': {e}") from e
