## MODIFIED Requirements

### Requirement: ModuleDefinition dataclass
The system SHALL provide a `Module` dataclass with `name: str`, `providers: list[Provider | type]`, `exports: list[type]`, `imports: list[Module | ForwardRef]`, `on_destroy: Any | None`, and `listeners: list[EventListener]` (defaulting to empty list).

#### Scenario: Define a module
- **WHEN** `module = Module(name="identity", providers=[...])` is created without specifying `listeners`
- **THEN** `module.listeners` SHALL default to an empty list

#### Scenario: Define a module with listeners
- **WHEN** `module = Module(name="notification", providers=[...], listeners=[EventListener(event=AgentPublished, handler=OnAgentPublished)])` is created
- **THEN** `module.listeners` SHALL contain the declared listener

## ADDED Requirements

### Requirement: ApplicationContext event_backend parameter
`ApplicationContext.__init__` SHALL accept an optional `event_backend: AsyncEventBackend | None` parameter (defaulting to `None`) for dispatching async events.

#### Scenario: Create context without backend
- **WHEN** `ApplicationContext(modules=[...])` is created without `event_backend`
- **THEN** it SHALL boot successfully if no module has async listeners

#### Scenario: Create context with backend
- **WHEN** `ApplicationContext(modules=[...], event_backend=InMemoryEventBackend())` is created
- **THEN** the backend SHALL be available for async listener dispatch
