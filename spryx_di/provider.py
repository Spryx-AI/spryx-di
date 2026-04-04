from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


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
class ClassProvider:
    """Provide a dependency via auto-wired class instantiation."""

    provide: type
    use_class: type
    scope: Scope = Scope.SINGLETON


@dataclass(frozen=True)
class FactoryProvider:
    """Provide a dependency via a factory callable."""

    provide: type
    use_factory: Any  # Callable[[Container], Any]
    scope: Scope = Scope.SINGLETON


@dataclass(frozen=True)
class ValueProvider:
    """Provide a pre-instantiated value."""

    provide: type
    use_value: Any


@dataclass(frozen=True)
class ExistingProvider:
    """Alias: when provide is requested, resolve use_existing instead."""

    provide: type
    use_existing: type


Provider = ClassProvider | FactoryProvider | ValueProvider | ExistingProvider
