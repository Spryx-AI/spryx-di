## ADDED Requirements

### Requirement: AsyncEventBackend protocol
The system SHALL provide an `AsyncEventBackend` Protocol with method `async def dispatch(self, event: object, metadata: EventMetadata) -> None`.

#### Scenario: Implement custom backend
- **WHEN** a class implements `async def dispatch(self, event: object, metadata: EventMetadata) -> None`
- **THEN** it SHALL satisfy the `AsyncEventBackend` protocol without explicit inheritance

### Requirement: EventMetadata dataclass
The system SHALL provide a frozen `EventMetadata` dataclass with fields: `event_type: str`, `handler_type: str`.

#### Scenario: Create metadata
- **WHEN** `EventMetadata(event_type="AgentPublished", handler_type="OnAgentPublished")` is created
- **THEN** all fields SHALL be accessible and the instance SHALL be immutable

### Requirement: InMemoryEventBackend
The system SHALL provide `InMemoryEventBackend` that captures dispatched events in a `dispatched: list[tuple[object, EventMetadata]]` list for test assertions.

#### Scenario: Capture dispatched event
- **WHEN** `backend.dispatch(event, metadata)` is awaited
- **THEN** `(event, metadata)` SHALL be appended to `backend.dispatched`

#### Scenario: assert_published helper
- **WHEN** `backend.assert_published(AgentPublished, agent_id="ag_01")` is called and a matching event exists
- **THEN** the assertion SHALL pass

#### Scenario: assert_published with no match
- **WHEN** `backend.assert_published(AgentPublished, agent_id="ag_99")` is called and no matching event exists
- **THEN** it SHALL raise `AssertionError`

#### Scenario: clear resets state
- **WHEN** `backend.clear()` is called
- **THEN** `backend.dispatched` SHALL be empty

### Requirement: CeleryEventBackend
The system SHALL provide `CeleryEventBackend` that dispatches events via Celery `send_task` with serialized payload and queue routing based on metadata.

#### Scenario: Dispatch via Celery
- **WHEN** `backend.dispatch(event, metadata)` is awaited
- **THEN** `celery_app.send_task` SHALL be called with the configured task name, serialized event payload, and handler metadata
