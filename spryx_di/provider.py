from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Scope(Enum):
    """Lifecycle scope for a provider."""

    TRANSIENT = "transient"
    SINGLETON = "singleton"


@dataclass(frozen=True)
class ClassProvider:
    """Provide a dependency via auto-wired class instantiation.

    When *use_class* is omitted it defaults to *provide*, so
    ``ClassProvider(provide=Foo)`` is equivalent to
    ``ClassProvider(provide=Foo, use_class=Foo)``.
    """

    provide: type
    use_class: type | None = None
    scope: Scope = Scope.SINGLETON
    export: bool = False
    public: bool = False

    def __post_init__(self) -> None:
        if self.use_class is None:
            object.__setattr__(self, "use_class", self.provide)


@dataclass(frozen=True)
class FactoryProvider:
    """Provide a dependency via a factory callable."""

    provide: type
    use_factory: Any  # Callable[[Container], Any]
    scope: Scope = Scope.SINGLETON
    export: bool = False
    public: bool = False


@dataclass(frozen=True)
class ValueProvider:
    """Provide a pre-instantiated value."""

    provide: type
    use_value: Any
    export: bool = False
    public: bool = False


@dataclass(frozen=True)
class ExistingProvider:
    """Alias: when provide is requested, resolve use_existing instead."""

    provide: type
    use_existing: type
    export: bool = False
    public: bool = False


Provider = ClassProvider | FactoryProvider | ValueProvider | ExistingProvider


def public(*types: type) -> list[ClassProvider]:
    """Helper to declare multiple types as public ClassProviders."""
    return [ClassProvider(provide=t, use_class=t, public=True) for t in types]
