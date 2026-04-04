# Container

The `Container` is the low-level DI container. It stores registrations and resolves dependencies by inspecting `__init__` type hints.

Most applications use `ApplicationContext` (which manages containers internally), but `Container` is useful for tests and simple setups.

```python
from spryx_di import Container

container = Container()
container.singleton(UserReader, PgUserReader)
container.instance(Database, my_db)

handler = container.resolve(ListHandler)  # auto-wired
handler = container[ListHandler]          # same thing
```

## Registration Methods

| Method | Behavior |
|---|---|
| `register(iface, impl)` | New instance every `resolve()` (transient) |
| `singleton(iface, impl)` | One instance per container lifetime |
| `instance(type, obj)` | Pre-built object, always the same |
| `factory(type, fn)` | Factory receives the container: `fn(container)` |

## Resolution

`resolve(Type)` follows this order:

1. Instance registered? Return it.
2. Factory registered? Call it.
3. Singleton cache hit? Return it.
4. Find implementation (singleton/transient mapping or auto-wire the type itself).
5. Inspect `__init__` type hints, resolve each dependency recursively.
6. Cache if singleton.

## Scoped Containers

```python
scope = container.create_scope()
scope.instance(Transaction, current_tx)

# Resolves Transaction from scope, Database from parent
handler = scope.resolve(Handler)
```

`ScopedContainer` inherits all parent registrations. Scope-local registrations take priority.
