"""
Internationalization (i18n) module for the Ans backend.

Provides translation support via JSON-based language files.
"""

from app.i18n.loader import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    get_translation,
    get_translations,
    parse_accept_language,
)

__all__ = [
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
    "get_translation",
    "get_translations",
    "parse_accept_language",
]
