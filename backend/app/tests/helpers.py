"""
Shared test helpers for the backend test suite.

These helpers address cross-database compatibility issues between
SQLite (used in tests) and PostgreSQL (production).
"""

from datetime import datetime


def normalize_dt(dt: datetime) -> datetime:
    """Normalize datetime by stripping timezone info for consistent comparisons.

    SQLite doesn't have native timezone support and inconsistently returns
    timezone-naive datetimes. PostgreSQL properly handles DateTime(timezone=True)
    and returns timezone-aware datetimes.

    Mixing naive and aware datetimes in comparisons causes TypeError.
    This helper ensures consistent comparison regardless of timezone presence
    by stripping timezone info from both sides.

    Args:
        dt: A datetime object (may be timezone-aware or timezone-naive)

    Returns:
        A timezone-naive datetime for consistent comparisons

    Example:
        # In tests comparing API response datetime with current time:
        last_reviewed = datetime.fromisoformat(data["last_reviewed"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        assert (normalize_dt(now) - normalize_dt(last_reviewed)).total_seconds() < 60
    """
    return dt.replace(tzinfo=None) if dt.tzinfo else dt
