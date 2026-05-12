"""Shared pytest fixtures and helpers."""

TEST_BASE_URL = "https://test.koulis.local"
TEST_TOKEN = "test_token_abc123"


# Valid UUIDs we reuse in mock responses. Pydantic rejects "abc-123".
RESTAURANT_ID = "22222222-2222-2222-2222-222222222222"
HOLD_ID = "33333333-3333-3333-3333-333333333333"
RESERVATION_ID = "11111111-1111-1111-1111-111111111111"
WEBHOOK_ID = "44444444-4444-4444-4444-444444444444"


def restaurant_fixture(**overrides):
    """Return a valid Restaurant payload matching the API schema."""
    base = {
        "id": RESTAURANT_ID,
        "name": "Sanukiya",
        "country_code": "FR",
        "is_published": True,
        "cuisines": ["japonaise"],
        "formats": [],
        "dietary": [],
        "atmosphere": [],
        "services": [],
        "reviews_count": 0,
        "created_at": "2026-05-12T10:00:00Z",
        "updated_at": "2026-05-12T10:00:00Z",
    }
    base.update(overrides)
    return base