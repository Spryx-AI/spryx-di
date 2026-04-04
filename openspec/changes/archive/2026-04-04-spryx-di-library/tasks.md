## 1. Project Setup

- [x] 1.1 Initialize project with uv: pyproject.toml, src/spryx_di/ layout, py.typed marker
- [x] 1.2 Configure ruff (lint/format) and ty (type checking) in pyproject.toml
- [x] 1.3 Configure pytest and create tests/ directory structure (unit/, integration/, conftest.py)
- [x] 1.4 Create src/spryx_di/__init__.py with public API exports
- [x] 1.5 Create src/spryx_di/errors.py with custom exceptions (UnresolvableTypeError, CircularDependencyError, TypeHintRequiredError)

## 2. Container Core

- [x] 2.1 Implement Container class with internal registries (_instances, _factories, _singletons, _transients, _singleton_cache)
- [x] 2.2 Implement register() for transient registration
- [x] 2.3 Implement singleton() for singleton registration
- [x] 2.4 Implement instance() for pre-built instance registration
- [x] 2.5 Implement factory() for factory function registration
- [x] 2.6 Implement has() check method
- [x] 2.7 Implement override() method
- [x] 2.8 Implement __getitem__ as alias for resolve
- [x] 2.9 Add duplicate registration warning logging
- [x] 2.10 Write unit tests for all container-core specs

## 3. Auto-Wiring & Resolution

- [x] 3.1 Implement resolve() with __init__ type hint inspection
- [x] 3.2 Implement recursive resolution of nested dependencies
- [x] 3.3 Implement default value fallback for unregistered types
- [x] 3.4 Implement circular dependency detection with stack and CircularDependencyError
- [x] 3.5 Implement UnresolvableTypeError with actionable message and hint
- [x] 3.6 Implement TypeHintRequiredError for missing type annotations
- [x] 3.7 Implement interface-to-implementation mapping before auto-wiring
- [x] 3.8 Write unit tests for all auto-wiring specs

## 4. Scoped Container

- [x] 4.1 Implement ScopedContainer that holds reference to parent Container
- [x] 4.2 Implement scope-local registrations that override parent
- [x] 4.3 Implement resolution fallback from scope to parent
- [x] 4.4 Implement create_scope() on Container
- [x] 4.5 Write unit tests for all scoped-container specs

## 5. Module System

- [x] 5.1 Implement ModuleDefinition dataclass (name, register callable)
- [x] 5.2 Implement compose_modules(modules, globals) function
- [x] 5.3 Ensure globals are registered as instances before module register functions
- [x] 5.4 Write unit tests for all module-system specs

## 6. FastAPI Integration

- [x] 6.1 Create src/spryx_di/ext/__init__.py and src/spryx_di/ext/fastapi.py
- [x] 6.2 Implement configure(app, container) function
- [x] 6.3 Implement Inject(type) returning FastAPI Depends
- [x] 6.4 Implement ScopedInject(type) returning FastAPI Depends with request scope
- [x] 6.5 Implement request scope middleware that creates ScopedContainer per request
- [x] 6.6 Write integration tests with FastAPI TestClient for all fastapi-integration specs

## 7. Testing Utilities

- [x] 7.1 Create src/spryx_di/testing/__init__.py and override.py
- [x] 7.2 Implement override() context manager with backup/restore
- [x] 7.3 Support both type and instance values in override dict
- [x] 7.4 Write unit tests for all testing-utilities specs

## 8. Pydantic-Settings Integration

- [x] 8.1 Create src/spryx_di/ext/settings.py
- [x] 8.2 Implement register_settings(container, settings_class) helper
- [x] 8.3 Write unit tests for all settings-integration specs

## 9. Type Safety & Quality

- [x] 9.1 Run ty in strict mode and fix all type errors
- [x] 9.2 Run ruff check and ruff format, fix all issues
- [x] 9.3 Verify all public API exports have proper type annotations
- [x] 9.4 Run full test suite and verify all tests pass
