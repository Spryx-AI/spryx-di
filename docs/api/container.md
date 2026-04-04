# Container API

## Container

### `register(interface: type, implementation: type) -> None`

Register a transient mapping. New instance every `resolve()`.

### `singleton(interface: type, implementation: type) -> None`

Register a singleton mapping. One instance per container lifetime.

### `instance(type_: type[T], obj: T) -> None`

Register a pre-built instance.

### `factory(type_: type[T], func: Callable[[Container], T]) -> None`

Register a factory function. Called with the container on each resolve.

### `has(type_: type) -> bool`

Check if a type is registered.

### `override(type_: type, implementation: Any) -> None`

Replace an existing registration. If `implementation` is a type, registers as transient. If it's an instance, registers as instance.

### `resolve(type_: type[T]) -> T`

Resolve a type, auto-wiring `__init__` dependencies.

**Raises:** `UnresolvableTypeError`, `CircularDependencyError`, `TypeHintRequiredError`

```python
handler = container.resolve(ListHandler)
```

### `__getitem__(type_: type[T]) -> T`

Alias for `resolve()`.

```python
handler = container[ListHandler]
```

### `create_scope() -> ScopedContainer`

Create a scoped container inheriting this container's registrations.

### `on_shutdown(hook: Callable) -> None`

Register a sync or async callable to run on `shutdown()`.

### `async shutdown() -> None`

Run all shutdown hooks in reverse order, then clear them.

## ScopedContainer

Extends `Container`. Resolves from scope-local registrations first, then falls back to parent.

```python
scope = container.create_scope()
scope.instance(Transaction, tx)
handler = scope.resolve(Handler)
```
