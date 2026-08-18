"""MCP gateway — exposes the latest device+health snapshot to AI agents.

Same-process design: this module is imported by app.main and its FastMCP
server is mounted at /mcp inside the *same* FastAPI app. The tools read
directly from app.store (shared in-memory) — no HTTP hop, no second port.

Reverse proxy note: this endpoint is NOT exposed publicly. It binds to the
same port as the main app but Hermes reaches it via loopback (127.0.0.1).
Only POST /ingest is reverse-proxied for the phone.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import app.store as store

mcp = FastMCP(
    "user-status",
    # Internal route is "/" — we mount the returned Starlette app at /mcp in
    # the main FastAPI app. Having the internal route also be /mcp would cause
    # a double-path mismatch (307 → 404) under FastAPI's mount.
    streamable_http_path="/",
    instructions=(
        "Provides the user's current device & health telemetry: battery, "
        "location, network, usage, health (heart rate, temperature, sleep, "
        "workout). The snapshot is whatever the phone last uploaded."
    ),
)


@mcp.tool()
async def get_status() -> dict:
    """Return the full latest device+health snapshot uploaded by the phone.

    Returns a dict like::

        {
          "package": {"version": 1, "date": "2026-08-18T07:44:05+08:00"},
          "device_stage": {
            "battery": {"percentage": 89, "is_charging": True},
            "location": {...},
            "network": {"is_using_wifi": True},
            "usage": {...}
          },
          "health": {
            "body": {"heart_beat": 72, "body_temperature": 36.6, ...},
            "status": {"is_sleeping": False, "activity": "walking"},
            "workout": {...}
          }
        }

    ``package.date`` is the phone-side upload timestamp — check it before using
    the data (stale data should trigger a fresh pull via the STS trigger).

    If no snapshot has been uploaded yet, returns an empty dict.
    """
    return store.get_all()


@mcp.tool()
async def get_battery() -> dict:
    """Return just the battery info (percentage + charging state)."""
    return store.get_all().get("device_stage", {}).get("battery", {})


@mcp.tool()
async def get_health() -> dict:
    """Return just the health info (heart rate, temperature, sleep, workout)."""
    return store.get_all().get("health", {})


@mcp.tool()
async def get_location() -> dict:
    """Return just the location info (state, city, street, lat/lng)."""
    return store.get_all().get("device_stage", {}).get("location", {})


def mcp_starlette_app():
    """Return the Starlette app to mount at /mcp in the main FastAPI app."""
    return mcp.streamable_http_app()