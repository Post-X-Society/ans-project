"""Add email_templates table for multilingual template storage

Issue #95: Email Templates (Multilingual EN/NL)
- Add email_templates table for database-backed templates
- Enables runtime template editing without deployment
- Supports multilingual content (EN, NL)

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-01-05 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email_templates table"""

    # Create EmailTemplateType enum with all 27 values
    email_template_type_enum = sa.Enum(
        "submission_received",
        "reviewer_assigned",
        "review_assigned",
        "review_completed",
        "workflow_update",
        "workflow_submitted",
        "workflow_queued",
        "workflow_assigned",
        "workflow_in_research",
        "workflow_draft_ready",
        "workflow_admin_review",
        "workflow_peer_review",
        "workflow_final_approval",
        "workflow_published",
        "workflow_rejected",
        "correction_request_received",
        "correction_approved",
        "correction_rejected",
        "correction_resolution",
        "peer_review_request",
        "peer_review_completed",
        "fact_check_published",
        "draft_reminder",
        "transparency_page_review_reminder",
        "system_notification",
        "weekly_digest",
        "password_reset",
        "welcome_email",
        "account_verification",
        name="emailtemplatetype",
    )

    # Create email_templates table
    op.create_table(
        "email_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("template_key", sa.String(length=100), nullable=False),
        sa.Column("template_type", email_template_type_enum, nullable=False),
        sa.Column("name", JSONB, nullable=False),
        sa.Column("description", JSONB, nullable=False),
        sa.Column("subject", JSONB, nullable=False),
        sa.Column("body_text", JSONB, nullable=False),
        sa.Column("body_html", JSONB, nullable=False),
        sa.Column("variables", JSONB, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_modified_by", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_key"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_email_templates_template_key"),
        "email_templates",
        ["template_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_templates_template_type"),
        "email_templates",
        ["template_type"],
        unique=False,
    )


def downgrade() -> None:
    """Remove email_templates table"""

    # Drop indexes
    op.drop_index(op.f("ix_email_templates_template_type"), table_name="email_templates")
    op.drop_index(op.f("ix_email_templates_template_key"), table_name="email_templates")

    # Drop table
    op.drop_table("email_templates")

    # Drop enum type
    sa.Enum(name="emailtemplatetype").drop(op.get_bind(), checkfirst=True)
