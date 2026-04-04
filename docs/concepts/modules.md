# Modules

A `Module` is a declarative unit of organization inspired by NestJS `@Module()`.

```python
from spryx_di import ClassProvider, Module

identity_module = Module(
    name="identity",
    providers=[
        ClassProvider(provide=UserRepository, use_class=PgUserRepository),
        ClassProvider(provide=UserReader, use_class=PgUserReader),
    ],
    exports=[UserReader],
    imports=[],
)
```

## Fields

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Unique module name |
| `providers` | `list[Provider \| type]` | What this module registers |
| `exports` | `list[type]` | What other modules can consume |
| `imports` | `list[Module \| ForwardRef]` | Which modules this module depends on |
| `on_destroy` | `Callable \| None` | Shutdown callback (see [Lifecycle](lifecycle.md)) |

## exports

Only exported types are visible to other modules. Everything else is private.

```python
exports=[UserReader]  # UserRepository stays internal
```

## imports

Reference modules directly or use `forward_ref` for circular dependencies:

```python
orders_module = Module(
    name="orders",
    imports=[identity_module],  # direct reference
)
```

## Composition

`ApplicationContext` wires all modules together:

```python
from spryx_di import ApplicationContext

ctx = ApplicationContext(
    modules=[identity_module, orders_module],
    globals=[ValueProvider(provide=Database, use_value=db)],
)
```

> In NestJS, `ApplicationContext` is similar to `NestFactory.create(AppModule)`. Modules map to `@Module()`, providers to the `providers` array, exports to the `exports` array.
