from __future__ import annotations


class UnresolvableTypeError(Exception):
    """Raised when a dependency cannot be resolved."""

    def __init__(self, target: type, parameter: str, expected_type: type) -> None:
        self.target = target
        self.parameter = parameter
        self.expected_type = expected_type
        if parameter:
            msg = (
                f"Cannot resolve '{target.__name__}'.\n"
                f"  Parameter '{parameter}' expects type '{expected_type.__name__}' "
                f"which is not registered.\n\n"
                f"  Hint: Register it with container.register("
                f"{expected_type.__name__}, <implementation>)"
            )
        else:
            msg = (
                f"Cannot resolve '{target.__name__}'.\n"
                f"  Type '{expected_type.__name__}' is not registered.\n\n"
                f"  Hint: Register it with container.register("
                f"{expected_type.__name__}, <implementation>)"
            )
        super().__init__(msg)


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""

    def __init__(self, chain: list[type]) -> None:
        self.chain = chain
        names = " -> ".join(t.__name__ for t in chain)
        super().__init__(f"Circular dependency detected:\n  {names}")


class TypeHintRequiredError(Exception):
    """Raised when __init__ parameter has no type hint."""

    def __init__(self, target: type, parameter: str) -> None:
        self.target = target
        self.parameter = parameter
        super().__init__(
            f"Cannot auto-wire '{target.__name__}.__init__'.\n"
            f"  Parameter '{parameter}' has no type hint.\n\n"
            f"  Hint: Add a type hint or register a factory with "
            f"container.factory({target.__name__}, ...)"
        )


class ModuleBoundaryError(Exception):
    """Raised when resolving a type that violates module boundaries."""

    def __init__(
        self,
        type_: type,
        module_name: str,
        owner_module: str,
        exported: set[type],
    ) -> None:
        self.type_ = type_
        self.module_name = module_name
        self.owner_module = owner_module
        self.exported = exported
        exported_names = ", ".join(t.__name__ for t in exported) if exported else "(none)"
        super().__init__(
            f"Cannot resolve '{type_.__name__}' in module '{module_name}'.\n"
            f"  '{type_.__name__}' is a provider of '{owner_module}' but is not exported.\n\n"
            f"  Exported by '{owner_module}': [{exported_names}]"
        )


class ExportWithoutProviderError(Exception):
    """Raised when a module exports a type that is not in its providers."""

    def __init__(self, module_name: str, type_: type) -> None:
        self.module_name = module_name
        self.type_ = type_
        super().__init__(
            f"Module '{module_name}' exports '{type_.__name__}' "
            f"but it is not in its providers.\n\n"
            f"  Hint: Add a ClassProvider(provide={type_.__name__}, use_class=...) "
            f"to the providers list, or remove {type_.__name__} from exports."
        )


class ModuleNotFoundError(Exception):
    """Raised when a module imports another module not registered in ApplicationContext."""

    def __init__(self, module_name: str, imported_name: str) -> None:
        self.module_name = module_name
        self.imported_name = imported_name
        super().__init__(
            f"Module '{module_name}' imports module '{imported_name}' "
            f"which is not registered in the ApplicationContext.\n\n"
            f"  Hint: Add '{imported_name}' to the modules list in ApplicationContext."
        )


class CircularModuleError(Exception):
    """Raised when circular dependencies are detected between modules."""

    def __init__(self, chain: list[str]) -> None:
        self.chain = chain
        names = " -> ".join(chain)
        super().__init__(
            f"Circular module dependency detected:\n"
            f"  {names}\n\n"
            f"  Hint: Break the cycle by extracting shared types into a separate module."
        )


class InvalidListenerError(Exception):
    """Raised when a listener's handler does not extend EventHandler."""

    def __init__(self, handler_name: str) -> None:
        self.handler_name = handler_name
        super().__init__(
            f"'{handler_name}' must extend EventHandler.\n\n"
            f"  Hint: class {handler_name}(EventHandler[YourEvent]): ..."
        )


class MissingEventBackendError(Exception):
    """Raised when an async listener is declared but no event_backend is configured."""

    def __init__(self, module_name: str, handler_name: str) -> None:
        self.module_name = module_name
        self.handler_name = handler_name
        super().__init__(
            f"Module '{module_name}' has async listener '{handler_name}' "
            f"but no event_backend was configured in ApplicationContext.\n\n"
            f"  Hint: Pass event_backend=InMemoryEventBackend() or "
            f"CeleryEventBackend(...) to ApplicationContext."
        )
