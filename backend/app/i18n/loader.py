"""
Translation loader for the Ans backend.

Provides functions to load and retrieve translations from JSON files.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# Configuration
LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = frozenset({"en", "nl"})


@lru_cache(maxsize=10)
def load_translations(locale: str) -> dict[str, Any]:
    """
    Load translations for a locale with caching.

    Args:
        locale: The locale code (e.g., 'en', 'nl')

    Returns:
        Dictionary containing all translations for the locale
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    file_path = LOCALES_DIR / f"{locale}.json"

    if not file_path.exists():
        # Fall back to default locale if file doesn't exist
        file_path = LOCALES_DIR / f"{DEFAULT_LOCALE}.json"

    with open(file_path, encoding="utf-8") as f:
        result: dict[str, Any] = json.load(f)
        return result


def get_translations(locale: str = DEFAULT_LOCALE) -> dict[str, Any]:
    """
    Get all translations for a locale.

    Args:
        locale: The locale code (e.g., 'en', 'nl')

    Returns:
        Dictionary containing all translations
    """
    return load_translations(locale)


def get_translation(key: str, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    """
    Get a translation by dot-notation key with optional interpolation.

    Args:
        key: The translation key in dot notation (e.g., 'errors.notFound')
        locale: The locale code (e.g., 'en', 'nl')
        **kwargs: Variables to interpolate into the translation

    Returns:
        The translated string, or the key if not found

    Example:
        >>> get_translation('errors.notFound', 'en')
        'The requested resource was not found'
        >>> get_translation('common.welcome', 'en', name='John')
        'Welcome, John!'
    """
    translations = load_translations(locale)

    # Navigate nested keys: "errors.notFound" -> translations["errors"]["notFound"]
    value: Any = translations
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
            if value is None:
                return key  # Key not found
        else:
            return key  # Key not found

    if not isinstance(value, str):
        return key  # Value is not a string

    # Interpolate variables: "Hello {name}" with name="World" -> "Hello World"
    if kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            # If interpolation fails, return the raw string
            return value

    return value


def parse_accept_language(accept_language: str | None) -> str:
    """
    Parse the Accept-Language header and return the best matching locale.

    Args:
        accept_language: The Accept-Language header value

    Returns:
        The best matching supported locale, or DEFAULT_LOCALE

    Example:
        >>> parse_accept_language('nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7')
        'nl'
        >>> parse_accept_language('fr-FR,fr;q=0.9')
        'en'  # Falls back to default
    """
    if not accept_language:
        return DEFAULT_LOCALE

    # Parse and sort by quality value
    languages: list[tuple[str, float]] = []
    for part in accept_language.split(","):
        part = part.strip()
        if not part:
            continue

        if ";q=" in part:
            lang, q = part.split(";q=")
            try:
                quality = float(q)
            except ValueError:
                quality = 1.0
        else:
            lang = part
            quality = 1.0

        # Extract the language code (e.g., 'en-US' -> 'en')
        lang_code = lang.split("-")[0].lower()
        languages.append((lang_code, quality))

    # Sort by quality (descending)
    languages.sort(key=lambda x: x[1], reverse=True)

    # Find the first supported language
    for lang_code, _ in languages:
        if lang_code in SUPPORTED_LOCALES:
            return lang_code

    return DEFAULT_LOCALE


def clear_cache() -> None:
    """Clear the translation cache. Useful for testing or hot-reloading."""
    load_translations.cache_clear()
