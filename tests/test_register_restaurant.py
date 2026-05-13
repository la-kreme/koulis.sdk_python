"""Tests for register_restaurant timezone/rating params and update_restaurant."""

import json

import httpx
import pytest
import respx

from koulis import AsyncKoulisClient, KoulisClient
from tests.conftest import (
    RESTAURANT_ID,
    TEST_BASE_URL,
    TEST_TOKEN,
    restaurant_fixture,
)


# ─── register_restaurant: timezone in payload ───────────────────────────


@respx.mock
async def test_async_register_sends_timezone_when_provided():
    route = respx.post(f"{TEST_BASE_URL}/v1/restaurants").mock(
        return_value=httpx.Response(
            201, json=restaurant_fixture(timezone="Asia/Tokyo")
        )
    )
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        r = await c.register_restaurant(
            name="Tokyo Ramen", country_code="JP", timezone="Asia/Tokyo"
        )
    assert r.timezone == "Asia/Tokyo"
    sent = json.loads(route.calls[0].request.content)
    assert sent["timezone"] == "Asia/Tokyo"


@respx.mock
async def test_async_register_omits_timezone_when_none():
    route = respx.post(f"{TEST_BASE_URL}/v1/restaurants").mock(
        return_value=httpx.Response(201, json=restaurant_fixture())
    )
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        await c.register_restaurant(name="Le Koulis", country_code="FR")
    sent = json.loads(route.calls[0].request.content)
    assert "timezone" not in sent


@respx.mock
async def test_async_register_sends_rating_when_provided():
    route = respx.post(f"{TEST_BASE_URL}/v1/restaurants").mock(
        return_value=httpx.Response(
            201, json=restaurant_fixture(rating=4.5)
        )
    )
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        r = await c.register_restaurant(
            name="Good Place", country_code="FR", rating=4.5
        )
    assert r.rating == 4.5
    sent = json.loads(route.calls[0].request.content)
    assert sent["rating"] == 4.5


@respx.mock
async def test_async_register_omits_rating_when_none():
    route = respx.post(f"{TEST_BASE_URL}/v1/restaurants").mock(
        return_value=httpx.Response(201, json=restaurant_fixture())
    )
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        await c.register_restaurant(name="Le Koulis", country_code="FR")
    sent = json.loads(route.calls[0].request.content)
    assert "rating" not in sent


# ─── register_restaurant: sync client ───────────────────────────────────


@respx.mock
def test_sync_register_sends_timezone():
    route = respx.post(f"{TEST_BASE_URL}/v1/restaurants").mock(
        return_value=httpx.Response(
            201, json=restaurant_fixture(timezone="Europe/London")
        )
    )
    with KoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        r = c.register_restaurant(
            name="London Pub", country_code="GB", timezone="Europe/London"
        )
    assert r.timezone == "Europe/London"
    sent = json.loads(route.calls[0].request.content)
    assert sent["timezone"] == "Europe/London"


# ─── update_restaurant ──────────────────────────────────────────────────


@respx.mock
async def test_async_update_restaurant_sends_patch():
    route = respx.patch(f"{TEST_BASE_URL}/v1/restaurants/{RESTAURANT_ID}").mock(
        return_value=httpx.Response(
            200, json=restaurant_fixture(timezone="America/New_York")
        )
    )
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        r = await c.update_restaurant(RESTAURANT_ID, timezone="America/New_York")
    assert r.timezone == "America/New_York"
    sent = json.loads(route.calls[0].request.content)
    assert sent == {"timezone": "America/New_York"}


@respx.mock
def test_sync_update_restaurant_sends_patch():
    route = respx.patch(f"{TEST_BASE_URL}/v1/restaurants/{RESTAURANT_ID}").mock(
        return_value=httpx.Response(
            200, json=restaurant_fixture(timezone="Asia/Tokyo", rating=4.8)
        )
    )
    with KoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        r = c.update_restaurant(RESTAURANT_ID, timezone="Asia/Tokyo", rating=4.8)
    assert r.timezone == "Asia/Tokyo"
    sent = json.loads(route.calls[0].request.content)
    assert sent == {"timezone": "Asia/Tokyo", "rating": 4.8}


async def test_async_update_restaurant_raises_on_empty():
    async with AsyncKoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        with pytest.raises(ValueError, match="At least one field"):
            await c.update_restaurant(RESTAURANT_ID)


def test_sync_update_restaurant_raises_on_empty():
    with KoulisClient(api_token=TEST_TOKEN, base_url=TEST_BASE_URL) as c:
        with pytest.raises(ValueError, match="At least one field"):
            c.update_restaurant(RESTAURANT_ID)
