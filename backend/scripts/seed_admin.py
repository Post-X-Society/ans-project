"""
Seed script for creating initial super admin user
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole


async def create_super_admin():
    """Create initial super admin if not exists"""
    # Default credentials (should be changed in production)
    email = "admin@ans.com"
    password = "Admin123!"

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Creating super admin user...")

        # Check if super admin already exists
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Super admin already exists: {email}")
            print(f"Role: {existing.role.value}")
            print(f"Active: {existing.is_active}")
            return

        # Create super admin
        admin = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()

        print("=" * 60)
        print("Super admin created successfully!")
        print("=" * 60)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Role: {admin.role.value}")
        print("=" * 60)
        print("WARNING: Please change the password immediately!")
        print("=" * 60)


async def main():
    """Main entry point"""
    try:
        await create_super_admin()
    except Exception as e:
        print(f"Error creating super admin: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
