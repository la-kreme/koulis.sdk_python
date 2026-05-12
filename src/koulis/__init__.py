"""
Koulis Python SDK — restaurant reservation infrastructure for AI agents.

Quick start (sync, e.g. CLI tools, scripts):

    from datetime import datetime, timezone
    from koulis import KoulisClient

    with KoulisClient(api_token="sk_...") as client:
        results = client.search(
            city="Paris",
            when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
            party_size=2,
        )

Quick start (async, e.g. inside FastAPI):

    from datetime import datetime, timezone
    from koulis import AsyncKoulisClient

    async with AsyncKoulisClient(api_token="sk_...") as client:
        results = await client.search(
            city="Paris",
            when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
            party_size=2,
        )
"""

from koulis.async_client import AsyncKoulisClient
from koulis.client import KoulisClient
from koulis.exceptions import (
    KoulisAPIError,
    KoulisAuthError,
    KoulisConflict,
    KoulisExpiredHold,
    KoulisNetworkError,
    KoulisNotFound,
    KoulisValidationError,
)
from koulis.models import (
    AvailabilitiesResponse,
    AvailabilitySlot,
    Event,
    Hold,
    Reservation,
    Restaurant,
    RestaurantWithSlots,
    SearchResponse,
    Status,
    WebhookDelivery,
    WebhookEndpoint,
)

__version__ = "0.1.0"

__all__ = [
    # Clients
    "KoulisClient",
    "AsyncKoulisClient",
    # Core models
    "Restaurant",
    "RestaurantWithSlots",
    "AvailabilitySlot",
    "AvailabilitiesResponse",
    "Hold",
    "Reservation",
    "SearchResponse",
    # Enums
    "Event",
    "Status",
    # Webhook models
    "WebhookEndpoint",
    "WebhookDelivery",
    # Exceptions
    "KoulisAPIError",
    "KoulisAuthError",
    "KoulisNotFound",
    "KoulisConflict",
    "KoulisExpiredHold",
    "KoulisValidationError",
    "KoulisNetworkError",
]