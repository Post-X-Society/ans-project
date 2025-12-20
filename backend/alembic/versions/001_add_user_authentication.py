"""add_user_authentication

Revision ID: 001
Revises: 74a3438eeb0f
Create Date: 2025-12-15 12:57:44.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = "74a3438eeb0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add RBAC role enum and is_active field to existing users table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        # Create user_role enum
        op.execute("CREATE TYPE userrole AS ENUM ('super_admin', 'admin', 'reviewer', 'submitter')")

        # Change role column from String to Enum
        op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")

        # Add is_active column
        op.add_column(
            "users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true")
        )
    else:
        # For SQLite, role is already String, just add is_active
        op.add_column(
            "users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true")
        )


def downgrade() -> None:
    """Remove RBAC changes from users table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # Remove is_active column
    op.drop_column("users", "is_active")

    if dialect_name == "postgresql":
        # Change role column back from Enum to String
        op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)")

        # Drop enum type
        op.execute("DROP TYPE userrole")
