## 1. Package Structure

- [x] 1.1 Create `spryx_di/events/__init__.py` with public API exports
- [x] 1.2 Create `spryx_di/events/backends/__init__.py`

## 2. Core Types

- [x] 2.1 Implement `EventHandler[E]` generic base class in `spryx_di/events/handler.py`
- [x] 2.2 Implement `ListenerScope` enum in `spryx_di/events/listener.py`
- [x] 2.3 Implement `EventListener[E]` frozen dataclass in `spryx_di/events/listener.py`
- [x] 2.4 Implement `EventMetadata` frozen dataclass in `spryx_di/events/backend.py`
- [x] 2.5 Implement `AsyncEventBackend` Protocol in `spryx_di/events/backend.py`

## 3. EventBus

- [x] 3.1 Implement `EventBus` class with `register_handler()` and `publish()` in `spryx_di/events/bus.py`
- [x] 3.2 Add event type extraction helper to resolve `E` from `EventHandler[E]` subclasses at runtime

## 4. Built-in Backends

- [x] 4.1 Implement `InMemoryEventBackend` with `dispatched` list, `assert_published`, and `clear` in `spryx_di/events/backends/memory.py`
- [x] 4.2 Implement `CeleryEventBackend` with `send_task` dispatch in `spryx_di/events/backends/celery.py`

## 5. Module Integration

- [x] 5.1 Add `listeners: list[EventListener]` field to `Module` dataclass in `spryx_di/module.py`
- [x] 5.2 Add `event_backend` parameter to `ApplicationContext.__init__`
- [x] 5.3 Implement boot-time listener validation (handler extends EventHandler, resolvable deps, async needs backend)
- [x] 5.4 Auto-register `EventBus` singleton when any module has listeners
- [x] 5.5 Register all module listeners in EventBus during boot

## 6. Public API

- [x] 6.1 Export event types from `spryx_di/events/__init__.py` (EventBus, EventHandler, EventListener, ListenerScope, AsyncEventBackend, EventMetadata)
- [x] 6.2 Re-export key event types from `spryx_di/__init__.py`

## 7. Error Types

- [x] 7.1 Add `InvalidListenerError` and `MissingEventBackendError` to `spryx_di/errors.py`

## 8. Tests

- [x] 8.1 Unit tests for `EventHandler` base class and event type introspection
- [x] 8.2 Unit tests for `EventBus` sync dispatch (single handler, multiple handlers, no handlers)
- [x] 8.3 Unit tests for `EventBus` async dispatch via backend
- [x] 8.4 Unit tests for `InMemoryEventBackend` (capture, assert_published, clear)
- [x] 8.5 Unit tests for `EventListener` and `ListenerScope`
- [x] 8.6 Unit tests for boot validation (invalid handler, unresolvable deps, async without backend)
- [x] 8.7 Integration test: full ApplicationContext with modules, listeners, and EventBus publish flow
