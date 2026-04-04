# Providers

Providers describe how to create an instance of a type. Each variant is a separate class — the type checker enforces correct usage.

```python
from spryx_di import ClassProvider, FactoryProvider, ValueProvider, ExistingProvider
```

## ClassProvider

Map an interface to a concrete class. The container auto-wires the class's `__init__`.

```python
ClassProvider(provide=TeamReader, use_class=PgTeamReader)
```

## FactoryProvider

Provide a callable that receives the container. Use for conditional logic or complex setup.

```python
FactoryProvider(
    provide=BillingGateway,
    use_factory=lambda c: StripeBillingGateway(c.resolve(Config)),
)
```

## ValueProvider

Register a pre-built instance.

```python
ValueProvider(provide=Database, use_value=my_db_instance)
```

## ExistingProvider

Alias one type to another. When `provide` is requested, the container resolves `use_existing` instead.

```python
ExistingProvider(provide=AssetService, use_existing=AssetServiceImpl)
```

Eliminates boilerplate factory functions for port → implementation mappings.

## Scope

`ClassProvider` and `FactoryProvider` accept a `scope` parameter. Default is `Scope.SINGLETON`.

```python
from spryx_di import Scope

ClassProvider(provide=Handler, use_class=Handler, scope=Scope.TRANSIENT)
```

| Scope | Behavior |
|---|---|
| `SINGLETON` (default) | One instance per container |
| `TRANSIENT` | New instance every `resolve()` |

## Union Type

All four are unified under `Provider`:

```python
Provider = ClassProvider | FactoryProvider | ValueProvider | ExistingProvider
```

## Bare Type Shorthand

Pass a class directly in `providers` as shorthand for `ClassProvider(provide=T, use_class=T)`:

```python
Module(
    name="identity",
    providers=[PgTeamReader, PgUserReader],  # singleton, self-bound
)
```

> In NestJS, this is equivalent to listing a class in `providers: [TeamService]`.
