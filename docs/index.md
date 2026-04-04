# spryx-di

Lightweight dependency injection for Python modular monoliths.

- **NestJS-inspired modules** with providers, exports, and imports
- **Type-based auto-wiring** via `__init__` type hints
- **Module boundary enforcement** at boot time
- **Zero runtime dependencies**
- **Zero intrusion** in domain code

## Quick Example

```python
from spryx_di import ClassProvider, Module, ApplicationContext

identity_module = Module(
    name="identity",
    providers=[
        ClassProvider(provide=UserRepository, use_class=PgUserRepository),
        ClassProvider(provide=UserReader, use_class=PgUserReader),
    ],
    exports=[UserReader],
)

ctx = ApplicationContext(modules=[identity_module])
reader = ctx.resolve(UserReader)  # auto-wired, singleton, boundary-safe
```

## Install

=== "uv"

    ```bash
    uv add spryx-di
    ```

=== "pip"

    ```bash
    pip install spryx-di
    ```

=== "poetry"

    ```bash
    poetry add spryx-di
    ```
