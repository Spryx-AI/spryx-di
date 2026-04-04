# Module API

## Module

```python
@dataclass
class Module:
    name: str
    providers: list[Provider | type]
    exports: list[type]
    imports: list[Module | ForwardRef]
    on_destroy: Callable[[Container], Awaitable[None]] | None = None
```

| Field | Description |
|---|---|
| `name` | Unique module identifier |
| `providers` | Types this module registers |
| `exports` | Types visible to importing modules |
| `imports` | Modules this module depends on |
| `on_destroy` | Async callback called on `shutdown()` with the module's container |

## ApplicationContext

### `__init__(modules: list[Module], globals: list[Provider] | None = None)`

Compose modules with boundary enforcement.

**Boot-time validation:**

1. Every export must exist in providers (`ExportWithoutProviderError`)
2. Every import must be in the modules list (`ModuleNotFoundError`)
3. No circular direct imports (`CircularModuleError`)

### `resolve(type_: type[T]) -> T`

Resolve from the global container. No boundary checks.

### `resolve_within(module: Module, type_: type[T]) -> T`

Resolve within a module's boundary.

**Raises:** `ModuleBoundaryError` if accessing a non-exported type from another module.

### `container: Container` (property)

Access the underlying global container.

### `on_shutdown(hook: Callable) -> None`

Register a shutdown hook.

### `async shutdown() -> None`

1. Run `on_destroy` for each module (reverse order)
2. Close managed instances (`__aexit__`/`aclose`/`close`)
3. Run container shutdown hooks

### `create_scope() -> ScopedContainer`

Create a scoped container from the global container.
