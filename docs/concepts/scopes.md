# Scopes

Scopes control the lifecycle of resolved instances.

## Singleton (default)

One instance per container lifetime. All calls to `resolve()` return the same object.

```python
ClassProvider(provide=UserReader, use_class=PgUserReader)  # singleton by default
```

Use for: repositories, readers, database pools, HTTP clients.

## Transient

New instance every `resolve()` call.

```python
from spryx_di import ClassProvider, Scope

ClassProvider(provide=RequestHandler, use_class=RequestHandler, scope=Scope.TRANSIENT)
```

Use for: stateful handlers, one-off processors.

## Scoped (request-level)

Create a `ScopedContainer` per request. Singletons within the scope are local — they don't leak to the parent or other scopes.

```python
scope = container.create_scope()
scope.instance(Transaction, current_tx)
scope.instance(TenantContext, current_tenant)

handler = scope.resolve(Handler)
# Handler gets Transaction from scope, Database from parent
```

In FastAPI, the `RequestScopeMiddleware` creates a scope per request automatically. See [FastAPI Integration](../integrations/fastapi.md).
