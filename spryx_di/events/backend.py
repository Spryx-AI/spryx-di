from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class EventMetadata:
    event_type: str
    handler_type: str


class AsyncEventBackend(Protocol):
    async def dispatch(self, payload: dict[str, Any], metadata: EventMetadata) -> None: ...
