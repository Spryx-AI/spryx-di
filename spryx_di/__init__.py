"""spryx-di: Lightweight type-based dependency injection for Python modular monoliths."""

from spryx_di.container import Container, ScopedContainer
from spryx_di.errors import (
    CircularDependencyError,
    CircularModuleError,
    ExportWithoutProviderError,
    ModuleBoundaryError,
    ModuleNotFoundError,
    TypeHintRequiredError,
    UnresolvableTypeError,
)
from spryx_di.module import ApplicationContext, Module
from spryx_di.provider import ForwardRef, Provider, Scope, forward_ref

__all__ = [
    "ApplicationContext",
    "CircularDependencyError",
    "CircularModuleError",
    "Container",
    "ExportWithoutProviderError",
    "ForwardRef",
    "Module",
    "ModuleBoundaryError",
    "ModuleNotFoundError",
    "Provider",
    "ScopedContainer",
    "Scope",
    "TypeHintRequiredError",
    "UnresolvableTypeError",
    "forward_ref",
]
