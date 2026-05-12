"""
Example: FastAPI webhook receiver for Koulis events.

This is the EXACT pattern reservation_service should implement.

Idempotency strategy:
- On hold.created → atomically decrement local inventory for the slot
- On hold.released → NO-OP (reservation.created arrives right after,
  the decrement was already applied at hold.created time)
- On hold.expired → atomically increment local inventory (rollback)
- On reservation.created → persist the reservation, link to local
  restaurant via the koulis_id mapping. Do NOT touch inventory
  (already decremented at hold.created).

This ensures the slot is "reserved" for the 5-minute hold window
from the partner's perspective, and never double-counted.
"""

from os import environ

from fastapi import FastAPI, HTTPException, Request

from koulis.webhooks import (
    HoldCreatedEvent,
    HoldExpiredEvent,
    HoldReleasedEvent,
    ReservationCreatedEvent,
    parse_event,
    verify_signature,
)


app = FastAPI()
WEBHOOK_SECRET = environ["KOULIS_WEBHOOK_SECRET"]


@app.post("/webhooks/koulis")
async def koulis_webhook(request: Request) -> dict[str, bool]:
    # 1. Validate signature on raw bytes (NOT re-serialized JSON)
    payload = await request.body()
    signature = request.headers.get("X-Koulis-Signature", "")
    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse into typed event
    event = parse_event(payload)

    # 3. Dispatch by event type (pattern matching on discriminated union)
    match event:
        case HoldCreatedEvent():
            await handle_hold_created(event.data)
        case HoldReleasedEvent():
            await handle_hold_released(event.data)
        case HoldExpiredEvent():
            await handle_hold_expired(event.data)
        case ReservationCreatedEvent():
            await handle_reservation_created(event.data)

    # Always 200 — Koulis treats 200 as "delivered, don't retry"
    return {"received": True}


# ─── Handlers — implement these against your local DB ─────────────────

async def handle_hold_created(data):
    """
    A slot is being temporarily held. Decrement local inventory now
    to make sure the partner side doesn't double-book.
    """
    # restaurant = lookup_by_koulis_id(data.restaurant_id)
    # decrement_local_inventory(restaurant.id, data.slot_at, data.party_size)
    pass


async def handle_hold_released(data):
    """
    A hold has been confirmed (precedes reservation.created by ms).
    NO-OP: inventory was already decremented at hold.created time.
    """
    pass


async def handle_hold_expired(data):
    """
    A hold expired without confirmation. Restore local inventory.
    """
    # restaurant = lookup_by_koulis_id(data.restaurant_id)
    # restore_local_inventory(restaurant.id, data.slot_at, data.party_size)
    pass


async def handle_reservation_created(data):
    """
    A reservation has been confirmed. Persist it locally and link
    to local restaurant via the koulis_id mapping.
    """
    # restaurant = lookup_by_koulis_id(data.restaurant_id)
    # save_reservation(
    #     restaurant_id=restaurant.id,
    #     koulis_confirmation_id=data.confirmation_id,
    #     slot_at=data.slot_at,
    #     customer_name=data.customer_name,
    #     ...
    # )
    pass