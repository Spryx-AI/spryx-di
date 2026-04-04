# Auto-Wiring

spryx-di resolves dependencies automatically by inspecting `__init__` type hints. No decorators, no registration of the handler itself.

```python
class ListHandler:
    def __init__(self, repo: ConversationRepo, reader: TeamReader) -> None:
        self._repo = repo
        self._reader = reader

handler = ctx.resolve(ListHandler)
# repo and reader are resolved from the container
```

## How It Works

1. Read `__init__` type hints (excluding `self` and `return`)
2. For each parameter, `resolve()` the hinted type recursively
3. If a type has a default value and isn't registered, use the default
4. Skip `*args` and `**kwargs` parameters
5. Construct the class with all resolved dependencies

## Errors

### UnresolvableTypeError

A required dependency isn't registered and has no default:

```
UnresolvableTypeError: Cannot resolve 'ListHandler'.
  Parameter 'reader' expects type 'TeamReader' which is not registered.

  Hint: Register it with container.register(TeamReader, <implementation>)
```

### CircularDependencyError

Two or more types depend on each other:

```
CircularDependencyError: Circular dependency detected:
  ServiceA -> ServiceB -> ServiceA
```

### TypeHintRequiredError

A parameter has no type hint:

```
TypeHintRequiredError: Cannot auto-wire 'MyService.__init__'.
  Parameter 'db' has no type hint.

  Hint: Add a type hint or register a factory with container.factory(MyService, ...)
```
