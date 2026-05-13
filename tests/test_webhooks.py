"""Tests for koulis.webhooks (signature + event parsing)."""

import hmac
import json
from hashlib import sha256

import pytest
from pydantic import ValidationError

from koulis.webhooks import (
    HoldCreatedEvent,
    HoldExpiredEvent,
    HoldReleasedEvent,
    ReservationCreatedEvent,
    parse_event,
    verify_signature,
)


SECRET = "supersecret"


def _sign(payload: bytes, secret: str = SECRET) -> str:
    sig = hmac.new(secret.encode(), payload, sha256).hexdigest()
    return f"sha256={sig}"


# ─── signature ───────────────────────────────────────────────────────

def test_valid_signature_accepted():
    payload = b'{"hello":"world"}'
    assert verify_signature(payload, _sign(payload), SECRET) is True


def test_invalid_signature_rejected():
    assert verify_signature(b"x", "sha256=deadbeef", SECRET) is False


def test_missing_prefix_rejected():
    payload = b'{"x":1}'
    sig = _sign(payload).removeprefix("sha256=")
    assert verify_signature(payload, sig, SECRET) is False


def test_wrong_secret_rejected():
    payload = b'{"x":1}'
    sig = _sign(payload, "wrongsecret")
    assert verify_signature(payload, sig, SECRET) is False


def test_modified_payload_rejected():
    payload = b'{"x":1}'
    sig = _sign(payload)
    assert verify_signature(b'{"x":2}', sig, SECRET) is False


def test_empty_payload():
    assert verify_signature(b"", _sign(b""), SECRET) is True


# ─── event parsing ───────────────────────────────────────────────────

def _make_localized_slot(iso_utc: str = "2026-05-12T20:00:00.000Z") -> dict:
    """Helper to build a valid LocalizedDateTime dict for fixtures.

    The Koulis API enriches every slot with a timezone-aware
    representation so that consumers don't have to do conversions.
    All four webhook events now include this field as `slot_localized`.
    """
    return {
        "iso_utc": iso_utc,
        "local_date": "2026-05-12",
        "local_time": "22:00",
        "local_datetime": "2026-05-12T22:00:00+02:00",
        "timezone": "Europe/Paris",
        "human_readable_fr": "mardi 12 mai à 22h00",
        "human_readable_en": "Tuesday, May 12 at 10:00 PM",
    }


def _reservation_payload():
    return {
        "id": "evt_r1",
        "type": "reservation.created",
        "created_at": "2026-05-12T14:30:00Z",
        "data": {
            "confirmation_id": "11111111-1111-1111-1111-111111111111",
            "restaurant_id": "22222222-2222-2222-2222-222222222222",
            "restaurant_name": "Sanukiya",
            "slot_at": "2026-05-12T20:00:00Z",
            "slot_localized": _make_localized_slot(),
            "party_size": 2,
            "customer_name": "Test",
            "customer_phone": "+33600000000",
            "customer_email": "t@example.com",
            "special_requests": None,
            "source": "mcp",
            "created_at": "2026-05-12T14:30:00Z",
        },
    }


def _hold_created_payload():
    return {
        "id": "evt_h1",
        "type": "hold.created",
        "created_at": "2026-05-12T14:00:00Z",
        "data": {
            "hold_id": "33333333-3333-3333-3333-333333333333",
            "restaurant_id": "22222222-2222-2222-2222-222222222222",
            "restaurant_name": "Sanukiya",
            "slot_at": "2026-05-12T20:00:00Z",
            "slot_localized": _make_localized_slot(),
            "party_size": 2,
            "expires_at": "2026-05-12T14:05:00Z",
            "source": "mcp",
        },
    }


def test_parse_reservation_created():
    event = parse_event(_reservation_payload())
    assert isinstance(event, ReservationCreatedEvent)
    assert event.data.party_size == 2
    # Consumers should prefer slot_localized for display purposes.
    # slot_at is kept only for backward-compat with SDK v0.1.x.
    assert event.data.slot_localized.timezone == "Europe/Paris"
    assert event.data.slot_localized.human_readable_fr == "mardi 12 mai à 22h00"


def test_parse_hold_created():
    event = parse_event(_hold_created_payload())
    assert isinstance(event, HoldCreatedEvent)
    assert event.data.slot_localized.timezone == "Europe/Paris"


def test_parse_accepts_bytes():
    payload = json.dumps(_reservation_payload()).encode()
    event = parse_event(payload)
    assert isinstance(event, ReservationCreatedEvent)


def test_parse_accepts_string():
    payload = json.dumps(_reservation_payload())
    event = parse_event(payload)
    assert isinstance(event, ReservationCreatedEvent)


def test_unknown_event_type_rejected():
    bad = {
        "id": "evt_x",
        "type": "unknown.event",
        "created_at": "2026-05-12T14:00:00Z",
        "data": {},
    }
    with pytest.raises(ValidationError):
        parse_event(bad)


def test_pattern_matching_dispatches_correctly():
    event = parse_event(_hold_created_payload())
    result = ""
    match event:
        case ReservationCreatedEvent():
            result = "reservation"
        case HoldCreatedEvent():
            result = "hold_created"
        case HoldReleasedEvent():
            result = "hold_released"
        case HoldExpiredEvent():
            result = "hold_expired"
    assert result == "hold_created"