## ADDED Requirements

### Requirement: Auto-wire via init type hints
The system SHALL resolve dependencies automatically by inspecting `__init__` type hints (excluding `self` and `return`).

#### Scenario: Resolve class with typed dependencies
- **WHEN** `ListHandler.__init__(self, repo: ConversationRepo, reader: TeamReader)` and both types are registered
- **THEN** `container.resolve(ListHandler)` SHALL construct `ListHandler` with resolved `ConversationRepo` and `TeamReader`

#### Scenario: Resolve class with no dependencies
- **WHEN** a class has `__init__(self)` with no parameters
- **THEN** `container.resolve(SimpleClass)` SHALL construct it with no arguments

### Requirement: Recursive resolution
The system SHALL recursively resolve nested dependencies.

#### Scenario: Nested dependency chain
- **WHEN** `ServiceA` depends on `ServiceB` which depends on `ServiceC`
- **THEN** resolving `ServiceA` SHALL resolve `ServiceB` and `ServiceC` first

### Requirement: Default value fallback
The system SHALL use default values for parameters whose types are not registered.

#### Scenario: Parameter with default value and unregistered type
- **WHEN** `__init__(self, repo: Repo, limit: int = 100)` and `int` is not registered
- **THEN** resolving SHALL use `100` for `limit`

### Requirement: Circular dependency detection
The system SHALL detect circular dependencies and raise `CircularDependencyError` with the full chain.

#### Scenario: Direct circular dependency
- **WHEN** `ServiceA` depends on `ServiceB` and `ServiceB` depends on `ServiceA`
- **THEN** resolving either SHALL raise `CircularDependencyError` showing `ServiceA -> ServiceB -> ServiceA`

#### Scenario: Indirect circular dependency
- **WHEN** `A` depends on `B`, `B` depends on `C`, `C` depends on `A`
- **THEN** resolving SHALL raise `CircularDependencyError` showing `A -> B -> C -> A`

### Requirement: Unresolvable type error
The system SHALL raise `UnresolvableTypeError` when a required parameter type is not registered and has no default.

#### Scenario: Missing dependency without default
- **WHEN** `Handler.__init__(self, reader: TeamReader)` and `TeamReader` is not registered
- **THEN** resolving SHALL raise `UnresolvableTypeError` with message indicating which parameter and type are missing, plus a hint to register it

### Requirement: Missing type hint error
The system SHALL raise `TypeHintRequiredError` when an `__init__` parameter has no type hint.

#### Scenario: Parameter without type annotation
- **WHEN** `Service.__init__(self, db)` where `db` has no type hint
- **THEN** resolving SHALL raise `TypeHintRequiredError` with a hint to add type hints or use a factory

### Requirement: Interface to implementation resolution
The system SHALL follow interface-to-implementation mappings before auto-wiring.

#### Scenario: Resolve via interface mapping
- **WHEN** `container.register(TeamReader, PgTeamReader)` and `Handler` depends on `TeamReader`
- **THEN** resolving `Handler` SHALL auto-wire `PgTeamReader` for the `TeamReader` parameter
