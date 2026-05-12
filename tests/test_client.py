"""Tests for KoulisClient (sync) using respx HTTP mocking."""

from datetime import datetime, timezone

import httpx
import pytest
import respx

from koulis import (
    KoulisClient,
    KoulisConflict,
    KoulisExpiredHold,
    KoulisNetworkError,
    KoulisValidationError,
)
from tests.conftest import TEST_BASE_URL, TEST_TOKEN, restaurant_fixture


@pytest.fixture
def client():
    return KoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL)


# ─── search ──────────────────────────────────────────────────────────

@respx.mock
def test_search_happy_path(client):
    respx.get(f"{TEST_BASE_URL}/v1/restaurants/search").mock(
        return_value=httpx.Response(200, json={
            "count": 1,
            "results": [restaurant_fixture()],
        })
    )
    results = client.search(
        city="Paris",
        when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
    assert len(results) == 1
    assert results[0].name == "Sanukiya"


def test_search_naive_datetime_raises(client):
    with pytest.raises(KoulisValidationError):
        client.search(
            city="Paris",
            when=datetime(2026, 5, 12, 20, 0),  # naive!
            party_size=2,
        )


@respx.mock
def test_search_with_filters_sent_as_query_params(client):
    route = respx.get(f"{TEST_BASE_URL}/v1/restaurants/search").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    client.search(
        city="Paris",
        when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        party_size=2,
        cuisine="japonaise",
        dietary="vegan",
    )
    url = str(route.calls.last.request.url)
    assert "cuisine=japonaise" in url
    assert "dietary=vegan" in url


# ─── consume_slot ────────────────────────────────────────────────────

@respx.mock
def test_consume_slot_conflict(client):
    respx.post(f"{TEST_BASE_URL}/v1/restaurants/abc/slots/consume").mock(
        return_value=httpx.Response(409, json={"message": "insufficient capacity"})
    )
    with pytest.raises(KoulisConflict):
        client.consume_slot(
            restaurant_id="abc",
            slot_at=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
            party_size=10,
        )


# ─── hold + confirm ──────────────────────────────────────────────────

@respx.mock
def test_hold_happy_path(client):
    respx.post(f"{TEST_BASE_URL}/v1/holds").mock(
        return_value=httpx.Response(201, json={
            "hold_id": "11111111-1111-1111-1111-111111111111",
            "restaurant_id": "22222222-2222-2222-2222-222222222222",
            "restaurant_name": "Sanukiya",
            "slot_at": "2026-05-12T20:00:00Z",
            "party_size": 2,
            "expires_at": "2026-05-12T20:05:00Z",
            "expires_in_seconds": 300,
        })
    )
    hold = client.hold(
        restaurant_id="22222222-2222-2222-2222-222222222222",
        slot_at=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
    assert hold.party_size == 2


@respx.mock
def test_confirm_expired_hold_raises(client):
    respx.post(f"{TEST_BASE_URL}/v1/reservations").mock(
        return_value=httpx.Response(410, json={"message": "hold expired"})
    )
    with pytest.raises(KoulisExpiredHold):
        client.confirm(
            hold_id="11111111-1111-1111-1111-111111111111",
            customer_name="Test",
            customer_phone="+33600000000",
            customer_email="t@example.com",
        )


# ─── webhooks ────────────────────────────────────────────────────────

@respx.mock
def test_register_webhook_returns_secret(client):
    respx.post(f"{TEST_BASE_URL}/v1/webhooks").mock(
        return_value=httpx.Response(201, json={
            "id": "33333333-3333-3333-3333-333333333333",
            "url": "https://example.com/hook",
            "events_subscribed": ["reservation.created"],
            "description": "test",
            "is_active": True,
            "secret": "abc123def456",
            "created_at": "2026-05-12T10:00:00Z",
        })
    )
    w = client.register_webhook(
        url="https://example.com/hook",
        events=["reservation.created"],
        description="test",
    )
    assert w.secret == "abc123def456"


@respx.mock
def test_delete_webhook_returns_none(client):
    respx.delete(f"{TEST_BASE_URL}/v1/webhooks/abc").mock(
        return_value=httpx.Response(204)
    )
    # Doit retourner None sans exception
    assert client.delete_webhook("abc") is None


# ─── context manager + network errors ────────────────────────────────

def test_context_manager_closes_underlying_client():
    with KoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        assert not c._client.is_closed
    assert c._client.is_closed


@respx.mock
def test_network_error_wrapped(client):
    respx.get(f"{TEST_BASE_URL}/v1/restaurants/search").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    with pytest.raises(KoulisNetworkError):
        client.search(
            city="Paris",
            when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
            party_size=2,
        )


def test_empty_token_raises():
    with pytest.raises(ValueError):
        KoulisClient(api_token="")