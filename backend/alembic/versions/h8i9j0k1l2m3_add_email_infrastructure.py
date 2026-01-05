"""Add email infrastructure - EmailLog table and User.email_opt_out

Issue #94: Email Service Infrastructure (Celery + SMTP)
- Add EmailLog table for delivery tracking
- Add User.email_opt_out field for opt-out mechanism

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-01-05 15:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add EmailLog table and User.email_opt_out field"""

    # Create EmailLog table
    op.create_table(
        "email_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("template", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "SENT",
                "FAILED",
                "BOUNCED",
                "DELIVERED",
                name="emailstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
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
    )

    # Create indexes
    op.create_index(op.f("ix_email_logs_to_email"), "email_logs", ["to_email"], unique=False)
    op.create_index(op.f("ix_email_logs_template"), "email_logs", ["template"], unique=False)
    op.create_index(op.f("ix_email_logs_status"), "email_logs", ["status"], unique=False)
    op.create_index(
        op.f("ix_email_logs_celery_task_id"),
        "email_logs",
        ["celery_task_id"],
        unique=False,
    )

    # Add email_opt_out column to users table
    op.add_column(
        "users",
        sa.Column("email_opt_out", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index(op.f("ix_users_email_opt_out"), "users", ["email_opt_out"], unique=False)


def downgrade() -> None:
    """Remove EmailLog table and User.email_opt_out field"""

    # Remove email_opt_out from users table
    op.drop_index(op.f("ix_users_email_opt_out"), table_name="users")
    op.drop_column("users", "email_opt_out")

    # Drop indexes from email_logs
    op.drop_index(op.f("ix_email_logs_celery_task_id"), table_name="email_logs")
    op.drop_index(op.f("ix_email_logs_status"), table_name="email_logs")
    op.drop_index(op.f("ix_email_logs_template"), table_name="email_logs")
    op.drop_index(op.f("ix_email_logs_to_email"), table_name="email_logs")

    # Drop email_logs table
    op.drop_table("email_logs")

    # Drop EmailStatus enum type
    sa.Enum(name="emailstatus").drop(op.get_bind(), checkfirst=True)
