## ADDED Requirements

### Requirement: EventListener dataclass
The system SHALL provide a frozen `EventListener[E]` dataclass with fields: `event: type[E]` (the event class), `handler: type[EventHandler[E]]` (the handler class), and `scope: ListenerScope` (defaulting to `ListenerScope.SYNC`).

#### Scenario: Create a sync listener
- **WHEN** `EventListener(event=AgentPublished, handler=OnAgentPublished)` is created
- **THEN** `listener.event` SHALL be `AgentPublished`, `listener.handler` SHALL be `OnAgentPublished`, and `listener.scope` SHALL be `ListenerScope.SYNC`

#### Scenario: Create an async listener
- **WHEN** `EventListener(event=AgentPublished, handler=OnAgentPublished, scope=ListenerScope.ASYNC)` is created
- **THEN** `listener.scope` SHALL be `ListenerScope.ASYNC`

### Requirement: ListenerScope enum
The system SHALL provide a `ListenerScope` enum with values `SYNC` and `ASYNC`.

#### Scenario: ListenerScope values
- **WHEN** `ListenerScope` is inspected
- **THEN** it SHALL have exactly two members: `SYNC` and `ASYNC`

### Requirement: Type checker validates event/handler pairing
The `EventListener` generic SHALL connect `event: type[E]` and `handler: type[EventHandler[E]]` such that the type checker can validate that the handler matches the event type.

#### Scenario: Matching event and handler passes type check
- **WHEN** `EventListener(event=AgentPublished, handler=OnAgentPublished)` where `OnAgentPublished` extends `EventHandler[AgentPublished]`
- **THEN** the type checker SHALL accept this as valid

#### Scenario: Mismatched event and handler fails type check
- **WHEN** `EventListener(event=AgentPublished, handler=OnWorkflowCompleted)` where `OnWorkflowCompleted` extends `EventHandler[WorkflowCompleted]`
- **THEN** the type checker SHALL report a type error
