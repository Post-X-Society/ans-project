"""
Seed script for populating development database with sample data
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.submission import Submission
from app.models.user import User
from app.models.volunteer import Volunteer


async def seed_data():
    """Seed the database with sample data"""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🌱 Seeding development data...")

        # Create users
        print("Creating users...")
        user1 = User(
            email="test@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWpQTpDEYaa",  # password
            role="user",
        )
        user2 = User(
            email="volunteer@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWpQTpDEYaa",
            role="volunteer",
        )
        admin = User(
            email="admin@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWpQTpDEYaa",
            role="admin",
        )
        session.add_all([user1, user2, admin])
        await session.flush()

        # Create volunteer profile
        print("Creating volunteer profile...")
        volunteer = Volunteer(
            user_id=user2.id,
            score=250.0,
            verified_count=15,
            accuracy_rate=0.93,
        )
        session.add(volunteer)

        # Create submissions
        print("Creating submissions...")
        submission1 = Submission(
            user_id=user1.id,
            content="I heard that drinking 8 glasses of water per day is necessary for health.",
            submission_type="text",
            status="completed",
        )
        submission2 = Submission(
            user_id=user1.id,
            content="Is it true that vaccines cause autism?",
            submission_type="text",
            status="processing",
        )
        submission3 = Submission(
            user_id=user1.id,
            content="Climate change is not real, right?",
            submission_type="text",
            status="pending",
        )
        session.add_all([submission1, submission2, submission3])

        # Create claims
        print("Creating claims...")
        claim1 = Claim(
            content="Drinking 8 glasses of water per day is necessary for optimal health",
            source="user_submission",
        )
        claim2 = Claim(
            content="Vaccines cause autism",
            source="user_submission",
        )
        claim3 = Claim(
            content="The Earth is flat",
            source="benedmo",
        )
        session.add_all([claim1, claim2, claim3])
        await session.flush()

        # Create fact checks
        print("Creating fact checks...")
        fact_check1 = FactCheck(
            claim_id=claim1.id,
            verdict="partially_true",
            confidence=0.75,
            reasoning="While hydration is important, the '8 glasses' rule is not scientifically proven. Water needs vary by person, activity level, and climate.",
            sources=[
                "https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/water/art-20044256",
                "https://www.health.harvard.edu/staying-healthy/how-much-water-should-you-drink",
            ],
        )
        fact_check2 = FactCheck(
            claim_id=claim2.id,
            verdict="false",
            confidence=0.99,
            reasoning="Numerous large-scale scientific studies have found no link between vaccines and autism. The original fraudulent study has been retracted.",
            sources=[
                "https://www.cdc.gov/vaccinesafety/concerns/autism.html",
                "https://www.who.int/news-room/fact-sheets/detail/autism-spectrum-disorders",
            ],
        )
        fact_check3 = FactCheck(
            claim_id=claim3.id,
            verdict="false",
            confidence=1.0,
            reasoning="The Earth is an oblate spheroid, as proven by countless observations, satellite imagery, and physical measurements over centuries.",
            sources=[
                "https://www.nasa.gov/topics/earth/features/earth-round.html",
                "https://www.scientificamerican.com/article/earth-is-not-flat/",
            ],
        )
        session.add_all([fact_check1, fact_check2, fact_check3])

        await session.commit()
        print("✅ Development data seeded successfully!")
        print("   - 3 users (user, volunteer, admin)")
        print("   - 1 volunteer profile")
        print("   - 3 submissions")
        print("   - 3 claims")
        print("   - 3 fact checks")


async def main():
    """Main entry point"""
    await seed_data()


if __name__ == "__main__":
    asyncio.run(main())
