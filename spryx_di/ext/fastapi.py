from __future__ import annotations

from typing import Any, TypeVar

from fastapi import Depends, FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from spryx_di.container import Container

T = TypeVar("T")


def configure(app: FastAPI, container: Container) -> None:
    app.state.container = container
    app.add_middleware(RequestScopeMiddleware)


def Inject(cls: type[T]) -> Any:
    def _resolve(request: Request) -> T:
        container: Container = request.app.state.container
        return container.resolve(cls)

    return Depends(_resolve)


def ScopedInject(cls: type[T]) -> Any:
    def _resolve(request: Request) -> T:
        scope: Container = request.state.scope
        return scope.resolve(cls)

    return Depends(_resolve)


class RequestScopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        container: Container = request.app.state.container
        scope = container.create_scope()
        request.state.scope = scope
        return await call_next(request)
