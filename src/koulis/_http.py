"""
Shared HTTP layer for sync and async clients.

Pure helpers (no actual HTTP calls): they build request headers, map
HTTP error responses to typed Koulis exceptions, and parse JSON
responses defensively.

Both KoulisClient and AsyncKoulisClient consume these helpers, which
keeps the sync/async client implementations as thin and symmetric as
possible.
"""

from typing import Any

import httpx

from koulis.exceptions import (
    KoulisAPIError,
    KoulisAuthError,
    KoulisConflict,
    KoulisExpiredHold,
    KoulisNetworkError,
    KoulisNotFound,
    KoulisValidationError,
)


DEFAULT_BASE_URL = "https://api.koulis.ai"
DEFAULT_TIMEOUT = 30.0
USER_AGENT = "koulis-python/0.1.0"


def build_headers(api_token: str) -> dict[str, str]:
    """Build the default headers for any Koulis API request."""
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


def map_response_to_exception(response: httpx.Response) -> KoulisAPIError:
    """
    Translate an HTTP error response into the appropriate KoulisAPIError.

    Inspects the response body for a 'message' or 'error' field; falls
    back to "HTTP <status>" if neither is present or the body is not
    parseable JSON.
    """
    try:
        body: Any = response.json()
        message = (
            body.get("message")
            or body.get("error")
            or f"HTTP {response.status_code}"
        )
    except Exception:
        body = response.text
        message = f"HTTP {response.status_code}: {response.text[:200]}"

    status = response.status_code
    kwargs: dict[str, Any] = {"status_code": status, "body": body}

    if status == 400:
        return KoulisValidationError(message, **kwargs)
    if status in (401, 403):
        return KoulisAuthError(message, **kwargs)
    if status == 404:
        return KoulisNotFound(message, **kwargs)
    if status == 409:
        return KoulisConflict(message, **kwargs)
    if status == 410:
        return KoulisExpiredHold(message, **kwargs)
    return KoulisAPIError(message, **kwargs)


def raise_for_status(response: httpx.Response) -> None:
    """Raise the appropriate KoulisAPIError if the response is not 2xx."""
    if response.is_success:
        return
    raise map_response_to_exception(response)


def parse_json(response: httpx.Response) -> dict[str, Any]:
    """
    Parse a successful response body as JSON.

    Raises KoulisNetworkError if the body is malformed (this is rare
    in practice — successful responses are always valid JSON from the
    Koulis API — but we defend against transport-level corruption).
    """
    try:
        return response.json()
    except Exception as exc:
        raise KoulisNetworkError(f"Failed to parse JSON response: {exc}") from exc