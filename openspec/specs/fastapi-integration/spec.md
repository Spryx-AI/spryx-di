## ADDED Requirements

### Requirement: configure function
The system SHALL provide `configure(app, container)` that attaches the container to `app.state.container`.

#### Scenario: Configure attaches container to app
- **WHEN** `configure(app, container)` is called
- **THEN** `app.state.container` SHALL be the provided container

### Requirement: Inject dependency helper
The system SHALL provide `Inject(type)` that returns a FastAPI `Depends()` resolving from the app's container.

#### Scenario: Inject resolves from global container
- **WHEN** a route parameter uses `handler: Handler = Inject(Handler)` and container has `Handler` registered
- **THEN** the route SHALL receive a resolved `Handler` instance

### Requirement: ScopedInject dependency helper
The system SHALL provide `ScopedInject(type)` that returns a FastAPI `Depends()` resolving from the request's scoped container.

#### Scenario: ScopedInject resolves from request scope
- **WHEN** a route parameter uses `handler: Handler = ScopedInject(Handler)` and request has a scoped container
- **THEN** the route SHALL receive a `Handler` resolved from the request-scoped container

### Requirement: Request scope middleware
The system SHALL provide middleware that creates a scoped container per request at `request.state.scope`.

#### Scenario: Each request gets its own scope
- **WHEN** two concurrent requests are processed
- **THEN** each SHALL have a separate `request.state.scope` scoped container

### Requirement: Inject and ScopedInject are importable from ext.fastapi
The integration SHALL be importable as `from spryx_di.ext.fastapi import Inject, ScopedInject, configure`.

#### Scenario: Import path works
- **WHEN** fastapi is installed and `from spryx_di.ext.fastapi import Inject` is executed
- **THEN** the import SHALL succeed without errors
