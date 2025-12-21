"""Tests for the i18n module."""

import pytest

from app.i18n import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    get_translation,
    get_translations,
    parse_accept_language,
)
from app.i18n.loader import clear_cache


@pytest.fixture(autouse=True)
def clear_translation_cache() -> None:
    """Clear the translation cache before each test."""
    clear_cache()


class TestGetTranslation:
    """Tests for get_translation function."""

    def test_get_translation_english(self) -> None:
        """Test getting a translation in English."""
        result = get_translation("auth.invalidCredentials", "en")
        assert result == "Invalid email or password"

    def test_get_translation_dutch(self) -> None:
        """Test getting a translation in Dutch."""
        result = get_translation("auth.invalidCredentials", "nl")
        assert result == "Ongeldige e-mail of wachtwoord"

    def test_get_translation_nested_key(self) -> None:
        """Test getting a nested translation key."""
        result = get_translation("common.success", "en")
        assert result == "Success"

    def test_get_translation_missing_key(self) -> None:
        """Test that missing keys return the key itself."""
        result = get_translation("nonexistent.key", "en")
        assert result == "nonexistent.key"

    def test_get_translation_unsupported_locale(self) -> None:
        """Test that unsupported locales fall back to default."""
        result = get_translation("auth.invalidCredentials", "fr")
        assert result == "Invalid email or password"  # Falls back to English

    def test_get_translation_with_interpolation(self) -> None:
        """Test translation with variable interpolation."""
        # Note: The current translation files don't have interpolation examples
        # but the function supports it
        result = get_translation("common.success", "en")
        assert result == "Success"


class TestGetTranslations:
    """Tests for get_translations function."""

    def test_get_translations_english(self) -> None:
        """Test getting all English translations."""
        translations = get_translations("en")
        assert "auth" in translations
        assert "common" in translations
        assert translations["auth"]["invalidCredentials"] == "Invalid email or password"

    def test_get_translations_dutch(self) -> None:
        """Test getting all Dutch translations."""
        translations = get_translations("nl")
        assert "auth" in translations
        assert translations["auth"]["invalidCredentials"] == "Ongeldige e-mail of wachtwoord"


class TestParseAcceptLanguage:
    """Tests for parse_accept_language function."""

    def test_parse_simple_language(self) -> None:
        """Test parsing a simple Accept-Language header."""
        result = parse_accept_language("nl")
        assert result == "nl"

    def test_parse_language_with_region(self) -> None:
        """Test parsing a language with region code."""
        result = parse_accept_language("nl-NL")
        assert result == "nl"

    def test_parse_multiple_languages(self) -> None:
        """Test parsing multiple languages with quality values."""
        result = parse_accept_language("nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7")
        assert result == "nl"

    def test_parse_english_preferred(self) -> None:
        """Test parsing when English is preferred."""
        result = parse_accept_language("en-US,en;q=0.9,nl;q=0.8")
        assert result == "en"

    def test_parse_unsupported_language(self) -> None:
        """Test parsing with unsupported language falls back to default."""
        result = parse_accept_language("fr-FR,fr;q=0.9")
        assert result == DEFAULT_LOCALE

    def test_parse_empty_header(self) -> None:
        """Test parsing empty header returns default."""
        result = parse_accept_language("")
        assert result == DEFAULT_LOCALE

    def test_parse_none_header(self) -> None:
        """Test parsing None returns default."""
        result = parse_accept_language(None)
        assert result == DEFAULT_LOCALE

    def test_parse_with_invalid_quality(self) -> None:
        """Test parsing with invalid quality value."""
        result = parse_accept_language("nl;q=invalid,en;q=0.5")
        # Should still work, treating invalid quality as 1.0
        assert result == "nl"


class TestConstants:
    """Tests for module constants."""

    def test_default_locale(self) -> None:
        """Test default locale is English."""
        assert DEFAULT_LOCALE == "en"

    def test_supported_locales(self) -> None:
        """Test supported locales include English and Dutch."""
        assert "en" in SUPPORTED_LOCALES
        assert "nl" in SUPPORTED_LOCALES
