from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from spryx_di.errors import SerializationError


def serialize_event(event: Any) -> dict[str, Any]:
    if isinstance(event, dict):
        return event

    if hasattr(event, "to_dict"):
        return event.to_dict()

    if hasattr(event, "model_dump"):
        return event.model_dump()

    if is_dataclass(event) and not isinstance(event, type):
        return asdict(event)

    raise SerializationError(type(event).__name__)
