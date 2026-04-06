"""spryx-di: Lightweight type-based dependency injection for Python modular monoliths."""

from spryx_di.container import Container, ScopedContainer
from spryx_di.errors import (
    CircularDependencyError,
    CircularModuleError,
    ExportWithoutProviderError,
    InvalidListenerError,
    MissingEventBackendError,
    ModuleBoundaryError,
    ModuleNotFoundError,
    SerializationError,
    TypeHintRequiredError,
    UnresolvableTypeError,
)
from spryx_di.events import (
    AsyncEventBackend,
    EventBus,
    EventHandler,
    EventListener,
    EventMetadata,
    ListenerScope,
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
    "AsyncEventBackend",
    "CircularDependencyError",
    "CircularModuleError",
    "ClassProvider",
    "Container",
    "EventBus",
    "EventHandler",
    "EventListener",
    "EventMetadata",
    "ExistingProvider",
    "ExportWithoutProviderError",
    "FactoryProvider",
    "ForwardRef",
    "InvalidListenerError",
    "ListenerScope",
    "MissingEventBackendError",
    "Module",
    "ModuleBoundaryError",
    "ModuleNotFoundError",
    "Provider",
    "ScopedContainer",
    "Scope",
    "SerializationError",
    "TypeHintRequiredError",
    "UnresolvableTypeError",
    "ValueProvider",
    "forward_ref",
]
