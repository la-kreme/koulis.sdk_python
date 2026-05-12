"""
Datetime validation helper.

Mirrors koulis-api's strict UTC validation to fail fast client-side
instead of after a 400 round-trip. The Koulis API rejects datetimes
without explicit timezone offset (Z or ±HH:MM); we enforce the same
contract here.

The underscore prefix indicates this is a private module — consumers
should not import to_utc_iso directly. It's used internally by both
KoulisClient and AsyncKoulisClient before any datetime is sent over
the wire.
"""

from datetime import datetime, timezone

from koulis.exceptions import KoulisValidationError


def to_utc_iso(value: datetime) -> str:
    """
    Convert a timezone-aware datetime to ISO 8601 UTC with Z suffix.

    Naive datetimes (no tzinfo) are rejected with KoulisValidationError.

    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> to_utc_iso(datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc))
        '2026-05-12T20:00:00Z'

        >>> paris = timezone(timedelta(hours=2))
        >>> to_utc_iso(datetime(2026, 5, 12, 22, 0, tzinfo=paris))
        '2026-05-12T20:00:00Z'

        >>> to_utc_iso(datetime(2026, 5, 12, 20, 0))
        Traceback (most recent call last):
            ...
        koulis.exceptions.KoulisValidationError: datetime must be timezone-aware...
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise KoulisValidationError(
            "datetime must be timezone-aware. Use "
            "`datetime(..., tzinfo=timezone.utc)` or any other tz-aware datetime."
        )
    utc_dt = value.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")