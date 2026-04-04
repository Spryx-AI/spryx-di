# Circular Dependencies

When two modules depend on each other, Python's import system will fail before spryx-di even runs. `forward_ref` solves this.

## The Problem

```python
# identity/module.py
from billing.module import billing_module  # ImportError: circular

identity_module = Module(
    name="identity",
    imports=[billing_module],
)
```

## The Solution: forward_ref

```python
from spryx_di import Module, forward_ref

# identity/module.py — does NOT import billing
identity_module = Module(
    name="identity",
    providers=[...],
    exports=[UserReader],
    imports=[forward_ref("billing")],
)

# billing/module.py — does NOT import identity
billing_module = Module(
    name="billing",
    providers=[...],
    exports=[BillingGateway],
    imports=[forward_ref("identity")],
)
```

`forward_ref("billing")` is a string reference resolved by `ApplicationContext` at boot time, after all modules are loaded.

## What Happens at Boot

- `ApplicationContext` resolves all forward_refs to real modules
- Circular via `forward_ref` is allowed, with a WARNING log:
  ```
  WARNING: Circular dependency between modules 'identity' <-> 'billing'
  (resolved via forward_ref). Consider extracting shared types
  into a separate module if this grows.
  ```
- Circular via direct references still raises `CircularModuleError`

## Alternatives

If `forward_ref` is spreading across many modules, consider:

1. **Extract a shared module** — move common types to a third module both can import
2. **Domain events** — decouple with async event bus instead of direct dependency
3. **Rethink boundaries** — maybe the two modules should be one
