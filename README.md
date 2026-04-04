# spryx-di

[![CI](https://github.com/spryx-ai/spryx-di/actions/workflows/ci.yml/badge.svg)](https://github.com/spryx-ai/spryx-di/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/spryx-di)](https://pypi.org/project/spryx-di/)
[![Python](https://img.shields.io/pypi/pyversions/spryx-di)](https://pypi.org/project/spryx-di/)
[![License](https://img.shields.io/github/license/spryx-ai/spryx-di)](https://github.com/spryx-ai/spryx-di/blob/main/LICENSE)

Lightweight dependency injection for Python modular monoliths.

- **NestJS-inspired modules** with providers, exports, and imports
- **Type-based auto-wiring** via `__init__` type hints
- **Module boundary enforcement** at boot time
- **Zero runtime dependencies**
- **Zero intrusion** in domain code

## Install

```bash
pip install spryx-di
```

## Quick Example

```python
from spryx_di import Module, Provider, ApplicationContext

identity_module = Module(
    name="identity",
    providers=[
        Provider(provide=UserRepository, use_class=PgUserRepository),
        Provider(provide=UserReader, use_class=PgUserReader),
    ],
    exports=[UserReader],
)

orders_module = Module(
    name="orders",
    providers=[
        Provider(provide=OrderRepository, use_class=PgOrderRepository),
    ],
    imports=[identity_module],
)

ctx = ApplicationContext(modules=[identity_module, orders_module])
handler = ctx.resolve(CreateOrderHandler)  # auto-wired from type hints
```

Handlers declare dependencies via `__init__` — no decorators, no DI imports:

```python
class CreateOrderHandler:
    def __init__(self, repo: OrderRepository, reader: UserReader) -> None:
        self._repo = repo
        self._reader = reader
```

## Features

| Feature | Description |
|---|---|
| `Provider` | `use_class`, `use_factory`, `use_value` with `Scope.SINGLETON` (default) or `TRANSIENT` |
| `Module` | Declarative `providers`, `exports`, `imports`, `on_destroy` |
| `ApplicationContext` | Composes modules with boundary enforcement and boot-time validation |
| `forward_ref()` | Circular module dependencies without Python import errors |
| Lifecycle | `on_destroy` per module, auto-close managed instances, `await ctx.shutdown()` |
| FastAPI | `Inject()`, `ScopedInject()`, `configure()`, request scope middleware |
| Testing | `override()` context manager, `Container` with fakes |

## Documentation

[https://spryx-ai.github.io/spryx-di](https://spryx-ai.github.io/spryx-di)

## Development

```bash
make install   # deps + pre-commit hooks
make check     # lint + typecheck + tests
make docs      # serve docs locally
```

## License

MIT
