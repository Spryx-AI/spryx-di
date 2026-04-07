# CHANGELOG


## v3.0.3 (2026-04-07)

### Bug Fixes

- **module**: Resolve exported ExistingProvider from global container
  ([#14](https://github.com/Spryx-AI/spryx-di/pull/14),
  [`1b82a35`](https://github.com/Spryx-AI/spryx-di/commit/1b82a35be3e434c8e4a4dd8a6c0cf936a2ad9150))

* fix(module): resolve exported ExistingProvider from global container

The module container only sees globals + own providers and cannot resolve types from other modules.
  Use the global container (which has all providers from step 7) and pin the result as an instance.

Also removes the singleton cache seeding which was unnecessary and could overwrite entries when two
  modules shared the same use_existing target.

* test(module): add multi-module ExistingProvider export test

Covers the case where two modules each export via ExistingProvider with distinct internal types,
  validating both resolve correctly under global-container resolution.


## v3.0.2 (2026-04-07)

### Bug Fixes

- **module**: Resolve exported ExistingProvider from owning module container
  ([#13](https://github.com/Spryx-AI/spryx-di/pull/13),
  [`3729a49`](https://github.com/Spryx-AI/spryx-di/commit/3729a494919e9d139e7c2676f203b4bbb158e095))

* fix(module): resolve exported ExistingProvider from owning module container

ExistingProvider(export=True) was resolving the target type from the global container, causing
  incorrect behavior when modules share internal types with different values. The resolution lambda
  now delegates to the owning module's container so internal dependencies stay correctly scoped.

* fix(module): guard singleton cache seeding against overwrites

When two modules share the same use_existing target, the second iteration would overwrite the first
  module's entry in the global singleton cache. Add a guard to only seed when no entry exists yet.


## v3.0.1 (2026-04-07)

### Bug Fixes

- **analysis**: Handle Protocols with non-method members in orphan check
  ([#12](https://github.com/Spryx-AI/spryx-di/pull/12),
  [`09615b3`](https://github.com/Spryx-AI/spryx-di/commit/09615b3f2d5f0020330879488e8c38e5a8d6fffe))


## v3.0.0 (2026-04-07)

### Features

- **module**: Downgrade module cycles to warnings, detect provider cycles at boot
  ([#10](https://github.com/Spryx-AI/spryx-di/pull/10),
  [`4ea651e`](https://github.com/Spryx-AI/spryx-di/commit/4ea651e7ad0e26de39ad3d947c6d9509fb23f1bd))

* feat(module): detect provider circular dependencies at boot and downgrade module cycles to
  warnings

Module-level circular dependencies (via dependencies field) are no longer blocking errors — they are
  logged as warnings since the ApplicationContext registers all providers globally before building
  module containers, so no initialization deadlock occurs.

Provider-level circular dependencies (A.__init__ needs B, B.__init__ needs A) are now detected
  eagerly at boot via static analysis of __init__ type hints, raising CircularDependencyError before
  any resolve() call.

BREAKING CHANGE: CircularDependencyInModulesError is no longer raised during boot. Module dependency
  cycles emit a warning instead. The class remains as an alias for backward compatibility.

* fix(analysis): skip ExistingProvider in orphan provider check

* fix(analysis): consider inheritance in orphan provider detection

* fix(analysis): allow ExistingProvider orphan detection and skip its targets

* fix(analysis): inspect FactoryProvider.provide __init__ for dependency tracking

* feat(provider): add deps/args to FactoryProvider for declarative factories

* test(provider): add comprehensive tests for FactoryProvider deps/args

* style(provider): trim verbose FactoryProvider docstring

### Breaking Changes

- **module**: Circulardependencyinmoduleserror is no longer raised during boot. Module dependency
  cycles emit a warning instead. The class remains as an alias for backward compatibility.


## v2.0.0 (2026-04-06)

### Features

- **module**: Replace imports/exports with dependencies and provider visibility flags
  ([#9](https://github.com/Spryx-AI/spryx-di/pull/9),
  [`93c7bf4`](https://github.com/Spryx-AI/spryx-di/commit/93c7bf402b19ae2ee5f77abb6caa1f1ed81cd993))

* feat(module): replace imports/exports with dependencies and provider visibility flags

BREAKING CHANGE: Module.imports renamed to Module.dependencies, Module.exports removed in favor of
  export/public flags on providers, ExportWithoutProviderError removed, error classes renamed
  (UnresolvedImportError -> UnresolvedDependencyError, CircularImportError ->
  CircularDependencyInModulesError). Old names kept as aliases. Inject() now enforces public=True.
  Boot emits warnings for unused providers, dependencies, and exports.

* chore: sync uv.lock version

* fix(fastapi): accept both Container and ApplicationContext in configure()

* fix(module): include public globals in public_types registry

* feat(cli): add spryx-di CLI with check, info, and graph commands

Extract warning logic into analysis.py, add analyze() method to ApplicationContext, and implement
  CLI via typer (optional dependency).

* fix(cli): handle missing typer gracefully and validate callable before invoke

* fix(cli): catch SpryxDIError during boot and display as formatted error

### Breaking Changes

- **module**: Module.imports renamed to Module.dependencies, Module.exports removed in favor of
  export/public flags on providers, ExportWithoutProviderError removed, error classes renamed
  (UnresolvedImportError -> UnresolvedDependencyError, CircularImportError ->
  CircularDependencyInModulesError). Old names kept as aliases. Inject() now enforces public=True.
  Boot emits warnings for unused providers, dependencies, and exports.


## v1.3.1 (2026-04-06)

### Refactoring

- **module**: Replace module-reference imports with port-based imports
  ([#8](https://github.com/Spryx-AI/spryx-di/pull/8),
  [`2d27c3a`](https://github.com/Spryx-AI/spryx-di/commit/2d27c3a0429abefa73236252d61de9fe1b5a59fa))

Modules no longer reference each other directly. Imports are now types (Protocols/ABCs) that the
  framework matches automatically against exports from other modules at boot time. Removes
  ForwardRef, forward_ref, module re-exports, and old cycle detection in favor of export registry,
  import validation, and implicit dependency graph cycle detection.


## v1.3.0 (2026-04-06)

### Features

- **provider**: Make ClassProvider.use_class optional and enforce explicit providers
  ([#7](https://github.com/Spryx-AI/spryx-di/pull/7),
  [`ff39da3`](https://github.com/Spryx-AI/spryx-di/commit/ff39da310a3640e7f74c7f49bfabe412a7daef9a))

ClassProvider.use_class now defaults to the value of provide, enabling ClassProvider(provide=Foo) as
  shorthand for ClassProvider(provide=Foo, use_class=Foo).

Module.providers no longer accepts bare types — all entries must be an explicit Provider instance
  for clarity and consistency.


## v1.2.0 (2026-04-06)

### Features

- **events**: Typed event bus with pluggable backends and serialization
  ([#6](https://github.com/Spryx-AI/spryx-di/pull/6),
  [`4f9249d`](https://github.com/Spryx-AI/spryx-di/commit/4f9249da7b19fef0ea45c1176445dd9de4ae362f))

* feat(events): add typed event bus with pluggable backends

Introduce a generic EventHandler[E] base class, EventBus mediator with sync/async dispatch,
  EventListener for declarative registration in modules, and AsyncEventBackend protocol. Ships
  InMemoryEventBackend for testing and CeleryEventBackend for production. ApplicationContext
  validates listeners at boot and auto-registers EventBus as singleton.

* refactor(events): pluggable serialization, strict typing, celery worker registration

- Add serialize_event() supporting dataclass, Pydantic, dict, and to_dict() -
  AsyncEventBackend.dispatch() now receives dict payload instead of raw object - Replace all Any
  with proper types (TypeVar, object, Callable, raw generics) - CeleryEventBackend: TYPE_CHECKING
  import, optional dep, register_worker() - ApplicationContext: event/handler registries, typed
  resolve/shutdown/hooks - EventBus: fail loud on ASYNC dispatch without backend - Add event_bus
  example with sync billing + async notifications

* chore: add openspec change artifacts for typed-event-bus

* fix: async dispatch, qualified registry keys, and deprecated asyncio usage

- Wrap CeleryEventBackend.send_task in asyncio.to_thread() to avoid blocking the event loop during
  broker I/O - Use fully qualified names (module.qualname) as registry keys for events and handlers
  to prevent silent collisions across packages - Replace deprecated
  asyncio.get_event_loop().run_until_complete() with asyncio.run() in test_events.py (Python ≥3.11)

---------

Co-authored-by: cubic-dev-ai[bot] <1082092+cubic-dev-ai[bot]@users.noreply.github.com>


## v1.1.1 (2026-04-04)

### Bug Fixes

- **container**: Handle TYPE_CHECKING imports, Optional types, and Protocol/ABC in auto-wiring
  ([#5](https://github.com/Spryx-AI/spryx-di/pull/5),
  [`0853999`](https://github.com/Spryx-AI/spryx-di/commit/085399930ca5f6f45b5e5e7dca2bb110419c6129))

- Enrich namespace with registered types when get_type_hints fails - Unwrap X | None to extract the
  real type before resolving - Skip Protocols and ABCs in auto-wiring instead of trying to
  instantiate


## v1.1.0 (2026-04-04)

### Features

- **module**: Support re-exports in module exports
  ([#4](https://github.com/Spryx-AI/spryx-di/pull/4),
  [`8fa8067`](https://github.com/Spryx-AI/spryx-di/commit/8fa8067ab83d95b5721a7aec41be3fd2ba74c158))

* feat(module): support re-exports in module exports

Allow modules to re-export types or entire modules from their imports, enabling sub-module
  composition where a parent module aggregates children and selectively exposes their exports to the
  outside world.

* fix(module): guard against circular re-exports and fix type annotation

Add visited set to _compute_effective_exports to prevent infinite recursion on circular re-exports.
  Use TYPE_CHECKING guard for precise Module type annotation in ExportWithoutProviderError.


## v1.0.0 (2026-04-04)

### Bug Fixes

- **provider**: Cache singleton factory results on resolve
  ([`edfb213`](https://github.com/Spryx-AI/spryx-di/commit/edfb2138b73747b565a58cff435107acef5d87f3))

FactoryProvider.scope was silently ignored — factories always created new instances regardless of
  scope setting. Fix by checking the singleton cache before the factory dict in
  Container._resolve_untyped.

Also fix missing ValueProvider imports in docs snippets.

- **provider**: Memoize singleton factory instead of hijacking _singletons
  ([`ccb89f9`](https://github.com/Spryx-AI/spryx-di/commit/ccb89f983504ffda426fe6cb090f52e30e899ee0))

Replace direct write to container._singletons with a memoizing wrapper around the factory callable.
  Each container gets its own cache, preserving correct per-container singleton semantics.

### Features

- **provider**: Replace Provider class with typed variants
  ([`3a74adc`](https://github.com/Spryx-AI/spryx-di/commit/3a74adcd83160c213e3fc97ad0900e9205c86cc1))

Replace Provider with a union of typed dataclasses: ClassProvider, FactoryProvider, ValueProvider,
  ExistingProvider.

Each variant has only its relevant fields. The type checker enforces correct usage at construction
  time.

Adds ExistingProvider for aliasing types without boilerplate: ExistingProvider(provide=AssetService,
  use_existing=Impl)

BREAKING CHANGE: Provider is now a union type, not a class

### Breaking Changes

- **provider**: Provider is now a union type, not a class


## v0.1.0 (2026-04-04)

### Chores

- Add openspec change artifacts for docs
  ([`debec7d`](https://github.com/Spryx-AI/spryx-di/commit/debec7d22bd41ded788e7c497c7dd1d6342ca320))

- Add openspec config and claude skills
  ([`7b54c03`](https://github.com/Spryx-AI/spryx-di/commit/7b54c0358335a47958171de13a1190d4b2c259eb))

### Code Style

- Remove redundant comments and docstrings
  ([`0358531`](https://github.com/Spryx-AI/spryx-di/commit/03585310fb1f2169da3727267657c923819e9e53))

### Continuous Integration

- Configure python-semantic-release with PyPI publishing
  ([`11371c9`](https://github.com/Spryx-AI/spryx-di/commit/11371c9dfd24ca80c7521f2218953cd22ef8e6d7))

Use official python-semantic-release and pypa/gh-action-pypi-publish actions with trusted publisher
  (OIDC). Add build dependency.

- **release**: Fix build step running outside semantic-release container
  ([`002cdac`](https://github.com/Spryx-AI/spryx-di/commit/002cdacdc84c8d238aa5041cac89f2fcbbf48adc))

### Documentation

- Add documentation site with Zensical
  ([`a03834a`](https://github.com/Spryx-AI/spryx-di/commit/a03834a6c42521dca9332a5b4ec5d7ee023d9969))

23 pages covering getting started, core concepts, integrations, guides, API reference, changelog,
  and contributing. Deployed to GitHub Pages via Actions artifacts.

- Add README with badges, example, and feature table
  ([`195b091`](https://github.com/Spryx-AI/spryx-di/commit/195b091f55bffd9c63de99d340c1f0aca7b82b35))

### Features

- Implement spryx-di library with modular DI container
  ([`9efda28`](https://github.com/Spryx-AI/spryx-di/commit/9efda280730fe85cfe9e3aadce6e096da4f6d22c))

Type-based dependency injection container for Python modular monoliths, inspired by NestJS module
  system. Includes auto-wiring via __init__ type hints, declarative Module/Provider/Scope API,
  boundary enforcement with exports/imports, forward_ref for circular dependencies, lifecycle hooks
  (on_destroy, shutdown), scoped containers, FastAPI and pydantic-settings integrations, testing
  utilities, and two complete examples.

### Refactoring

- **container**: Eliminate type: ignore with resolve/untyped split
  ([`06d7124`](https://github.com/Spryx-AI/spryx-di/commit/06d7124498a4286173a1dd3005773ba0090a111f))

Split resolve into public resolve(type_) -> T with a single cast and private _resolve_untyped(type_,
  resolving) -> object. Extract _find_implementation and _resolve_from_parent. ScopedContainer now
  delegates instead of duplicating resolution logic.
