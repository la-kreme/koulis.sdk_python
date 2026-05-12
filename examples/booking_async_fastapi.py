"""
Example: using the async client inside a FastAPI service.

This is the canonical pattern for embedding Koulis as a downstream
dependency: open the client at app startup (lifespan), close it on
shutdown, share a single instance across all requests.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from os import environ

from fastapi import FastAPI, HTTPException

from koulis import AsyncKoulisClient, KoulisAPIError


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.koulis = AsyncKoulisClient(
        api_token=environ["KOULIS_API_TOKEN"],
    )
    yield
    await app.state.koulis.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/restaurants/{city}")
async def find_restaurants(city: str, party_size: int = 2):
    when = (
        datetime.now(tz=timezone.utc)
        .replace(hour=20, minute=0, second=0, microsecond=0)
    )
    try:
        results = await app.state.koulis.search(
            city=city,
            when=when,
            party_size=party_size,
        )
    except KoulisAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return [{"id": str(r.id), "name": r.name} for r in results]