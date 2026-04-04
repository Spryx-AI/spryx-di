"""
Application composition root.

This is the ONLY place where all modules are wired together.
Each module is self-contained — they don't know about each other's implementations.
spryx-di resolves cross-module dependencies automatically via type hints.
Module boundaries are enforced: only exported types are visible across modules.
"""

from __future__ import annotations

from fastapi import FastAPI
from modules.catalog.module import catalog_module
from modules.identity.module import identity_module
from modules.orders.module import orders_module

from api.routes import router
from api.settings import AppSettings
from spryx_di import ApplicationContext
from spryx_di.ext.fastapi import configure
from spryx_di.ext.settings import register_settings

# ── Compose all modules with boundary enforcement ──
app_context = ApplicationContext(
    modules=[
        identity_module,  # exports: [UserReader]
        catalog_module,  # exports: [ProductReader]
        orders_module,  # imports: [identity, catalog]
    ],
)

# ── Register settings from environment ──
settings = register_settings(app_context.container, AppSettings)

# ── Create FastAPI app ──
app = FastAPI(title=settings.app_name, debug=settings.debug)
configure(app, app_context.container)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
