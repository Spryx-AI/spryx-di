from __future__ import annotations

from typing import Generic, TypeVar, get_args

E = TypeVar("E")


class EventHandler(Generic[E]):
    """Base class for typed event handlers."""

    async def handle(self, event: E) -> None:
        raise NotImplementedError


def extract_event_type(handler_cls: type) -> type:
    for base in getattr(handler_cls, "__orig_bases__", ()):
        origin = getattr(base, "__origin__", None)
        if origin is EventHandler:
            args = get_args(base)
            if args:
                return args[0]  # type: ignore[no-any-return]
    msg = (
        f"Cannot extract event type from '{handler_cls.__name__}'. "
        f"Ensure it directly extends EventHandler[SomeEvent]."
    )
    raise TypeError(msg)
