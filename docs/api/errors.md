# Errors

## UnresolvableTypeError

A required dependency is not registered and has no default value.

```
Cannot resolve 'ListHandler'.
  Parameter 'reader' expects type 'TeamReader' which is not registered.

  Hint: Register it with container.register(TeamReader, <implementation>)
```

## CircularDependencyError

Two or more types depend on each other in a cycle.

```
Circular dependency detected:
  ServiceA -> ServiceB -> ServiceA
```

## TypeHintRequiredError

An `__init__` parameter has no type annotation.

```
Cannot auto-wire 'MyService.__init__'.
  Parameter 'db' has no type hint.

  Hint: Add a type hint or register a factory with container.factory(MyService, ...)
```

## ModuleBoundaryError

Attempting to access a type from another module that isn't exported.

```
Cannot resolve 'UserRepository' in module 'orders'.
  'UserRepository' is a provider of 'identity' but is not exported.

  Exported by 'identity': [UserReader]
```

## ExportWithoutProviderError

A module exports a type that isn't in its providers list.

```
Module 'identity' exports 'TeamReader' but it is not in its providers.

  Hint: Add a Provider(provide=TeamReader, use_class=...) to the providers list,
  or remove TeamReader from exports.
```

## ModuleNotFoundError

A module imports another module not registered in the ApplicationContext.

```
Module 'orders' imports module 'billing' which is not registered in the ApplicationContext.

  Hint: Add 'billing' to the modules list in ApplicationContext.
```

## CircularModuleError

Circular dependency between modules via direct references (not `forward_ref`).

```
Circular module dependency detected:
  a -> b -> c -> a

  Hint: Break the cycle by extracting shared types into a separate module.
```
