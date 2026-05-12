"""
Example: onboard a new restaurant from the partner side (e.g. when a
restaurant signs up for Koulis through reservation_service / La Krème).

Three steps:
1. Register the restaurant — receive Koulis-assigned UUID, store it locally
2. Push 7 days of availabilities upfront
3. Register the webhook endpoint — receive the signing secret, store it

Run once per restaurant activation. Idempotency on slot push is
guaranteed by the API (transactional upsert per date).
"""

import asyncio
from datetime import date, datetime, time, timedelta, timezone
from os import environ

from koulis import AsyncKoulisClient


async def main() -> None:
    async with AsyncKoulisClient(api_token=environ["KOULIS_API_TOKEN"]) as koulis:
        # 1. Register the restaurant
        restaurant = await koulis.register_restaurant(
            name="Sanukiya",
            country_code="FR",
            slug="sanukiya-paris",
            address="9 rue d'Argenteuil",
            postal_code="75001",
            city_name="Paris",
            cuisines=["japonaise"],
            formats=["déjeuner", "dîner"],
            is_published=True,
            source="lakreme",
        )
        print(f"Registered: {restaurant.id} — {restaurant.name}")
        print(f"Persist this koulis_id in your local restaurants table")

        # 2. Push 7 days of availabilities (3 slots per day, 4 covers each)
        today = date.today()
        for offset in range(7):
            target_date = today + timedelta(days=offset)
            slots = [
                {
                    "slot_at": datetime.combine(
                        target_date,
                        time(hour=19 + i),
                        tzinfo=timezone.utc,
                    ),
                    "capacity_total": 4,
                }
                for i in range(3)
            ]
            await koulis.push_availabilities(
                restaurant_id=restaurant.id,
                date=target_date,
                slots=slots,
            )
        print("7 days of availabilities pushed")

        # 3. Register the webhook endpoint
        webhook = await koulis.register_webhook(
            url=environ["RESERVATION_SERVICE_WEBHOOK_URL"],
            events=[
                "reservation.created",
                "hold.created",
                "hold.released",
                "hold.expired",
            ],
            description="reservation_service webhook receiver",
        )
        print(f"Webhook registered: {webhook.id}")
        print(f"Store this secret IMMEDIATELY (shown only once):")
        print(f"   {webhook.secret}")


if __name__ == "__main__":
    asyncio.run(main())