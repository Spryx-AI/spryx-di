## ADDED Requirements

### Requirement: Container instantiation
The system SHALL provide a `Container` class that can be instantiated without arguments.

#### Scenario: Create empty container
- **WHEN** a user creates `Container()`
- **THEN** the container is created with no registrations

### Requirement: Transient registration
The system SHALL provide `container.register(interface, implementation)` that registers a transient mapping (new instance per resolve).

#### Scenario: Register interface to implementation
- **WHEN** `container.register(TeamReader, PgTeamReader)` is called
- **THEN** resolving `TeamReader` SHALL return a new `PgTeamReader` instance each time

#### Scenario: Register concrete class to itself
- **WHEN** `container.register(PgTeamReader, PgTeamReader)` is called
- **THEN** resolving `PgTeamReader` SHALL return a new instance each time

### Requirement: Singleton registration
The system SHALL provide `container.singleton(interface, implementation)` that registers a singleton mapping (one instance per container lifetime).

#### Scenario: Singleton returns same instance
- **WHEN** `container.singleton(TeamReader, PgTeamReader)` is called
- **THEN** resolving `TeamReader` multiple times SHALL return the exact same instance (identity check)

### Requirement: Instance registration
The system SHALL provide `container.instance(type, obj)` that registers a pre-built instance.

#### Scenario: Instance returns the exact object
- **WHEN** `container.instance(Database, my_db)` is called
- **THEN** resolving `Database` SHALL return `my_db` (same object reference)

### Requirement: Factory registration
The system SHALL provide `container.factory(type, callable)` that registers a factory function receiving the container.

#### Scenario: Factory is called with container
- **WHEN** `container.factory(TeamReader, lambda c: PgTeamReader(c.resolve(Database)))` is called
- **THEN** resolving `TeamReader` SHALL call the factory with the container and return its result

### Requirement: Dict-style access
The system SHALL support `container[Type]` as an alias for `container.resolve(Type)`.

#### Scenario: Bracket access resolves type
- **WHEN** `handler = container[ListConversationsHandler]` is called
- **THEN** it SHALL behave identically to `container.resolve(ListConversationsHandler)`

### Requirement: Has check
The system SHALL provide `container.has(type)` returning `bool` indicating whether a type is registered.

#### Scenario: Check registered type
- **WHEN** `TeamReader` is registered and `container.has(TeamReader)` is called
- **THEN** it SHALL return `True`

#### Scenario: Check unregistered type
- **WHEN** `UnknownType` is not registered and `container.has(UnknownType)` is called
- **THEN** it SHALL return `False`

### Requirement: Override registration
The system SHALL provide `container.override(type, new_implementation)` that replaces an existing registration.

#### Scenario: Override replaces previous registration
- **WHEN** `container.singleton(TeamReader, PgTeamReader)` then `container.override(TeamReader, FakeTeamReader)` is called
- **THEN** resolving `TeamReader` SHALL return a `FakeTeamReader` instance

### Requirement: Duplicate registration warning
The system SHALL log a WARNING when a type is registered twice via `register`/`singleton`/`instance`/`factory` (not via `override`).

#### Scenario: Duplicate registration logs warning
- **WHEN** `container.singleton(TeamReader, PgTeamReader)` is called twice with different implementations
- **THEN** a WARNING SHALL be logged indicating the overwrite, and the last registration wins
