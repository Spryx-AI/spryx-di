# Provider API

## Provider

```python
@dataclass(frozen=True)
class Provider:
    provide: type
    use_class: type | None = None
    use_factory: Callable[[Container], Any] | None = None
    use_value: Any = _MISSING
    scope: Scope = Scope.SINGLETON
```

Exactly one of `use_class`, `use_factory`, or `use_value` must be specified. Raises `ValueError` otherwise.

## Scope

```python
class Scope(Enum):
    TRANSIENT = "transient"
    SINGLETON = "singleton"
```

Default is `SINGLETON`.

## ForwardRef

```python
@dataclass(frozen=True)
class ForwardRef:
    module_name: str
```

Lazy module reference resolved by `ApplicationContext` at boot.

## forward_ref

```python
def forward_ref(name: str) -> ForwardRef
```

Create a forward reference to a module by name. Use in `Module.imports` to avoid circular Python imports.

```python
identity_module = Module(
    name="identity",
    imports=[forward_ref("billing")],
)
```
