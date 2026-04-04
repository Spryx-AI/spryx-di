from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_MISSING = object()


@dataclass(frozen=True)
class ForwardRef:
    """Lazy module reference — avoids circular imports between module files."""

    module_name: str


def forward_ref(name: str) -> ForwardRef:
    return ForwardRef(module_name=name)


class Scope(Enum):
    """Lifecycle scope for a provider."""

    TRANSIENT = "transient"
    SINGLETON = "singleton"


@dataclass(frozen=True)
class Provider:
    """Describes how to provide a dependency via use_class, use_factory, or use_value."""

    provide: type
    use_class: type | None = None
    use_factory: Any | None = None  # Callable[[Container], Any]
    use_value: Any = field(default=_MISSING)
    scope: Scope = Scope.SINGLETON

    def __post_init__(self) -> None:
        sources = [
            self.use_class is not None,
            self.use_factory is not None,
            self.use_value is not _MISSING,
        ]
        count = sum(sources)
        if count == 0:
            msg = (
                f"Provider for '{self.provide.__name__}' must specify exactly one of: "
                f"use_class, use_factory, or use_value"
            )
            raise ValueError(msg)
        if count > 1:
            msg = (
                f"Provider for '{self.provide.__name__}' must specify exactly one of: "
                f"use_class, use_factory, or use_value (got {count})"
            )
            raise ValueError(msg)
