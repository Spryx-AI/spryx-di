# CHANGELOG


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
