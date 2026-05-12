"""
Example: complete booking flow with the synchronous client.

Use case: a CLI script, a backend cron, or any non-async caller
that wants to book a restaurant slot end-to-end.
"""

import os
from datetime import datetime, timezone

from koulis import KoulisClient, KoulisConflict, KoulisExpiredHold


def main() -> None:
    with KoulisClient(api_token=os.environ["KOULIS_API_TOKEN"]) as client:
        when = datetime(2026, 5, 12, 20, 0, tzinfo=timezone.utc)

        # 1. Discover restaurants
        restaurants = client.search(
            city="Paris",
            when=when,
            party_size=2,
            cuisine="japonaise",
        )
        if not restaurants:
            print("No restaurants available.")
            return

        target = restaurants[0]
        print(f"Selected: {target.name}")

        # 2. List available slots for that restaurant
        slots = client.discover_slots(
            restaurant_id=target.id,
            when=when,
            party_size=2,
        )
        if not slots:
            print(f"No slots for {target.name}.")
            return

        # 3. Create a 5-min hold on the first slot
        try:
            hold = client.hold(
                restaurant_id=target.id,
                slot_at=slots[0].slot_at,
                party_size=2,
            )
        except KoulisConflict:
            print("Slot just taken by another client.")
            return

        print(f"Hold created: {hold.hold_id} (expires in {hold.expires_in_seconds}s)")

        # 4. Confirm the hold to finalize the reservation
        try:
            reservation = client.confirm(
                hold_id=hold.hold_id,
                customer_name="Massimo Marcellin",
                customer_phone="+33600000000",
                customer_email="massimo@koulis.app",
            )
        except KoulisExpiredHold:
            print("Hold expired before confirmation — start over.")
            return

        print(f"Reservation confirmed: {reservation.confirmation_id}")


if __name__ == "__main__":
    main()