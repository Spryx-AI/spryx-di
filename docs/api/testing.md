# Testing Utilities API

```python
from spryx_di.testing import override
```

## `override(container: Container, overrides: dict[type, Any]) -> Iterator[None]`

Context manager that temporarily replaces container registrations and restores them on exit.

```python
with override(container, {UserReader: FakeUserReader}):
    result = container.resolve(UserReader)  # FakeUserReader

# Original registration restored
result = container.resolve(UserReader)  # PgUserReader
```

**Parameters:**

- `container` — The container to override
- `overrides` — Dict mapping types to replacements. Values can be:
  - A type (registered as transient)
  - An instance (registered as instance)
