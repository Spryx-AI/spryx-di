from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from spryx_di.container import Container

_MISSING = object()


@contextmanager
def override(container: Container, overrides: dict[type, Any]) -> Iterator[None]:
    """Temporarily override container registrations, restoring originals on exit."""
    backups: dict[type, dict[str, Any]] = {}

    for type_ in overrides:
        backups[type_] = {
            "instances": container._instances.pop(type_, _MISSING),
            "factories": container._factories.pop(type_, _MISSING),
            "singletons": container._singletons.pop(type_, _MISSING),
            "transients": container._transients.pop(type_, _MISSING),
            "singleton_cache": container._singleton_cache.pop(type_, _MISSING),
        }

        value = overrides[type_]
        if isinstance(value, type):
            container._transients[type_] = value
        else:
            container._instances[type_] = value

    try:
        yield
    finally:
        for type_, backup in backups.items():
            container._instances.pop(type_, None)
            container._factories.pop(type_, None)
            container._singletons.pop(type_, None)
            container._transients.pop(type_, None)
            container._singleton_cache.pop(type_, None)

            for registry_name, value in backup.items():
                if value is not _MISSING:
                    getattr(container, f"_{registry_name}")[type_] = value
