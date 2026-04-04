from __future__ import annotations

from typing import TypeVar

from pydantic_settings import BaseSettings

from spryx_di.container import Container

T = TypeVar("T", bound=BaseSettings)


def register_settings(container: Container, settings_class: type[T]) -> T:
    instance = settings_class()
    container.instance(settings_class, instance)
    return instance
