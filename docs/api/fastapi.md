# FastAPI Integration API

```python
from spryx_di.ext.fastapi import configure, Inject, ScopedInject
```

## `configure(app: FastAPI, container: Container) -> None`

Attach the container to `app.state.container` and add `RequestScopeMiddleware`.

## `Inject(cls: type[T]) -> T`

Returns a FastAPI `Depends()` that resolves `cls` from the app's global container.

```python
@router.get("/items")
def list_items(handler: ListHandler = Inject(ListHandler)):
    ...
```

## `ScopedInject(cls: type[T]) -> T`

Returns a FastAPI `Depends()` that resolves `cls` from the request-scoped container.

```python
@router.get("/items")
def list_items(handler: ListHandler = ScopedInject(ListHandler)):
    ...
```

## RequestScopeMiddleware

Added automatically by `configure()`. Creates a `ScopedContainer` per request at `request.state.scope`.
