"""HMAC SHA-256 verification of incoming Koulis webhooks."""

import hmac
from hashlib import sha256


def verify_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """
    Verify a Koulis webhook signature.

    Pass the RAW REQUEST BYTES (not a re-stringified JSON object) —
    otherwise the signature will mismatch due to whitespace or key
    ordering differences.

    The signature header has the form "sha256=<hex>". Returns True
    if the signature matches, False otherwise. Uses constant-time
    comparison to prevent timing attacks.

    Example (FastAPI receiver):

        from fastapi import FastAPI, Request, HTTPException
        from koulis.webhooks import verify_signature, parse_event

        app = FastAPI()
        WEBHOOK_SECRET = os.environ["KOULIS_WEBHOOK_SECRET"]

        @app.post("/webhooks/koulis")
        async def koulis_webhook(request: Request):
            payload = await request.body()
            sig = request.headers.get("X-Koulis-Signature", "")
            if not verify_signature(payload, sig, WEBHOOK_SECRET):
                raise HTTPException(401, "Invalid signature")
            event = parse_event(payload)
            # ... handle event
    """
    if not signature_header.startswith("sha256="):
        return False

    expected_hex = signature_header[len("sha256="):]
    computed = hmac.new(
        secret.encode("utf-8"),
        payload,
        sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, expected_hex)