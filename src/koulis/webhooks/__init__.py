"""Webhook handling for the Koulis SDK.

Two responsibilities:
- verify_signature: HMAC SHA-256 verification of incoming requests
- parse_event: typed Pydantic parsing with discriminated union

Receivers should always verify the signature BEFORE parsing the event.
"""

from koulis.webhooks.events import (
    HoldCreatedData,
    HoldCreatedEvent,
    HoldExpiredData,
    HoldExpiredEvent,
    HoldReleasedData,
    HoldReleasedEvent,
    ReservationCreatedData,
    ReservationCreatedEvent,
    WebhookEvent,
    parse_event,
)
from koulis.webhooks.signature import verify_signature

__all__ = [
    # Top-level event types (for pattern matching)
    "WebhookEvent",
    "ReservationCreatedEvent",
    "HoldCreatedEvent",
    "HoldReleasedEvent",
    "HoldExpiredEvent",
    # Event data payloads (for handler signatures)
    "ReservationCreatedData",
    "HoldCreatedData",
    "HoldReleasedData",
    "HoldExpiredData",
    # Functions
    "parse_event",
    "verify_signature",
]