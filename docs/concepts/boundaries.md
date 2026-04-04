# Module Boundaries

spryx-di enforces module boundaries at boot time. If a module tries to access a type that belongs to another module but isn't exported, it fails early.

## How It Works

Each module gets an isolated container with:

1. Its own providers
2. Globals (shared by all modules)
3. Exports from imported modules

Types not in this set are inaccessible via `resolve_within()`.

## ModuleBoundaryError

```python
identity_module = Module(
    name="identity",
    providers=[
        ClassProvider(provide=UserRepository, use_class=PgUserRepository),
        ClassProvider(provide=UserReader, use_class=PgUserReader),
    ],
    exports=[UserReader],  # UserRepository NOT exported
)

orders_module = Module(
    name="orders",
    imports=[identity_module],
)

ctx = ApplicationContext(modules=[identity_module, orders_module])

ctx.resolve_within(orders_module, UserRepository)
# ModuleBoundaryError: Cannot resolve 'UserRepository' in module 'orders'.
#   'UserRepository' is a provider of 'identity' but is not exported.
#
#   Exported by 'identity': [UserReader]
```

## Boot-Time Validation

These errors are raised during `ApplicationContext.__init__()`, before any request is served:

| Error | Cause |
|---|---|
| `ExportWithoutProviderError` | Module exports a type not in its providers |
| `ModuleNotFoundError` | Module imports a module not in the ApplicationContext |
| `CircularModuleError` | Circular dependency via direct references (use `forward_ref` instead) |

## resolve() vs resolve_within()

- `ctx.resolve(Type)` — resolves from the global container, no boundary checks
- `ctx.resolve_within(module, Type)` — resolves within a module's boundary
