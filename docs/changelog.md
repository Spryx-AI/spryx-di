# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-04-04

### Added

- `Container` with `register`, `singleton`, `instance`, `factory`, `resolve`, `override`, `has`
- Auto-wiring via `__init__` type hints with recursive resolution
- Circular dependency detection with `CircularDependencyError`
- `ScopedContainer` with parent inheritance and local overrides
- `Module` dataclass with `providers`, `exports`, `imports`, `on_destroy`
- `Provider` with `use_class`, `use_factory`, `use_value`, `Scope.SINGLETON`/`TRANSIENT`
- `ApplicationContext` with module composition and boundary enforcement
- `forward_ref()` for circular module dependencies
- Boot-time validation: `ExportWithoutProviderError`, `ModuleNotFoundError`, `CircularModuleError`
- `ModuleBoundaryError` for boundary violations via `resolve_within()`
- Lifecycle hooks: `on_destroy`, `on_shutdown`, managed instance auto-close
- FastAPI integration: `Inject()`, `ScopedInject()`, `configure()`, `RequestScopeMiddleware`
- pydantic-settings integration: `register_settings()`
- Testing utilities: `override()` context manager
- `py.typed` marker for type checkers
