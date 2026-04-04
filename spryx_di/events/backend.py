from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EventMetadata:
    event_type: str
    handler_type: str


class AsyncEventBackend(Protocol):
    async def dispatch(self, event: object, metadata: EventMetadata) -> None: ...
