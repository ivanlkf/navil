# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Navil Cloud — FastAPI application."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from navil.cloud.api import router
from navil.cloud.auth import ClerkAuthMiddleware
from navil.cloud.demo import seed_demo_data
from navil.cloud.state import AppState

logger = logging.getLogger(__name__)

DASHBOARD_DIR = Path(__file__).resolve().parent.parent.parent / "dashboard" / "dist"

# ALLOWED_ORIGINS: comma-separated allowed origins.
# Defaults to "*" when unset (local dev / no Clerk).
_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
_allow_origins: list[str] = (
    [o.strip() for o in _origins_env.split(",") if o.strip()] if _origins_env else ["*"]
)


def create_app(with_demo: bool = True) -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="Navil Cloud",
        description="Security dashboard for AI agent fleet monitoring",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Clerk auth — no-op when CLERK_SECRET_KEY is not set
    app.add_middleware(ClerkAuthMiddleware)

    app.include_router(router)

    @app.on_event("startup")
    def on_startup() -> None:
        # Initialize persistent storage (creates tables if needed)
        try:
            from navil.cloud.database import init_db

            init_db()
        except Exception:
            logger.warning("Database initialization skipped (sqlalchemy not installed?)")

        state = AppState.get()
        if with_demo:
            seed_demo_data(state)
            logger.info("Demo data seeded: 5 agents, ~150 invocations, 5 credentials")

    # Serve frontend static files if built
    if DASHBOARD_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(DASHBOARD_DIR / "assets")), name="assets")

        @app.get("/{path:path}")
        def serve_frontend(path: str) -> FileResponse:
            """Serve the React SPA — all non-API routes go to index.html."""
            file_path = DASHBOARD_DIR / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            # Never cache index.html so new builds are picked up immediately
            return FileResponse(
                str(DASHBOARD_DIR / "index.html"),
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )
    else:

        @app.get("/")
        def no_frontend() -> dict[str, str]:
            return {
                "message": "Navil Cloud API is running. Frontend not built yet.",
                "hint": "Run: cd dashboard && npm install && npm run build",
            }

    return app


def serve(host: str = "0.0.0.0", port: int = 8484) -> None:
    """Launch the Navil Cloud server."""
    import uvicorn

    app = create_app()
    logger.info(f"Starting Navil Cloud at http://localhost:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
