# Lifecycle

spryx-di supports graceful shutdown via `on_destroy` callbacks on modules and automatic cleanup of managed instances.

## Module on_destroy

Each module can declare a shutdown callback that receives its container:

```python
async def shutdown_messaging(container: Container) -> None:
    client = container.resolve(httpx.AsyncClient)
    await client.aclose()

messaging_module = Module(
    name="messaging",
    providers=[...],
    on_destroy=shutdown_messaging,
)
```

## Managed Instances

Instances registered with `use_value` that implement `__aexit__`, `aclose`, or `close` are closed automatically on shutdown:

```python
# These are auto-closed on shutdown
ctx = ApplicationContext(
    modules=[...],
    globals=[
        Provider(provide=AsyncEngine, use_value=engine),     # has .dispose()
        Provider(provide=Redis, use_value=redis_client),     # has .aclose()
    ],
)
```

## Container Shutdown Hooks

For additional cleanup, register hooks directly:

```python
ctx.on_shutdown(lambda: print("shutting down"))
```

## Shutdown Order

`await ctx.shutdown()` executes in this order:

1. `on_destroy` of each module (reverse registration order)
2. Auto-close managed instances (reverse order)
3. Container-level shutdown hooks (reverse order)

## FastAPI Integration

```python
@app.on_event("shutdown")
async def shutdown():
    await app_context.shutdown()
```
