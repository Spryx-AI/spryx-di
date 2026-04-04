## ADDED Requirements

### Requirement: Create scoped container
The system SHALL provide `container.create_scope()` that returns a `ScopedContainer` inheriting all parent registrations.

#### Scenario: Scope inherits parent registrations
- **WHEN** parent has `Database` registered and `scope = container.create_scope()`
- **THEN** `scope.resolve(Database)` SHALL return the parent's `Database` instance

### Requirement: Scoped local overrides
The system SHALL allow registrations on the scoped container that override parent registrations locally.

#### Scenario: Scope-local registration overrides parent
- **WHEN** parent has `TeamReader` registered, and `scope.instance(TeamReader, fake_reader)`
- **THEN** `scope.resolve(TeamReader)` SHALL return `fake_reader`
- **AND** `container.resolve(TeamReader)` SHALL still return the parent's registration

### Requirement: Scoped singletons are scope-local
Singletons registered on a scoped container SHALL be cached within that scope only.

#### Scenario: Singleton in scope does not affect parent
- **WHEN** `scope.singleton(Cache, RedisCache)` and resolved from scope
- **THEN** parent container SHALL NOT have `Cache` registered

### Requirement: Mixed resolution from scope and parent
The system SHALL resolve dependencies using scope-local registrations first, falling back to parent.

#### Scenario: Handler with mixed dependencies
- **WHEN** scope has `Transaction` registered locally and parent has `Database` registered
- **THEN** resolving a `Handler(db: Database, tx: Transaction)` from scope SHALL use parent's `Database` and scope's `Transaction`
