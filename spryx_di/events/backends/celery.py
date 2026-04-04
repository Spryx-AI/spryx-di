from __future__ import annotations

from dataclasses import asdict
from typing import Any

from spryx_di.events.backend import EventMetadata


class CeleryEventBackend:
    def __init__(
        self,
        celery_app: Any,
        task_name: str = "spryx_di.handle_event",
    ) -> None:
        self._app = celery_app
        self._task_name = task_name

    async def dispatch(self, event: object, metadata: EventMetadata) -> None:
        payload = self._serialize(event)
        self._app.send_task(
            self._task_name,
            kwargs={
                "event_type": metadata.event_type,
                "handler_type": metadata.handler_type,
                "payload": payload,
            },
        )

    @staticmethod
    def _serialize(event: object) -> dict[str, Any]:
        return asdict(event)  # type: ignore[arg-type]
