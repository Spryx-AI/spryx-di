from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from spryx_di.events.backend import EventMetadata

if TYPE_CHECKING:
    from celery import Celery

    from spryx_di.module import ApplicationContext


class CeleryEventBackend:
    def __init__(
        self,
        celery_app: Celery,
        task_name: str = "spryx_di.handle_event",
        default_queue: str = "events",
    ) -> None:
        self._app = celery_app
        self._task_name = task_name
        self._default_queue = default_queue

    def register_worker(self, app_context: ApplicationContext) -> None:
        ctx = app_context

        @self._app.task(name=self._task_name)
        def handle_event(event_type: str, handler_type: str, payload: dict[str, Any]) -> None:
            import asyncio

            event_cls = ctx.event_registry[event_type]
            handler_cls = ctx.handler_registry[handler_type]
            event = event_cls(**payload)
            handler = ctx.resolve(handler_cls)
            asyncio.run(handler.handle(event))

    async def dispatch(self, payload: dict[str, Any], metadata: EventMetadata) -> None:
        await asyncio.to_thread(
            self._app.send_task,
            self._task_name,
            kwargs={
                "event_type": metadata.event_type,
                "handler_type": metadata.handler_type,
                "payload": payload,
            },
            queue=f"{self._default_queue}.{metadata.event_type}",
        )
