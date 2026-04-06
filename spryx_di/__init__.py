"""spryx-di: Lightweight type-based dependency injection for Python modular monoliths."""

from spryx_di.container import Container, ScopedContainer
from spryx_di.errors import (
    AmbiguousExportError,
    CircularDependencyError,
    CircularImportError,
    ExportWithoutProviderError,
    InvalidListenerError,
    MissingEventBackendError,
    ModuleBoundaryError,
    SerializationError,
    SpryxDIError,
    TypeHintRequiredError,
    UnresolvableTypeError,
    UnresolvedImportError,
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
    Provider,
    Scope,
    ValueProvider,
)

__all__ = [
    "AmbiguousExportError",
    "ApplicationContext",
    "AsyncEventBackend",
    "CircularDependencyError",
    "CircularImportError",
    "ClassProvider",
    "Container",
    "EventBus",
    "EventHandler",
    "EventListener",
    "EventMetadata",
    "ExistingProvider",
    "ExportWithoutProviderError",
    "FactoryProvider",
    "InvalidListenerError",
    "ListenerScope",
    "MissingEventBackendError",
    "Module",
    "ModuleBoundaryError",
    "Provider",
    "ScopedContainer",
    "Scope",
    "SerializationError",
    "SpryxDIError",
    "TypeHintRequiredError",
    "UnresolvedImportError",
    "UnresolvableTypeError",
    "ValueProvider",
]
