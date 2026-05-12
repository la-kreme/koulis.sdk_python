"""Typed Pydantic models for Koulis webhook events.

Uses a discriminated union on the `type` field so that parse_event()
returns the correctly-typed event class — enabling pattern matching
with match/case in receivers.
"""

import json
from datetime import datetime
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _BaseEventData(BaseModel):
    """Base for all event data payloads. Ignores unknown fields
    (forward-compatibility: adding fields server-side won't break clients)."""

    model_config = ConfigDict(extra="ignore")


class ReservationCreatedData(_BaseEventData):
    confirmation_id: UUID
    restaurant_id: UUID
    restaurant_name: str
    slot_at: datetime
    party_size: int
    customer_name: str
    customer_phone: str
    customer_email: str
    special_requests: str | None = None
    source: str
    created_at: datetime


class HoldCreatedData(_BaseEventData):
    hold_id: UUID
    restaurant_id: UUID
    restaurant_name: str
    slot_at: datetime
    party_size: int
    expires_at: datetime
    source: str


class HoldReleasedData(_BaseEventData):
    hold_id: UUID
    restaurant_id: UUID
    restaurant_name: str
    slot_at: datetime
    party_size: int
    reason: str
    source: str


class HoldExpiredData(_BaseEventData):
    hold_id: UUID
    restaurant_id: UUID
    restaurant_name: str
    slot_at: datetime
    party_size: int
    expired_at: datetime
    source: str


class _BaseEvent(BaseModel):
    """Common envelope fields for every webhook event."""

    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime


class ReservationCreatedEvent(_BaseEvent):
    type: Literal["reservation.created"]
    data: ReservationCreatedData


class HoldCreatedEvent(_BaseEvent):
    type: Literal["hold.created"]
    data: HoldCreatedData


class HoldReleasedEvent(_BaseEvent):
    type: Literal["hold.released"]
    data: HoldReleasedData


class HoldExpiredEvent(_BaseEvent):
    type: Literal["hold.expired"]
    data: HoldExpiredData


# Discriminated union: Pydantic picks the right concrete class based
# on the `type` field. This is what makes pattern matching work cleanly
# in receivers.
WebhookEvent = Annotated[
    Union[
        ReservationCreatedEvent,
        HoldCreatedEvent,
        HoldReleasedEvent,
        HoldExpiredEvent,
    ],
    Field(discriminator="type"),
]


_event_adapter: TypeAdapter[WebhookEvent] = TypeAdapter(WebhookEvent)


def parse_event(payload: bytes | str | dict) -> WebhookEvent:
    """
    Parse a webhook payload into a typed event.

    Accepts raw bytes (recommended — same bytes used for signature
    verification), JSON string, or already-parsed dict. Raises
    pydantic.ValidationError for malformed or unknown event types.

    Example with pattern matching:

        from koulis.webhooks import (
            parse_event,
            ReservationCreatedEvent,
            HoldCreatedEvent,
            HoldReleasedEvent,
            HoldExpiredEvent,
        )

        event = parse_event(payload)
        match event:
            case ReservationCreatedEvent():
                handle_reservation(event.data)
            case HoldCreatedEvent():
                # Decrement local inventory for this slot
                handle_hold_created(event.data)
            case HoldReleasedEvent():
                # No-op (reservation.created arrives right after)
                pass
            case HoldExpiredEvent():
                # Restore local inventory
                handle_hold_expired(event.data)
    """
    if isinstance(payload, bytes):
        data = json.loads(payload)
    elif isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload

    return _event_adapter.validate_python(data)