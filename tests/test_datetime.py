"""Tests for koulis._datetime.to_utc_iso."""

from datetime import datetime, timedelta, timezone

import pytest

from koulis._datetime import to_utc_iso
from koulis.exceptions import KoulisValidationError


def test_utc_datetime_passthrough():
    dt = datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc)
    assert to_utc_iso(dt) == "2026-05-12T20:00:00Z"


def test_positive_offset_converted_to_utc():
    paris_tz = timezone(timedelta(hours=2))
    dt = datetime(2026, 5, 12, 22, 0, tzinfo=paris_tz)
    assert to_utc_iso(dt) == "2026-05-12T20:00:00Z"


def test_negative_offset_converted_to_utc():
    nyc_tz = timezone(timedelta(hours=-5))
    dt = datetime(2026, 5, 12, 15, 0, tzinfo=nyc_tz)
    assert to_utc_iso(dt) == "2026-05-12T20:00:00Z"


def test_naive_datetime_raises():
    dt = datetime(2026, 5, 12, 20, 0)
    with pytest.raises(KoulisValidationError) as exc:
        to_utc_iso(dt)
    assert "timezone-aware" in str(exc.value)


def test_microseconds_truncated():
    dt = datetime(2026, 5, 12, 20, 0, 0, 999999, tzinfo=timezone.utc)
    assert to_utc_iso(dt) == "2026-05-12T20:00:00Z"


def test_midnight_utc():
    dt = datetime(2026, 5, 12, 0, 0, tzinfo=timezone.utc)
    assert to_utc_iso(dt) == "2026-05-12T00:00:00Z"


def test_end_of_day_utc():
    dt = datetime(2026, 5, 12, 23, 59, 59, tzinfo=timezone.utc)
    assert to_utc_iso(dt) == "2026-05-12T23:59:59Z"