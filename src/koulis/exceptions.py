"""Typed exceptions for the Koulis SDK. Mirror HTTP status codes."""

from typing import Any


class KoulisAPIError(Exception):
    """Base exception. Catch this to handle all API errors uniformly."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class KoulisValidationError(KoulisAPIError):
    """Input validation failed (HTTP 400).

    Most often raised client-side when a datetime is naive (no tzinfo).
    Also raised when the API rejects an input field (URL invalide,
    party_size hors range, etc.).
    """


class KoulisAuthError(KoulisAPIError):
    """API token missing, invalid, or insufficiently scoped (HTTP 401/403)."""


class KoulisNotFound(KoulisAPIError):
    """Resource not found (HTTP 404).

    Common causes: unknown restaurant_id, hold_id, webhook_id, or
    a slot_at datetime with no matching availability.
    """


class KoulisConflict(KoulisAPIError):
    """Conflict (HTTP 409).

    Common causes:
    - Slot capacity insufficient for the requested party_size
    - Hold already consumed by another reservation
    - Webhook URL already registered
    """


class KoulisExpiredHold(KoulisAPIError):
    """Hold has expired (HTTP 410).

    Holds live 5 minutes after creation. Create a new hold by calling
    hold() again — the underlying slot may still be available.
    """


class KoulisNetworkError(KoulisAPIError):
    """Network transport error: timeout, DNS failure, connection refused.

    Wraps httpx.HTTPError. status_code is None because no HTTP response
    was received.
    """