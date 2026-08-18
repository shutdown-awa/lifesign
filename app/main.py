"""User Status Server — lightweight HTTP service for device & health telemetry.

Single process, single port (default 8764):

    POST /ingest      — phone pushes latest snapshot (phone API-key auth)
    GET  /query_all   — full snapshot for AI agents (agent key auth)
    GET  /health      — health check (no auth)
    /mcp              — MCP streamable-http gateway for Hermes (same process)

Only /ingest is meant to be reverse-proxied publicly; the MCP endpoint is
reached via loopback by Hermes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.mcp_server import mcp, mcp_starlette_app
from app.routers.ingest import router as ingest_router
from app.routers.query_all import router as query_all_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Boot the MCP session manager alongside the FastAPI app.

    The mounted FastMCP Starlette app has its own lifespan (session_manager.run)
    but sub-app lifespans are NOT propagated by FastAPI when using mount().
    We therefore run the MCP session manager explicitly here.
    """
    # Ensure the Starlette app (and its session manager) exists first
    _mcp_app = mcp_starlette_app()
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Lifesign — User Status & Health Telemetry Server",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

# ------- routes -----------------------------------------------------------

app.include_router(ingest_router, prefix="")
app.include_router(query_all_router, prefix="")

# ------- MCP gateway (mounted same-process at /mcp) -----------------------

app.mount("/mcp", mcp_starlette_app())


# ------- health check -----------------------------------------------------

@app.get("/health", tags=["health"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}