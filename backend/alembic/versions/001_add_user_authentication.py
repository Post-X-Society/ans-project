"""add_user_authentication

Revision ID: 001
Revises:
Create Date: 2025-12-15 12:57:44.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add users table with authentication fields"""
    # Create user_role enum only for PostgreSQL
    # SQLite doesn't support custom types, so we'll use String
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("CREATE TYPE userrole AS ENUM ('super_admin', 'admin', 'reviewer', 'submitter')")
        role_type = sa.Enum("super_admin", "admin", "reviewer", "submitter", name="userrole")
        # PostgreSQL uses UUID type
        from sqlalchemy.dialects.postgresql import UUID

        id_type = UUID(as_uuid=True)
    else:
        # For SQLite, use String instead of enum
        role_type = sa.String(length=20)
        # SQLite doesn't have native UUID, use String
        id_type = sa.String(length=36)

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", id_type, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    """Remove users table and enum"""
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop enum type only for PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE userrole")
