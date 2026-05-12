"""Synchronous Koulis client. Use for scripts, CLI tools, batch jobs."""

from __future__ import annotations

from datetime import date, datetime
from types import TracebackType
from typing import Any
from uuid import UUID

import httpx

from koulis._datetime import to_utc_iso
from koulis._http import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    build_headers,
    parse_json,
    raise_for_status,
)
from koulis.exceptions import KoulisNetworkError
from koulis.models import (
    AvailabilitySlot,
    Hold,
    RegisterWebhookOutput,
    Reservation,
    Restaurant,
    UpsertAvailabilitiesResponse,
    WebhookDelivery,
    WebhookEndpoint,
)


class KoulisClient:
    """
    Synchronous client for the Koulis API.

    Use this for CLI tools, scripts, batch jobs, or any context where
    you don't need asyncio. For FastAPI / async workers, use
    AsyncKoulisClient instead — the public API is identical.

    Example:
        >>> from datetime import datetime, timezone
        >>> with KoulisClient(api_token="sk_...") as client:
        ...     results = client.search(
        ...         city="Paris",
        ...         when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        ...         party_size=2,
        ...     )
    """

    def __init__(
        self,
        api_token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_token:
            raise ValueError("api_token is required")
        self._base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            headers=build_headers(api_token),
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "KoulisClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    # ─── Restaurants & onboarding ───────────────────────────────────────

    def register_restaurant(
        self,
        *,
        name: str,
        country_code: str,
        slug: str | None = None,
        address: str | None = None,
        postal_code: str | None = None,
        city_name: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        phone: str | None = None,
        actor_type: str | None = None,
        price_range: int | None = None,
        excerpt: str | None = None,
        cuisines: list[str] | None = None,
        formats: list[str] | None = None,
        dietary: list[str] | None = None,
        atmosphere: list[str] | None = None,
        services: list[str] | None = None,
        is_published: bool = True,
        source: str = "sdk",
    ) -> Restaurant:
        """
        Register a new restaurant in the Koulis network.

        Used during partner onboarding (e.g. reservation_service when
        a restaurant activates "Bookable via Koulis"). Returns the full
        Restaurant object including its Koulis-assigned UUID, which
        the partner should persist locally to map koulis_id ↔ local_id.
        """
        payload: dict[str, Any] = {
            "name": name,
            "country_code": country_code,
            "is_published": is_published,
            "source": source,
        }
        optional = {
            "slug": slug,
            "address": address,
            "postal_code": postal_code,
            "city_name": city_name,
            "latitude": latitude,
            "longitude": longitude,
            "phone": phone,
            "actor_type": actor_type,
            "price_range": price_range,
            "excerpt": excerpt,
            "cuisines": cuisines,
            "formats": formats,
            "dietary": dietary,
            "atmosphere": atmosphere,
            "services": services,
        }
        for key, value in optional.items():
            if value is not None:
                payload[key] = value

        response = self._post("/v1/restaurants", json_body=payload)
        return Restaurant.model_validate(parse_json(response))

    def search(
        self,
        *,
        city: str,
        when: datetime,
        party_size: int,
        window_hours: int = 3,
        cuisine: str | None = None,
        dietary: str | None = None,
    ) -> list[Restaurant]:
        """
        Discover restaurants in a city with available slots around a datetime.

        Returns a list of restaurants matching the criteria. The window
        is ±window_hours around `when` (default ±3h).
        """
        params: dict[str, Any] = {
            "city": city,
            "datetime": to_utc_iso(when),
            "party_size": party_size,
            "window_hours": window_hours,
        }
        if cuisine:
            params["cuisine"] = cuisine
        if dietary:
            params["dietary"] = dietary

        response = self._get("/v1/restaurants/search", params=params)
        data = parse_json(response)
        return [Restaurant.model_validate(r) for r in data["results"]]

    # ─── Availabilities ─────────────────────────────────────────────────

    def push_availabilities(
        self,
        *,
        restaurant_id: UUID | str,
        date: date,
        slots: list[dict[str, Any]],
    ) -> UpsertAvailabilitiesResponse:
        """
        Replace all availabilities for a restaurant on a given date.

        Transactional: either all slots are written or none.

        Each slot in `slots` is a dict with:
        - 'slot_at' (tz-aware datetime — converted to UTC ISO internally)
        - 'capacity_total' (int)
        """
        normalized_slots = []
        for slot in slots:
            slot_at = slot["slot_at"]
            if isinstance(slot_at, datetime):
                slot_at_iso = to_utc_iso(slot_at)
            else:
                slot_at_iso = slot_at
            normalized_slots.append(
                {
                    "slot_at": slot_at_iso,
                    "capacity_total": slot["capacity_total"],
                }
            )

        payload = {
            "date": date.isoformat(),
            "slots": normalized_slots,
        }
        response = self._put(
            f"/v1/restaurants/{restaurant_id}/availabilities",
            json_body=payload,
        )
        return UpsertAvailabilitiesResponse.model_validate(parse_json(response))

    def discover_slots(
        self,
        *,
        restaurant_id: UUID | str,
        when: datetime,
        party_size: int,
        window_hours: int = 2,
    ) -> list[AvailabilitySlot]:
        """List available slots for one restaurant within ±window_hours."""
        params = {
            "datetime": to_utc_iso(when),
            "party_size": party_size,
            "window_hours": window_hours,
        }
        response = self._get(
            f"/v1/restaurants/{restaurant_id}/availabilities",
            params=params,
        )
        data = parse_json(response)
        return [AvailabilitySlot.model_validate(s) for s in data["slots"]]

    # ─── Slot mutations (external consumption) ──────────────────────────

    def consume_slot(
        self,
        *,
        restaurant_id: UUID | str,
        slot_at: datetime,
        party_size: int,
    ) -> AvailabilitySlot:
        """
        Atomically decrement slot capacity.

        Call this when an external booking (Reserve with Google, phone
        reservation, walk-in) consumes a slot, so that Koulis stays in
        sync with the partner's source-of-truth inventory.

        Raises KoulisConflict if capacity is insufficient.
        """
        payload = {
            "slot_at": to_utc_iso(slot_at),
            "party_size": party_size,
        }
        response = self._post(
            f"/v1/restaurants/{restaurant_id}/slots/consume",
            json_body=payload,
        )
        return AvailabilitySlot.model_validate(parse_json(response))

    def restore_slot(
        self,
        *,
        restaurant_id: UUID | str,
        slot_at: datetime,
        party_size: int,
    ) -> AvailabilitySlot:
        """
        Atomically increment slot capacity (capped at capacity_total).

        Call this when an external booking is cancelled.
        """
        payload = {
            "slot_at": to_utc_iso(slot_at),
            "party_size": party_size,
        }
        response = self._post(
            f"/v1/restaurants/{restaurant_id}/slots/restore",
            json_body=payload,
        )
        return AvailabilitySlot.model_validate(parse_json(response))

    # ─── Booking flow ───────────────────────────────────────────────────

    def hold(
        self,
        *,
        restaurant_id: UUID | str,
        slot_at: datetime,
        party_size: int,
    ) -> Hold:
        """
        Create a 5-minute hold on a slot. Step 1 of booking.

        The slot's capacity is temporarily decremented. The hold must be
        confirmed via confirm() within 5 minutes, or it expires and the
        capacity is restored automatically.
        """
        payload = {
            "restaurant_id": str(restaurant_id),
            "slot_at": to_utc_iso(slot_at),
            "party_size": party_size,
        }
        response = self._post("/v1/holds", json_body=payload)
        return Hold.model_validate(parse_json(response))

    def confirm(
        self,
        *,
        hold_id: UUID | str,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        special_requests: str | None = None,
    ) -> Reservation:
        """
        Confirm a hold and finalize the reservation. Step 2 of booking.

        Idempotent on hold_id: calling twice with the same hold_id
        returns the same reservation (idempotent_replay=True on replays).

        Raises KoulisExpiredHold if the hold is older than 5 minutes.
        Raises KoulisNotFound if the hold_id is unknown.
        """
        payload: dict[str, Any] = {
            "hold_id": str(hold_id),
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_email": customer_email,
        }
        if special_requests:
            payload["special_requests"] = special_requests

        response = self._post("/v1/reservations", json_body=payload)
        return Reservation.model_validate(parse_json(response))

    def book(
        self,
        *,
        restaurant_id: UUID | str,
        slot_at: datetime,
        party_size: int,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        special_requests: str | None = None,
    ) -> Reservation:
        """
        One-shot booking helper: creates a hold and immediately confirms it.

        Use this for automated workflows where the user has already
        confirmed (e.g. agent IA backend) and you don't need the 5-min
        confirmation window.

        For interactive flows (e.g. MCP), use hold() + confirm()
        separately to give the user time to review before commitment.
        """
        h = self.hold(
            restaurant_id=restaurant_id,
            slot_at=slot_at,
            party_size=party_size,
        )
        return self.confirm(
            hold_id=h.hold_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            special_requests=special_requests,
        )

    # ─── Webhooks ───────────────────────────────────────────────────────

    def register_webhook(
        self,
        *,
        url: str,
        events: list[str],
        description: str | None = None,
    ) -> RegisterWebhookOutput:
        """
        Register a webhook endpoint to receive Koulis events.

        Available events:
        - "reservation.created"
        - "hold.created"
        - "hold.released"
        - "hold.expired"

        The returned `secret` is shown ONLY on creation. Store it
        immediately; it cannot be retrieved later. Use it to verify
        incoming webhook signatures via koulis.webhooks.verify_signature.
        """
        payload: dict[str, Any] = {"url": url, "events": events}
        if description:
            payload["description"] = description

        response = self._post("/v1/webhooks", json_body=payload)
        return RegisterWebhookOutput.model_validate(parse_json(response))

    def list_webhooks(self) -> list[WebhookEndpoint]:
        """List all registered webhook endpoints. Secrets are not exposed."""
        response = self._get("/v1/webhooks", params={})
        data = parse_json(response)
        return [WebhookEndpoint.model_validate(w) for w in data["results"]]

    def delete_webhook(self, webhook_id: UUID | str) -> None:
        """Soft-delete a webhook endpoint (sets is_active=false)."""
        self._delete(f"/v1/webhooks/{webhook_id}")

    def list_webhook_deliveries(
        self,
        *,
        endpoint_id: UUID | str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        """List recent webhook delivery attempts. Useful for debugging."""
        params: dict[str, Any] = {"limit": limit}
        if endpoint_id is not None:
            params["endpoint_id"] = str(endpoint_id)
        if status:
            params["status"] = status

        response = self._get("/v1/webhook_deliveries", params=params)
        data = parse_json(response)
        return [WebhookDelivery.model_validate(d) for d in data["deliveries"]]

    def retry_webhook_delivery(self, delivery_id: UUID | str) -> WebhookDelivery:
        """Force an immediate retry of a webhook delivery."""
        response = self._post(
            f"/v1/webhook_deliveries/{delivery_id}/retry",
            json_body={},
        )
        return WebhookDelivery.model_validate(parse_json(response))

    # ─── HTTP internals ─────────────────────────────────────────────────

    def _get(self, path: str, *, params: dict[str, Any]) -> httpx.Response:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise KoulisNetworkError(f"Network error: {exc}") from exc
        raise_for_status(response)
        return response

    def _post(self, path: str, *, json_body: dict[str, Any]) -> httpx.Response:
        try:
            response = self._client.post(path, json=json_body)
        except httpx.HTTPError as exc:
            raise KoulisNetworkError(f"Network error: {exc}") from exc
        raise_for_status(response)
        return response

    def _put(self, path: str, *, json_body: dict[str, Any]) -> httpx.Response:
        try:
            response = self._client.put(path, json=json_body)
        except httpx.HTTPError as exc:
            raise KoulisNetworkError(f"Network error: {exc}") from exc
        raise_for_status(response)
        return response

    def _delete(self, path: str) -> httpx.Response:
        try:
            response = self._client.delete(path)
        except httpx.HTTPError as exc:
            raise KoulisNetworkError(f"Network error: {exc}") from exc
        raise_for_status(response)
        return response