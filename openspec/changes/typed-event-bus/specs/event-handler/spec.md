## ADDED Requirements

### Requirement: EventHandler generic base class
The system SHALL provide `EventHandler[E]`, a generic abstract base class where `E` is the event type. It SHALL define `async def handle(self, event: E) -> None` as an abstract method that raises `NotImplementedError` by default.

#### Scenario: Subclass with concrete event type
- **WHEN** a class `OnAgentPublished(EventHandler[AgentPublished])` is defined with `async def handle(self, event: AgentPublished) -> None`
- **THEN** the class SHALL be a valid `EventHandler` subclass and the type checker SHALL enforce that `event` is `AgentPublished`

#### Scenario: Calling handle on base class raises NotImplementedError
- **WHEN** `EventHandler().handle(event)` is awaited directly on the base class
- **THEN** it SHALL raise `NotImplementedError`

### Requirement: EventHandler event type introspection
The system SHALL be able to extract the concrete event type `E` from an `EventHandler[E]` subclass at runtime via `__orig_bases__`.

#### Scenario: Extract event type from handler subclass
- **WHEN** `OnAgentPublished` extends `EventHandler[AgentPublished]`
- **THEN** runtime introspection SHALL yield `AgentPublished` as the event type
