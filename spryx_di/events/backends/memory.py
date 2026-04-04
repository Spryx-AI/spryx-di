from __future__ import annotations

from spryx_di.events.backend import EventMetadata


class InMemoryEventBackend:
    """In-memory event backend for testing."""

    def __init__(self) -> None:
        self.dispatched: list[tuple[object, EventMetadata]] = []

    async def dispatch(self, event: object, metadata: EventMetadata) -> None:
        self.dispatched.append((event, metadata))

    def assert_published(self, event_type: type, **kwargs: object) -> None:
        matches = [
            e
            for e, _m in self.dispatched
            if isinstance(e, event_type) and all(getattr(e, k) == v for k, v in kwargs.items())
        ]
        assert matches, f"No {event_type.__name__} event matching {kwargs}"

    def clear(self) -> None:
        self.dispatched.clear()
