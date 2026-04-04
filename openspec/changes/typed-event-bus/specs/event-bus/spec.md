## ADDED Requirements

### Requirement: EventBus singleton registration
The system SHALL provide an `EventBus` class that is registered as a singleton in the root container when any module declares listeners.

#### Scenario: EventBus available when listeners exist
- **WHEN** at least one module has a non-empty `listeners` list
- **THEN** `container.resolve(EventBus)` SHALL return the same `EventBus` instance every time

#### Scenario: No EventBus when no listeners
- **WHEN** no module declares any listeners
- **THEN** `EventBus` SHALL NOT be registered in the container

### Requirement: EventBus publish dispatches to sync handlers
The system SHALL dispatch published events to all registered sync handlers by resolving them from the container and awaiting `handler.handle(event)`.

#### Scenario: Publish event to sync handler
- **WHEN** `EventBus.publish(event)` is called and there is a sync handler registered for `type(event)`
- **THEN** the handler SHALL be resolved from the container and `handler.handle(event)` SHALL be awaited

#### Scenario: Publish event with no handlers
- **WHEN** `EventBus.publish(event)` is called and no handlers are registered for `type(event)`
- **THEN** the call SHALL complete without error

### Requirement: EventBus publish dispatches to async handlers
The system SHALL dispatch published events to async handlers by calling `AsyncEventBackend.dispatch()` with the event and metadata.

#### Scenario: Publish event to async handler
- **WHEN** `EventBus.publish(event)` is called and there is an async handler registered for `type(event)`
- **THEN** `AsyncEventBackend.dispatch(event, metadata)` SHALL be called with correct `EventMetadata`

### Requirement: EventBus supports multiple handlers per event
The system SHALL support multiple handlers (sync and/or async) for the same event type.

#### Scenario: Multiple handlers for same event
- **WHEN** two handlers are registered for `AgentPublished` (one sync, one async) and the event is published
- **THEN** both handlers SHALL be invoked — the sync handler awaited inline, the async handler dispatched to the backend
