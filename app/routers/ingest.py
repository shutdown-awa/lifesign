"""POST /ingest — receive device+health snapshot from phone."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.status import StatusPayload
from app.store import put

router = APIRouter(tags=["ingest"])

# The one key the phone (iOS Shortcuts) presents. Overridable via env so it can
# be rotated without touching code; falls back to the original dev default.
PHONE_KEY = os.environ.get("USER_STATUS_PHONE_KEY", "phone-secret-key-001")


async def _require_ingest_auth(request: Request) -> str:
    """Require the phone key for the ingest endpoint (identity only)."""
    auth = request.headers.get("Authorization", "")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != PHONE_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return parts[1]


@router.post("/ingest", status_code=204)
async def ingest(payload: StatusPayload, _key: str = Depends(_require_ingest_auth)):
    """Accept a device + health status snapshot.

    **Phone-side usage (iOS Shortcuts):**

        URL:  POST https://<your-server>/ingest
        Headers:
            Authorization: Bearer <phone key>
            Content-Type:  application/json
        Body:  { "deviceStage": {...}, "health": {...} }

    Returns 204 No Content on success.
    """
    put(payload.model_dump(exclude_none=True))
    return None