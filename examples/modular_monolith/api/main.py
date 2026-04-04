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

app_context = ApplicationContext(
    modules=[identity_module, catalog_module, orders_module],
)

settings = register_settings(app_context.container, AppSettings)

app = FastAPI(title=settings.app_name, debug=settings.debug)
configure(app, app_context.container)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
