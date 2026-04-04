## ADDED Requirements

### Requirement: Landing page
The docs SHALL have an `index.md` with lib description, feature bullets, quick code example, install command, and badges.

#### Scenario: Landing page loads
- **WHEN** a user visits the docs root
- **THEN** they SHALL see what spryx-di is, a runnable code example, and install instructions within 10 seconds of reading

### Requirement: Getting Started section
The docs SHALL have `installation.md` and `quickstart.md` pages.

#### Scenario: Quickstart is runnable
- **WHEN** a user copies the quickstart example
- **THEN** it SHALL run without modification after `pip install spryx-di`

### Requirement: Core Concepts section
The docs SHALL have pages for container, providers, modules, boundaries, scopes, auto-wiring, and lifecycle.

#### Scenario: One concept per page
- **WHEN** a user reads `concepts/modules.md`
- **THEN** it SHALL explain only the Module system, with code examples and optionally a NestJS comparison

### Requirement: Integrations section
The docs SHALL have a FastAPI integration page with step-by-step setup.

#### Scenario: FastAPI guide is complete
- **WHEN** a user reads `integrations/fastapi.md`
- **THEN** it SHALL cover configure(), Inject(), ScopedInject(), and request scope middleware with runnable examples

### Requirement: Guides section
The docs SHALL have guides for modular monolith, testing, migration, and circular dependencies.

#### Scenario: Guides are scenario-driven
- **WHEN** a user reads `guides/testing.md`
- **THEN** it SHALL show how to test with fakes, override(), and TestClient with runnable examples

### Requirement: API Reference section
The docs SHALL have reference pages for Container, Module, Provider, Errors, FastAPI integration, and Testing utilities.

#### Scenario: API reference is complete
- **WHEN** a user reads `api/container.md`
- **THEN** it SHALL list every public method with signature, parameters, return type, exceptions, and example

### Requirement: Portuguese translation
All concept and guide pages SHALL have Portuguese translations in `docs/pt/` with identical structure.

#### Scenario: Code blocks unchanged in translation
- **WHEN** `docs/pt/concepts/modules.md` is compared to `docs/en/concepts/modules.md`
- **THEN** all Python code blocks SHALL be identical; only surrounding text is translated
