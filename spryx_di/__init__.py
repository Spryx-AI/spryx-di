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
from spryx_di.provider import (
    ClassProvider,
    ExistingProvider,
    FactoryProvider,
    ForwardRef,
    Provider,
    Scope,
    ValueProvider,
    forward_ref,
)

__all__ = [
    "ApplicationContext",
    "CircularDependencyError",
    "CircularModuleError",
    "ClassProvider",
    "Container",
    "ExistingProvider",
    "ExportWithoutProviderError",
    "FactoryProvider",
    "ForwardRef",
    "Module",
    "ModuleBoundaryError",
    "ModuleNotFoundError",
    "Provider",
    "ScopedContainer",
    "Scope",
    "TypeHintRequiredError",
    "UnresolvableTypeError",
    "ValueProvider",
    "forward_ref",
]
