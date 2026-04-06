## ADDED Requirements

### Requirement: Validate handler extends EventHandler
During boot, `ApplicationContext` SHALL verify that every listener's handler class is a subclass of `EventHandler`. If not, it SHALL raise an error.

#### Scenario: Handler not extending EventHandler
- **WHEN** a module declares `EventListener(event=E, handler=PlainClass)` where `PlainClass` does not extend `EventHandler`
- **THEN** boot SHALL raise an error with message indicating the handler must extend `EventHandler`

### Requirement: Validate handler is resolvable
During boot, `ApplicationContext` SHALL verify that the handler's `__init__` dependencies are registered in the container. If not, it SHALL raise an error.

#### Scenario: Handler with unresolvable dependency
- **WHEN** a handler's `__init__` requires `SomeService` which is not registered
- **THEN** boot SHALL raise an error indicating the dependency cannot be resolved

### Requirement: Validate async listeners require backend
During boot, if any module has a listener with `ListenerScope.ASYNC`, `ApplicationContext` SHALL verify that an `event_backend` was provided. If not, it SHALL raise an error.

#### Scenario: Async listener without backend
- **WHEN** a module declares an async listener and `ApplicationContext` is created without `event_backend`
- **THEN** boot SHALL raise an error with message indicating that an `event_backend` is required for async listeners

#### Scenario: Async listener with backend
- **WHEN** a module declares an async listener and `ApplicationContext` is created with `event_backend=InMemoryEventBackend()`
- **THEN** boot SHALL succeed without error

### Requirement: Register listeners in EventBus at boot
During boot, `ApplicationContext` SHALL iterate all module listeners and call `EventBus.register_handler()` for each one.

#### Scenario: Listeners registered during boot
- **WHEN** a module declares two listeners and `ApplicationContext` boots
- **THEN** `EventBus` SHALL have both handlers registered for their respective event types
