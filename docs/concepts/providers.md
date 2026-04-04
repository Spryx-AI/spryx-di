# Providers

A `Provider` describes how to create an instance of a type.

## use_class

Map an interface to a concrete class. The container auto-wires the class's `__init__`.

```python
Provider(provide=TeamReader, use_class=PgTeamReader)
```

## use_factory

Provide a callable that receives the container. Use for conditional logic or complex setup.

```python
Provider(
    provide=BillingGateway,
    use_factory=lambda c: StripeBillingGateway(c.resolve(Config)),
)
```

## use_value

Register a pre-built instance.

```python
Provider(provide=Database, use_value=my_db_instance)
```

## Scope

Default is `Scope.SINGLETON` — one instance for the container's lifetime.

```python
from spryx_di import Scope

Provider(provide=Handler, use_class=Handler, scope=Scope.TRANSIENT)
```

| Scope | Behavior |
|---|---|
| `SINGLETON` (default) | One instance per container |
| `TRANSIENT` | New instance every `resolve()` |

## Bare Type Shorthand

Pass a class directly in `providers` as shorthand for `Provider(provide=T, use_class=T)`:

```python
Module(
    name="identity",
    providers=[PgTeamReader, PgUserReader],  # singleton, self-bound
)
```

> In NestJS, this is equivalent to listing a class in `providers: [TeamService]`.
