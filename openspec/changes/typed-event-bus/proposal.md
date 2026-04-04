## Why

spryx_di provides module boundaries and dependency injection but has no built-in mechanism for cross-module communication. Teams end up importing handlers directly across module boundaries or building ad-hoc pub/sub. A typed event bus — integrated with the existing Module/ApplicationContext system — gives modules a decoupled, type-safe way to react to each other's domain events, with pluggable async backends for background processing.

## What Changes

- Add `EventHandler[E]` generic base class so handlers declare which event type they accept, enabling static type checking.
- Add `EventBus` mediator that dispatches events to registered handlers, supporting both sync (in-process) and async (background) scopes.
- Add `EventListener` dataclass and `ListenerScope` enum for declarative listener registration inside `Module`.
- **BREAKING**: Extend `Module` with an optional `listeners: list[EventListener]` field.
- **BREAKING**: Extend `ApplicationContext` with an optional `event_backend` parameter and boot-time validation of listeners.
- Add `AsyncEventBackend` protocol for pluggable async dispatch.
- Ship two built-in backends: `CeleryEventBackend` and `InMemoryEventBackend` (for testing).
- Register `EventBus` as a singleton automatically when any module declares listeners.

## Capabilities

### New Capabilities
- `event-handler`: Generic `EventHandler[E]` base class with typed `handle(event: E)` contract
- `event-bus`: `EventBus` mediator that routes published events to registered handlers by type
- `event-listener`: `EventListener` dataclass and `ListenerScope` enum for declarative registration in modules
- `async-event-backend`: `AsyncEventBackend` protocol with `CeleryEventBackend` and `InMemoryEventBackend` implementations
- `event-boot-validation`: ApplicationContext boot-time validation of listener registrations (handler type, resolvability, backend presence)

### Modified Capabilities
- `module-system`: Module gains an optional `listeners` field; ApplicationContext gains `event_backend` parameter and listener validation at boot

## Impact

- **Code**: New `spryx_di/events/` package with handler, bus, listener, backend modules plus `spryx_di/events/backends/` sub-package.
- **Existing API**: `Module` and `ApplicationContext` signatures change (additive but keyword-only, so non-breaking for most users). Marked BREAKING above for completeness.
- **Dependencies**: Core event system remains dependency-free. `CeleryEventBackend` requires `celery` as an optional dependency.
- **Tests**: New unit tests for event bus, handler dispatch, listener validation, and both backends.
