## ADDED Requirements

### Requirement: ModuleDefinition dataclass
The system SHALL provide a `ModuleDefinition` with `name: str` and `register: Callable[[Container], None]`.

#### Scenario: Define a module
- **WHEN** `module = ModuleDefinition(name="identity", register=register_fn)`
- **THEN** `module.name` SHALL be `"identity"` and `module.register` SHALL be `register_fn`

### Requirement: compose_modules function
The system SHALL provide `compose_modules(modules, globals)` that creates a Container, registers globals as instances, and calls each module's register function in order.

#### Scenario: Compose multiple modules
- **WHEN** `compose_modules(modules=[mod_a, mod_b], globals={Database: db})` is called
- **THEN** a Container SHALL be returned with `Database` as instance and all registrations from `mod_a` and `mod_b`

#### Scenario: Module registration order
- **WHEN** `mod_a` registers `TeamReader` and `mod_b` registers same type with different impl
- **THEN** `mod_b`'s registration SHALL win (last module wins)

### Requirement: Globals registered before modules
The system SHALL register all globals as instances before calling any module's register function.

#### Scenario: Module can depend on globals
- **WHEN** `globals={Database: db}` and a module's register function calls `container.resolve(Database)`
- **THEN** it SHALL successfully resolve to `db`
