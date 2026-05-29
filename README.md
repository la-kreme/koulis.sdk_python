# koulis

Python SDK for the **Koulis** restaurant reservation infrastructure.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Installation

```bash
uv add git+ssh://git@github.com/koulis-app/koulis.sdk_python.git
```

## Quick start

### Synchronous (scripts, CLI, batch jobs)

```python
from datetime import datetime, timezone
from koulis import KoulisClient

with KoulisClient(api_token="sk_...") as client:
    results = client.search(
        city="Paris",
        when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
```

### Asynchronous (FastAPI, async services)

```python
from datetime import datetime, timezone
from koulis import AsyncKoulisClient

async with AsyncKoulisClient(api_token="sk_...") as client:
    results = await client.search(
        city="Paris",
        when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
```

Both clients expose strictly identical APIs — pick the one matching
your runtime context.

## Authentication

Pass an API token via the `api_token` argument. Tokens use Bearer
authentication. Contact Koulis support for a token.

## API surface

| Method | Purpose |
|---|---|
| `register_restaurant()` | Register a new restaurant in the Koulis network |
| `search()` | Discover restaurants with available slots in a city |
| `push_availabilities()` | Replace availabilities for a restaurant on a given date |
| `discover_slots()` | List slots for one restaurant |
| `consume_slot()` | Decrement slot capacity (external booking) |
| `restore_slot()` | Restore slot capacity (external cancellation) |
| `hold()` | Create a 5-minute hold on a slot |
| `confirm()` | Convert a hold into a confirmed reservation |
| `book()` | One-shot: hold + confirm in one call |
| `register_webhook()` | Register a webhook endpoint |
| `list_webhooks()` | List registered endpoints |
| `delete_webhook()` | Soft-delete an endpoint |
| `list_webhook_deliveries()` | Debug recent webhook deliveries |
| `retry_webhook_delivery()` | Force retry of a failed delivery |

## Datetime handling

All datetimes passed to the SDK MUST be timezone-aware. Naive
datetimes are rejected client-side with `KoulisValidationError`
before any HTTP round-trip:

```python
from datetime import datetime, timezone

# ✅ OK
when = datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc)

# ❌ raises KoulisValidationError
when = datetime(2026, 5, 12, 20, 0)
```

## Error handling

| Exception | Meaning |
|---|---|
| `KoulisValidationError` | Bad input (400) — naive datetime, invalid URL, etc. |
| `KoulisAuthError` | Missing or invalid API token (401, 403) |
| `KoulisNotFound` | Resource doesn't exist (404) |
| `KoulisConflict` | Slot capacity insufficient, hold consumed (409) |
| `KoulisExpiredHold` | Hold older than 5 minutes (410) |
| `KoulisNetworkError` | Connection failure, timeout |
| `KoulisAPIError` | Base — catch this for any API error |

```python
from koulis import KoulisClient, KoulisConflict, KoulisExpiredHold

try:
    reservation = client.book(...)
except KoulisConflict:
    # Slot was just taken
    ...
except KoulisExpiredHold:
    # Hold ran out before confirm
    ...
```

## Webhooks

Koulis delivers four event types via HTTP POST:

| Event | When |
|---|---|
| `hold.created` | A slot has been temporarily reserved (5-min window) |
| `hold.released` | A hold has been confirmed (precedes `reservation.created`) |
| `hold.expired` | A hold ran out without confirmation |
| `reservation.created` | A reservation is finalized |

Receiver (FastAPI):

```python
from fastapi import FastAPI, Request, HTTPException
from koulis.webhooks import (
    parse_event,
    verify_signature,
    HoldCreatedEvent,
    ReservationCreatedEvent,
)

app = FastAPI()

@app.post("/webhooks/koulis")
async def koulis_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("X-Koulis-Signature", "")
    if not verify_signature(payload, sig, WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid signature")

    event = parse_event(payload)
    match event:
        case HoldCreatedEvent():
            await handle_hold_created(event.data)
        case ReservationCreatedEvent():
            await handle_reservation_created(event.data)

    return {"received": True}
```

Always pass the **raw request bytes** to `verify_signature` — not
a re-serialized JSON dict. Whitespace differences will mismatch
the signature.

## Examples

See [`examples/`](./examples) for full working code:

- `booking_sync.py` — end-to-end booking flow (sync, no extra deps)
- `booking_async_fastapi.py` — FastAPI integration (`pip install fastapi uvicorn`)
- `onboarding_partner.py` — restaurant onboarding (no extra deps)
- `webhook_receiver_fastapi.py` — webhook receiver pattern (`pip install fastapi uvicorn`)

## Workspace

This repository is part of the Koulis workspace. See [`ARCHITECTURE.md`](../ARCHITECTURE.md) at the workspace root for a complete map of all repos and their interactions.

### Position in the ecosystem

```
reservation_service (PMS backend)
    │
    │ import koulis
    │
    ▼
koulis.sdk_python (this repo) ──HTTPS──▶ koulis.api (../koulis.api)
                                               │
                                               │ webhooks
                                               ▼
                                         reservation_service
```

- **Consumes**: [`koulis.api`](../koulis.api) — the core Koulis API at `api.koulis.ai`
- **Used by**: [`reservation_service`](../reservation_service) — PMS backend for restaurant onboarding, availability sync, and webhook reception
- **Related**: [`koulis`](../koulis) — MCP server that also consumes `koulis.api` (but via the MCP protocol, not this SDK)

### Key integrations

The SDK is the bridge between PMS partners and the Koulis protocol. In the `reservation_service`:

- **Onboarding**: `register_restaurant()` registers a restaurant in the Koulis network
- **Sync**: `push_availabilities()` pushes real-time table availability from the PMS to Koulis (hourly cron + event-driven)
- **Webhooks**: `verify_signature()` and `parse_event()` validate and dispatch incoming webhooks from `koulis.api`

## Development

```bash
git clone git@github.com:koulis-app/koulis.sdk_python.git
cd koulis.sdk_python
uv sync
uv run pytest
```

Regenerate models from the live OpenAPI spec when the API changes:

```bash
./scripts/regenerate_models.sh
```

## License

MIT — see [LICENSE](./LICENSE).