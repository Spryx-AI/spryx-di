from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

from spryx_di.events.handler import EventHandler

E = TypeVar("E")


class ListenerScope(Enum):
    SYNC = "sync"
    ASYNC = "async"


@dataclass(frozen=True)
class EventListener(Generic[E]):
    event: type[E]
    handler: type[EventHandler[E]]
    scope: ListenerScope = field(default=ListenerScope.SYNC)
