## Context

spryx_di is a zero-dependency DI framework for modular monoliths. Modules currently communicate only through explicit imports/exports of service types. There is no built-in mechanism for one module to react to events from another without a direct dependency on the handler type.

The existing `Module` dataclass has `name`, `providers`, `exports`, `imports`, and `on_destroy`. `ApplicationContext` composes modules, enforces boundaries, and manages lifecycle. The event system must integrate naturally with both.

## Goals / Non-Goals

**Goals:**
- Type-safe event handlers where the type checker validates event/handler pairings
- Declarative listener registration inside `Module` (same pattern as providers)
- Sync dispatch (in-process, awaited) and async dispatch (background, via pluggable backend)
- Boot-time validation: handler extends `EventHandler`, dependencies resolvable, async listeners require a backend
- Two built-in backends: Celery (production) and in-memory (testing)
- `EventBus` auto-registered as singleton when any module has listeners

**Non-Goals:**
- Event sourcing or event store persistence
- Event replay or dead-letter queues
- Saga/choreography orchestration primitives
- Distributed tracing integration (can be added later via backend decorator)
- Event schema versioning or migration

## Decisions

### 1. EventHandler as a Generic base class (not Protocol)

Use `class EventHandler(Generic[E])` with an abstract `async def handle(self, event: E) -> None`.

**Why over Protocol**: Handlers need to be instantiated via the container's auto-wiring. A base class gives a clear `issubclass` check at boot time and a single `__orig_bases__` introspection point to extract `E`. Protocols can't be reliably introspected for the generic parameter at runtime.

**Alternative considered**: Decorator-based registration (`@handles(AgentPublished)`). Rejected because it moves type information out of the class signature and into runtime metadata, losing static type checking of the `handle` method parameter.

### 2. EventBus resolves handlers via the container

When dispatching a sync event, `EventBus` calls `container.resolve(handler_type)` for each registered handler. This means handlers get full auto-wiring — their dependencies are injected just like any other service.

**Why not pre-instantiate**: Handlers may depend on request-scoped or transient services. Resolving at dispatch time ensures correct lifecycle.

### 3. ListenerScope enum: SYNC and ASYNC

`SYNC` handlers are awaited inline during `publish()`. `ASYNC` handlers are dispatched to the configured `AsyncEventBackend`.

**Why not just async-all**: Many events need immediate consistency (e.g., updating a read model after a write). Forcing everything through a queue adds latency and complexity for simple in-process reactions.

### 4. AsyncEventBackend as Protocol

A simple `Protocol` with `async def dispatch(self, event: object, metadata: EventMetadata) -> None`. This keeps the core dependency-free while allowing any queue system.

**Why Protocol over ABC**: The backend is a boundary type — consumers don't extend it, they implement it. Protocol fits the structural typing pattern used elsewhere in Python's ecosystem (e.g., `Iterable`, `Hashable`).

### 5. Module.listeners as optional field

Add `listeners: list[EventListener] = field(default_factory=list)` to `Module`. This is additive and keyword-only-compatible — existing code that creates `Module(name=..., providers=..., ...)` continues to work without change.

### 6. EventBus auto-registration

During `ApplicationContext._boot()`, if any module declares listeners, an `EventBus` singleton is registered in the root container. If no listeners exist, no `EventBus` is created — zero overhead for projects that don't use events.

### 7. Event type extraction at boot time

At boot, `ApplicationContext` inspects `EventHandler.__orig_bases__` on each handler class to extract the concrete event type `E`. This is validated against the `EventListener.event` field to ensure consistency. If they don't match, boot fails with a clear error.

## Risks / Trade-offs

**[Risk] Runtime generic extraction may break with complex inheritance** → Mitigation: Only support single-level generic specialization (`EventHandler[ConcreteEvent]`). Document this limitation. Add a clear error message if extraction fails.

**[Risk] Celery backend introduces an optional dependency** → Mitigation: Keep it in `spryx_di/events/backends/celery.py`, import celery lazily, and document it as optional in pyproject.toml extras.

**[Trade-off] Sync handlers block the publish call** → This is intentional for consistency guarantees. Users who need non-blocking behavior should use `ListenerScope.ASYNC`.

**[Trade-off] EventBus needs a container reference** → The bus must resolve handlers at dispatch time. It receives the container at construction (injected by ApplicationContext). This creates a service-locator pattern inside the bus, but this is contained to the framework internals — user code never sees it.
