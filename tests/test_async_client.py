"""Tests for AsyncKoulisClient (async) using respx."""

from datetime import datetime, timezone

import httpx
import pytest
import respx

from koulis import (
    AsyncKoulisClient,
    KoulisConflict,
    KoulisValidationError,
)
from tests.conftest import TEST_BASE_URL, TEST_TOKEN, restaurant_fixture


@pytest.fixture
async def async_client():
    client = AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL)
    yield client
    await client.aclose()


@respx.mock
async def test_async_search_happy_path(async_client):
    respx.get(f"{TEST_BASE_URL}/v1/restaurants/search").mock(
        return_value=httpx.Response(200, json={
            "count": 1,
            "results": [restaurant_fixture()],
        })
    )
    results = await async_client.search(
        city="Paris",
        when=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
    assert results[0].name == "Sanukiya"


async def test_async_naive_datetime_raises(async_client):
    with pytest.raises(KoulisValidationError):
        await async_client.search(
            city="Paris",
            when=datetime(2026, 5, 12, 20, 0),
            party_size=2,
        )


@respx.mock
async def test_async_consume_slot_conflict(async_client):
    respx.post(f"{TEST_BASE_URL}/v1/restaurants/abc/slots/consume").mock(
        return_value=httpx.Response(409, json={"message": "no capacity"})
    )
    with pytest.raises(KoulisConflict):
        await async_client.consume_slot(
            restaurant_id="abc",
            slot_at=datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc),
            party_size=10,
        )


async def test_async_context_manager():
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        assert not c._client.is_closed
    assert c._client.is_closed