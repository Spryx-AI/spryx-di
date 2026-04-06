from __future__ import annotations

from typing import Any, TypeVar

from fastapi import Depends, FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from spryx_di.container import Container
from spryx_di.errors import PublicAccessError
from spryx_di.module import ApplicationContext

T = TypeVar("T")


def configure(app: FastAPI, ctx: ApplicationContext | Container) -> None:
    if isinstance(ctx, ApplicationContext):
        app.state.container = ctx.container
        app.state.app_context = ctx
    else:
        app.state.container = ctx
        app.state.app_context = None
    app.add_middleware(RequestScopeMiddleware)


def Inject(cls: type[T]) -> Any:
    def _resolve(request: Request) -> T:
        app_ctx: ApplicationContext | None = getattr(request.app.state, "app_context", None)
        if app_ctx is not None and not app_ctx.is_public(cls):
            raise PublicAccessError(cls)
        container: Container = request.app.state.container
        return container.resolve(cls)

    return Depends(_resolve)


def ScopedInject(cls: type[T]) -> Any:
    def _resolve(request: Request) -> T:
        app_ctx: ApplicationContext | None = getattr(request.app.state, "app_context", None)
        if app_ctx is not None and not app_ctx.is_public(cls):
            raise PublicAccessError(cls)
        scope: Container = request.state.scope
        return scope.resolve(cls)

    return Depends(_resolve)


class RequestScopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        container: Container = request.app.state.container
        scope = container.create_scope()
        request.state.scope = scope
        return await call_next(request)
