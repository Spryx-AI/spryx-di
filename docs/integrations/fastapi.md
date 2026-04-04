# FastAPI Integration

```bash
pip install spryx-di[fastapi]
```

## Setup

```python
from fastapi import FastAPI
from spryx_di import ApplicationContext
from spryx_di.ext.fastapi import configure

ctx = ApplicationContext(modules=[...])

app = FastAPI()
configure(app, ctx.container)
```

`configure()` attaches the container to `app.state.container` and adds the request scope middleware.

## Inject

Resolve a dependency from the global container:

```python
from spryx_di.ext.fastapi import Inject

@router.get("/conversations")
async def list_conversations(
    handler: ListConversationsHandler = Inject(ListConversationsHandler),
):
    return await handler.handle()
```

## ScopedInject

Resolve from the per-request scoped container:

```python
from spryx_di.ext.fastapi import ScopedInject

@router.get("/conversations")
async def list_conversations(
    handler: ListConversationsHandler = ScopedInject(ListConversationsHandler),
):
    return await handler.handle()
```

Each request gets its own `ScopedContainer`. Use `ScopedInject` when you need request-scoped dependencies like transactions or tenant context.

## Shutdown

```python
@app.on_event("shutdown")
async def shutdown():
    await ctx.shutdown()
```
