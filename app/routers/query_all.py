"""GET /query_all — unrestricted full snapshot for the AI-agent MCP gateway.

Unlike the old /query endpoint (field-whitelisted per client), this endpoint
returns the *entire* latest snapshot to a caller that presents the agent key.
It exists solely as the data source for the MCP server process, which cannot
share the in-memory store directly.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request

from app.store import get_all

router = APIRouter(tags=["query_all"])

# Key the MCP agent gateway must present. Intentionally an env var so it can
# be rotated without touching code; falls back to a dev default.
AGENT_KEY = os.environ.get("USER_STATUS_AGENT_KEY", "agent-read-secret-key-001")


async def _require_agent_auth(request: Request) -> None:
    """Require the agent key (Bearer token) — identity, not per-field ACL."""
    auth = request.headers.get("Authorization", "")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != AGENT_KEY:
        raise HTTPException(status_code=401, detail="Invalid agent key")


@router.get("/query_all")
async def query_all(_: None = Depends(_require_agent_auth)) -> dict:
    """Return the full latest snapshot (no field filtering)."""
    return get_all()