from __future__ import annotations

from typing import Any

from spryx_di.events.backend import EventMetadata


class InMemoryEventBackend:
    """In-memory event backend for testing."""

    def __init__(self) -> None:
        self.dispatched: list[tuple[dict[str, Any], EventMetadata]] = []

    async def dispatch(self, payload: dict[str, Any], metadata: EventMetadata) -> None:
        self.dispatched.append((payload, metadata))

    def assert_published(self, event_type: str, **kwargs: object) -> None:
        matches = [
            p
            for p, m in self.dispatched
            if m.event_type == event_type and all(p.get(k) == v for k, v in kwargs.items())
        ]
        assert matches, f"No '{event_type}' event matching {kwargs}"

    def clear(self) -> None:
        self.dispatched.clear()
