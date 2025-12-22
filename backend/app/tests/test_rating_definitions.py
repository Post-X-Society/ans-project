"""
Tests for RatingDefinition model - TDD approach: Write tests FIRST
"""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class TestRatingDefinitionModel:
    """Tests for RatingDefinition model"""

    @pytest.mark.asyncio
    async def test_create_rating_definition(self, db_session: AsyncSession) -> None:
        """Test creating a rating definition with all required fields"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="TRUE",
            title={"en": "True", "nl": "Waar"},
            description={
                "en": "The claim is accurate and supported by evidence.",
                "nl": "De claim is accuraat en wordt ondersteund door bewijs.",
            },
            visual_color="#00AA00",
            icon_name="check-circle",
            display_order=1,
        )

        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        assert rating.id is not None
        assert isinstance(rating.id, UUID)
        assert rating.rating_key == "TRUE"
        assert rating.title["en"] == "True"
        assert rating.title["nl"] == "Waar"
        assert rating.description["en"] == "The claim is accurate and supported by evidence."
        assert rating.visual_color == "#00AA00"
        assert rating.icon_name == "check-circle"
        assert rating.display_order == 1
        assert isinstance(rating.created_at, datetime)

    @pytest.mark.asyncio
    async def test_rating_key_unique(self, db_session: AsyncSession) -> None:
        """Test that rating_key must be unique"""
        from app.models.rating_definition import RatingDefinition

        rating1 = RatingDefinition(
            rating_key="FALSE",
            title={"en": "False", "nl": "Onwaar"},
            description={"en": "Description 1", "nl": "Beschrijving 1"},
        )
        db_session.add(rating1)
        await db_session.commit()

        rating2 = RatingDefinition(
            rating_key="FALSE",  # Duplicate key
            title={"en": "False 2", "nl": "Onwaar 2"},
            description={"en": "Description 2", "nl": "Beschrijving 2"},
        )
        db_session.add(rating2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_rating_key_not_null(self, db_session: AsyncSession) -> None:
        """Test that rating_key cannot be null"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key=None,
            title={"en": "Test"},
            description={"en": "Test"},
        )
        db_session.add(rating)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_title_not_null(self, db_session: AsyncSession) -> None:
        """Test that title cannot be null"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="TEST",
            title=None,
            description={"en": "Test"},
        )
        db_session.add(rating)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_description_not_null(self, db_session: AsyncSession) -> None:
        """Test that description cannot be null"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="TEST",
            title={"en": "Test"},
            description=None,
        )
        db_session.add(rating)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_optional_fields(self, db_session: AsyncSession) -> None:
        """Test that visual_color, icon_name, and display_order are optional"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="MINIMAL",
            title={"en": "Minimal"},
            description={"en": "Minimal description"},
            # visual_color, icon_name, display_order are not provided
        )

        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        assert rating.id is not None
        assert rating.visual_color is None
        assert rating.icon_name is None
        assert rating.display_order is None

    @pytest.mark.asyncio
    async def test_multilingual_content(self, db_session: AsyncSession) -> None:
        """Test that JSONB fields correctly store multilingual content"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="PARTLY_FALSE",
            title={
                "en": "Partly False",
                "nl": "Gedeeltelijk onwaar",
            },
            description={
                "en": "The claim contains some accurate information but also includes false or misleading elements.",
                "nl": "De claim bevat enige accurate informatie, maar ook onjuiste of misleidende elementen.",
            },
            visual_color="#FFA500",
            icon_name="alert-circle",
            display_order=2,
        )

        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        # Verify multilingual access
        assert rating.title["en"] == "Partly False"
        assert rating.title["nl"] == "Gedeeltelijk onwaar"
        assert "false or misleading" in rating.description["en"]
        assert "misleidende elementen" in rating.description["nl"]

    @pytest.mark.asyncio
    async def test_query_by_rating_key(self, db_session: AsyncSession) -> None:
        """Test querying rating by rating_key"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="SATIRE",
            title={"en": "Satire"},
            description={"en": "The content is satirical in nature."},
            display_order=6,
        )
        db_session.add(rating)
        await db_session.commit()

        # Query by rating_key
        result = await db_session.execute(
            select(RatingDefinition).where(RatingDefinition.rating_key == "SATIRE")
        )
        loaded_rating = result.scalar_one()

        assert loaded_rating.rating_key == "SATIRE"
        assert loaded_rating.display_order == 6

    @pytest.mark.asyncio
    async def test_order_by_display_order(self, db_session: AsyncSession) -> None:
        """Test ordering ratings by display_order"""
        from app.models.rating_definition import RatingDefinition

        ratings_data = [
            ("THIRD", 3),
            ("FIRST", 1),
            ("SECOND", 2),
        ]

        for key, order in ratings_data:
            rating = RatingDefinition(
                rating_key=key,
                title={"en": key.title()},
                description={"en": f"Description for {key}"},
                display_order=order,
            )
            db_session.add(rating)

        await db_session.commit()

        # Query ordered by display_order
        result = await db_session.execute(
            select(RatingDefinition).order_by(RatingDefinition.display_order)
        )
        ratings = result.scalars().all()

        assert len(ratings) == 3
        assert ratings[0].rating_key == "FIRST"
        assert ratings[1].rating_key == "SECOND"
        assert ratings[2].rating_key == "THIRD"

    @pytest.mark.asyncio
    async def test_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of RatingDefinition"""
        from app.models.rating_definition import RatingDefinition

        rating = RatingDefinition(
            rating_key="ALTERED",
            title={"en": "Altered"},
            description={"en": "The content has been digitally altered."},
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        repr_str = repr(rating)
        assert "RatingDefinition" in repr_str
        assert "ALTERED" in repr_str


class TestEFCSNRatings:
    """Tests for verifying all 6 EFCSN ratings can be created"""

    @pytest.mark.asyncio
    async def test_create_all_efcsn_ratings(self, db_session: AsyncSession) -> None:
        """Test creating all 6 EFCSN rating definitions"""
        from app.models.rating_definition import RatingDefinition

        efcsn_ratings = [
            {
                "rating_key": "TRUE",
                "title": {"en": "True", "nl": "Waar"},
                "description": {
                    "en": "The claim is accurate and supported by evidence.",
                    "nl": "De claim is accuraat en wordt ondersteund door bewijs.",
                },
                "visual_color": "#00AA00",
                "icon_name": "check-circle",
                "display_order": 1,
            },
            {
                "rating_key": "PARTLY_FALSE",
                "title": {"en": "Partly False", "nl": "Gedeeltelijk onwaar"},
                "description": {
                    "en": "The claim contains some accurate information but also includes false or misleading elements.",
                    "nl": "De claim bevat enige accurate informatie maar bevat ook onjuiste of misleidende elementen.",
                },
                "visual_color": "#FFA500",
                "icon_name": "alert-circle",
                "display_order": 2,
            },
            {
                "rating_key": "FALSE",
                "title": {"en": "False", "nl": "Onwaar"},
                "description": {
                    "en": "The claim is inaccurate and not supported by evidence.",
                    "nl": "De claim is onjuist en wordt niet ondersteund door bewijs.",
                },
                "visual_color": "#FF0000",
                "icon_name": "x-circle",
                "display_order": 3,
            },
            {
                "rating_key": "MISSING_CONTEXT",
                "title": {"en": "Missing Context", "nl": "Ontbrekende context"},
                "description": {
                    "en": "The claim lacks important context that would give a different impression.",
                    "nl": "De claim mist belangrijke context die een andere indruk zou geven.",
                },
                "visual_color": "#FFD700",
                "icon_name": "info-circle",
                "display_order": 4,
            },
            {
                "rating_key": "ALTERED",
                "title": {"en": "Altered", "nl": "Gemanipuleerd"},
                "description": {
                    "en": "The content has been digitally altered or manipulated.",
                    "nl": "De inhoud is digitaal gewijzigd of gemanipuleerd.",
                },
                "visual_color": "#800080",
                "icon_name": "edit-circle",
                "display_order": 5,
            },
            {
                "rating_key": "SATIRE",
                "title": {"en": "Satire", "nl": "Satire"},
                "description": {
                    "en": "The content is satirical in nature and not intended to be taken as fact.",
                    "nl": "De inhoud is satirisch van aard en is niet bedoeld om als feit te worden beschouwd.",
                },
                "visual_color": "#808080",
                "icon_name": "smile-circle",
                "display_order": 6,
            },
        ]

        for rating_data in efcsn_ratings:
            rating = RatingDefinition(**rating_data)
            db_session.add(rating)

        await db_session.commit()

        # Verify all 6 ratings were created
        result = await db_session.execute(
            select(RatingDefinition).order_by(RatingDefinition.display_order)
        )
        ratings = result.scalars().all()

        assert len(ratings) == 6
        assert ratings[0].rating_key == "TRUE"
        assert ratings[1].rating_key == "PARTLY_FALSE"
        assert ratings[2].rating_key == "FALSE"
        assert ratings[3].rating_key == "MISSING_CONTEXT"
        assert ratings[4].rating_key == "ALTERED"
        assert ratings[5].rating_key == "SATIRE"

        # Verify all have both EN and NL translations
        for rating in ratings:
            assert "en" in rating.title
            assert "nl" in rating.title
            assert "en" in rating.description
            assert "nl" in rating.description
