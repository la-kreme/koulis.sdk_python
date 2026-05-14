"""Tests for push_availabilities — max_party_size support (v0.5.0)."""

from datetime import date, datetime, timezone

import httpx
import pytest
import respx

from koulis import AsyncKoulisClient, KoulisClient
from tests.conftest import RESTAURANT_ID, TEST_BASE_URL, TEST_TOKEN

PUSH_URL = f"{TEST_BASE_URL}/v1/restaurants/{RESTAURANT_ID}/availabilities"

UPSERT_RESPONSE = {
    "restaurant_id": RESTAURANT_ID,
    "day": "2026-05-14",
    "slots_written": 1,
}

SLOT_AT = datetime(2026, 5, 14, 18, 0, tzinfo=timezone.utc)
TARGET_DAY = date(2026, 5, 14)


# ─── Async client ──────────────────────────────────────────────────────


@pytest.fixture
async def async_client():
    client = AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL)
    yield client
    await client.aclose()


@respx.mock
async def test_async_push_with_max_party_size(async_client):
    """When max_party_size is provided, it appears in the JSON payload."""
    route = respx.put(PUSH_URL).mock(
        return_value=httpx.Response(200, json=UPSERT_RESPONSE)
    )

    await async_client.push_availabilities(
        restaurant_id=RESTAURANT_ID,
        day=TARGET_DAY,
        slots=[
            {"slot_at": SLOT_AT, "capacity_total": 10, "max_party_size": 4},
        ],
    )

    sent = route.calls.last.request
    body = httpx.Request("PUT", PUSH_URL, json=None).read()  # dummy
    import json

    body = json.loads(sent.content)
    assert len(body["slots"]) == 1
    slot = body["slots"][0]
    assert slot["capacity_total"] == 10
    assert slot["max_party_size"] == 4


@respx.mock
async def test_async_push_without_max_party_size(async_client):
    """When max_party_size is omitted, the key is absent from the payload (retro-compat)."""
    route = respx.put(PUSH_URL).mock(
        return_value=httpx.Response(200, json=UPSERT_RESPONSE)
    )

    await async_client.push_availabilities(
        restaurant_id=RESTAURANT_ID,
        day=TARGET_DAY,
        slots=[
            {"slot_at": SLOT_AT, "capacity_total": 10},
        ],
    )

    import json

    body = json.loads(route.calls.last.request.content)
    slot = body["slots"][0]
    assert slot["capacity_total"] == 10
    assert "max_party_size" not in slot


# ─── Sync client ───────────────────────────────────────────────────────


@pytest.fixture
def sync_client():
    client = KoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL)
    yield client
    client.close()


@respx.mock
def test_sync_push_with_max_party_size(sync_client):
    """Sync client: max_party_size present in payload when provided."""
    route = respx.put(PUSH_URL).mock(
        return_value=httpx.Response(200, json=UPSERT_RESPONSE)
    )

    sync_client.push_availabilities(
        restaurant_id=RESTAURANT_ID,
        date=TARGET_DAY,
        slots=[
            {"slot_at": SLOT_AT, "capacity_total": 8, "max_party_size": 6},
        ],
    )

    import json

    body = json.loads(route.calls.last.request.content)
    slot = body["slots"][0]
    assert slot["capacity_total"] == 8
    assert slot["max_party_size"] == 6


@respx.mock
def test_sync_push_without_max_party_size(sync_client):
    """Sync client: max_party_size absent from payload when not provided."""
    route = respx.put(PUSH_URL).mock(
        return_value=httpx.Response(200, json=UPSERT_RESPONSE)
    )

    sync_client.push_availabilities(
        restaurant_id=RESTAURANT_ID,
        date=TARGET_DAY,
        slots=[
            {"slot_at": SLOT_AT, "capacity_total": 8},
        ],
    )

    import json

    body = json.loads(route.calls.last.request.content)
    slot = body["slots"][0]
    assert slot["capacity_total"] == 8
    assert "max_party_size" not in slot
