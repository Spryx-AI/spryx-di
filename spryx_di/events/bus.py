from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from spryx_di.errors import MissingEventBackendError
from spryx_di.events.backend import AsyncEventBackend, EventMetadata
from spryx_di.events.handler import EventHandler
from spryx_di.events.listener import ListenerScope
from spryx_di.events.serialization import serialize_event

if TYPE_CHECKING:
    from spryx_di.container import Container


@dataclass(frozen=True)
class _RegisteredHandler:
    handler_type: type[EventHandler]
    scope: ListenerScope


class EventBus:
    """Dispatches events to registered handlers."""

    def __init__(
        self,
        container: Container,
        async_backend: AsyncEventBackend | None = None,
    ) -> None:
        self._container = container
        self._async_backend = async_backend
        self._handlers: dict[type, list[_RegisteredHandler]] = {}

    def register_handler(
        self,
        event_type: type,
        handler_type: type[EventHandler],
        scope: ListenerScope,
    ) -> None:
        self._handlers.setdefault(event_type, []).append(
            _RegisteredHandler(handler_type=handler_type, scope=scope)
        )

    async def publish(self, event: object) -> None:
        event_type = type(event)
        for registered in self._handlers.get(event_type, []):
            if registered.scope == ListenerScope.SYNC:
                handler = self._container.resolve(registered.handler_type)
                await handler.handle(event)
            else:
                if self._async_backend is None:
                    raise MissingEventBackendError("(runtime)", registered.handler_type.__name__)
                payload = serialize_event(event)
                metadata = EventMetadata(
                    event_type=event_type.__name__,
                    handler_type=registered.handler_type.__name__,
                )
                await self._async_backend.dispatch(payload, metadata)
