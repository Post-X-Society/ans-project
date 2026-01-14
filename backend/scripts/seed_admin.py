"""
Seed script for creating initial test users (super admin, admin, reviewer, submitter)
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole

# Test user credentials
TEST_USERS = [
    {
        "email": "admin@ans.com",
        "password": "Admin123!",
        "role": UserRole.SUPER_ADMIN,
        "description": "Super Admin - Full system access",
    },
    {
        "email": "manager@ans.com",
        "password": "Manager123!",
        "role": UserRole.ADMIN,
        "description": "Admin - User management and approval",
    },
    {
        "email": "reviewer@ans.com",
        "password": "Reviewer123!",
        "role": UserRole.REVIEWER,
        "description": "Reviewer - Fact-check submissions",
    },
    {
        "email": "submitter@ans.com",
        "password": "Submitter123!",
        "role": UserRole.SUBMITTER,
        "description": "Submitter - Submit content for review",
    },
]


async def create_test_users():
    """Create initial test users if they don't exist"""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n" + "=" * 70)
        print("CREATING TEST USERS FOR ANS PLATFORM")
        print("=" * 70 + "\n")

        created_users = []
        existing_users = []

        for user_data in TEST_USERS:
            email = user_data["email"]

            # Check if user already exists
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing_users.append(
                    {"email": email, "role": existing.role.value, "active": existing.is_active}
                )
                continue

            # Create user
            user = User(
                email=email,
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
            )
            session.add(user)
            created_users.append(user_data)

        if created_users:
            await session.commit()
            print("✓ Successfully created the following test users:\n")
            for user_data in created_users:
                print(f"  • {user_data['description']}")
                print(f"    Email:    {user_data['email']}")
                print(f"    Password: {user_data['password']}")
                print(f"    Role:     {user_data['role'].value}")
                print()

        if existing_users:
            print("ℹ The following users already exist:\n")
            for user in existing_users:
                print(f"  • {user['email']} ({user['role']}) - Active: {user['active']}")
            print()

        if not created_users and not existing_users:
            print("⚠ No users were created or found.\n")

        print("=" * 70)
        print("IMPORTANT: Change these passwords in production!")
        print("=" * 70 + "\n")


async def main():
    """Main entry point"""
    try:
        await create_test_users()
    except Exception as e:
        print(f"\n❌ Error creating test users: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
