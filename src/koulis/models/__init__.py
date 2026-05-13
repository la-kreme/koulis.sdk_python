"""Public models for the Koulis SDK. Re-exports from auto-generated module."""

from koulis.models._generated import (
    AvailabilitiesResponse,
    AvailabilitySlot,
    ConsumeSlotInput,
    CreateHoldInput,
    CreateReservationInput,
    CreateRestaurantInput,
    ErrorResponse,
    Event,
    HoldResponse,
    ListWebhookDeliveriesResponse,
    ListWebhooksResponse,
    LocalizedDateTime,
    RegisterWebhookInput,
    RegisterWebhookOutput,
    ReservationResponse,
    RestoreSlotInput,
    Restaurant,
    RestaurantWithSlots,
    SearchResponse,
    Status,
    UpsertAvailabilitiesInput,
    UpsertAvailabilitiesResponse,
    WebhookDelivery,
    WebhookEndpoint,
)

# Ergonomic aliases for public consumption.
# The OpenAPI uses "*Response" / "*Input" naming, but consumers expect
# domain-level names like Hold and Reservation.
Hold = HoldResponse
Reservation = ReservationResponse

__all__ = [
    # Core domain models
    "Restaurant",
    "RestaurantWithSlots",
    "AvailabilitySlot",
    "AvailabilitiesResponse",
    "Hold",
    "Reservation",
    "SearchResponse",
    # Localization
    "LocalizedDateTime",
    # Enums (give consumers autocomplete on valid values)
    "Event",
    "Status",
    # Webhooks
    "WebhookEndpoint",
    "WebhookDelivery",
    "ListWebhooksResponse",
    "ListWebhookDeliveriesResponse",
    "RegisterWebhookOutput",
    # Input types (rarely needed but available)
    "CreateRestaurantInput",
    "ConsumeSlotInput",
    "RestoreSlotInput",
    "CreateHoldInput",
    "CreateReservationInput",
    "RegisterWebhookInput",
    "UpsertAvailabilitiesInput",
    "UpsertAvailabilitiesResponse",
    "ErrorResponse",
]