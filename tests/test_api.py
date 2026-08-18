"""Tests for the User Status Server.

Run:  pip install httpx pytest pytest-asyncio && python -m pytest tests/ -v
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

PHONE_KEY = "phone-secret-key-001"
AGENT_KEY = "agent-read-secret-key-001"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _clear_store():
    """Reset in-memory store before each test."""
    from app.store import put
    put({})


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ingest_happy_path(client):
    payload = {
        "deviceStage": {
            "battery": {"percentage": 89, "is_charging": True},
            "network": {"is_using_wifi": True},
        },
        "health": {
            "status": {"is_sleeping": False, "activity": "walking"},
            "body": {"heart_beat": 72},
        },
    }

    resp = await client.post(
        "/ingest",
        json=payload,
        headers={"Authorization": f"Bearer {PHONE_KEY}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_ingest_uses_snake_case_in_store(client):
    """camelCase JSON from iPhone must land in store as snake_case (app uses snake_case)."""
    payload = {
        "deviceStage": {
            "battery": {"percentage": 80, "is_charging": False},
        },
    }
    await client.post(
        "/ingest",
        json=payload,
        headers={"Authorization": f"Bearer {PHONE_KEY}"},
    )
    from app.store import get_all
    store = get_all()
    # snake_case top-level key
    assert "device_stage" in store
    assert store["device_stage"]["battery"]["percentage"] == 80


@pytest.mark.asyncio
async def test_ingest_unauthorized(client):
    resp = await client.post("/ingest", json={})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_query_all_with_agent_key(client):
    payload = {
        "deviceStage": {
            "battery": {"percentage": 80, "is_charging": False},
            "location": {"city": "中山市", "state": "广东省"},
        },
        "health": {
            "status": {"is_sleeping": False, "activity": "静止"},
            "body": {"heart_beat": 65},
        },
    }
    await client.post(
        "/ingest",
        json=payload,
        headers={"Authorization": f"Bearer {PHONE_KEY}"},
    )

    resp = await client.get(
        "/query_all",
        headers={"Authorization": f"Bearer {AGENT_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "device_stage" in data
    assert data["device_stage"]["battery"]["percentage"] == 80
    assert "location" in data["device_stage"]
    assert "health" in data
    assert data["health"]["body"]["heart_beat"] == 65


@pytest.mark.asyncio
async def test_query_all_unauthorized(client):
    resp = await client.get(
        "/query_all",
        headers={"Authorization": "Bearer totally-wrong-key"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_query_all_no_data_returns_empty(client):
    resp = await client.get(
        "/query_all",
        headers={"Authorization": f"Bearer {AGENT_KEY}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {}