from __future__ import annotations


class SpryxDIError(Exception):
    """Base exception for all spryx-di errors."""


class UnresolvableTypeError(SpryxDIError):
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


class CircularDependencyError(SpryxDIError):
    """Raised when a circular dependency is detected."""

    def __init__(self, chain: list[type]) -> None:
        self.chain = chain
        names = " -> ".join(t.__name__ for t in chain)
        super().__init__(f"Circular dependency detected:\n  {names}")


class TypeHintRequiredError(SpryxDIError):
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


class ModuleBoundaryError(SpryxDIError):
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


class ExportWithoutProviderError(SpryxDIError):
    """Raised when a module exports a type that is not in its providers."""

    def __init__(self, module_name: str, type_: type) -> None:
        self.module_name = module_name
        self.type_ = type_
        type_name = getattr(type_, "__name__", str(type_))
        super().__init__(
            f"Module '{module_name}' exports '{type_name}' "
            f"but it is not in its providers.\n\n"
            f"  Hint: Add a provider for {type_name}."
        )


class UnresolvedImportError(SpryxDIError):
    """Module requires a port that no module exports."""

    def __init__(
        self,
        module_name: str,
        import_type: type,
        available_exports: dict[type, str],
    ) -> None:
        self.module_name = module_name
        self.import_type = import_type
        self.available_exports = available_exports
        available = "\n".join(
            f"  {t.__name__} (exported by '{m}')" for t, m in available_exports.items()
        )
        super().__init__(
            f"Module '{module_name}' requires '{import_type.__name__}' "
            f"but no module exports it.\n\n"
            f"Available exports:\n{available}"
        )


class AmbiguousExportError(SpryxDIError):
    """Two modules export the same port."""

    def __init__(self, export_type: type, module_a: str, module_b: str) -> None:
        self.export_type = export_type
        self.module_a = module_a
        self.module_b = module_b
        super().__init__(
            f"'{export_type.__name__}' is exported by both "
            f"'{module_a}' and '{module_b}'.\n"
            f"Only one module should export each port."
        )


class CircularImportError(SpryxDIError):
    """Circular dependency detected in the module import graph."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        chain = " -> ".join(cycle)
        super().__init__(
            f"Circular dependency detected: {chain}\n\n"
            f"Hint: Use the event bus to break the cycle. "
            f"One of the modules should publish an event instead of "
            f"importing a port from the other."
        )


class InvalidListenerError(SpryxDIError):
    """Raised when a listener's handler does not extend EventHandler."""

    def __init__(self, handler_name: str) -> None:
        self.handler_name = handler_name
        super().__init__(
            f"'{handler_name}' must extend EventHandler.\n\n"
            f"  Hint: class {handler_name}(EventHandler[YourEvent]): ..."
        )


class MissingEventBackendError(SpryxDIError):
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


class SerializationError(SpryxDIError):
    """Raised when an event cannot be serialized."""

    def __init__(self, type_name: str) -> None:
        self.type_name = type_name
        super().__init__(
            f"Cannot serialize event of type '{type_name}'.\n\n"
            f"  Supported: dataclass, Pydantic BaseModel, dict, "
            f"or any class with to_dict()."
        )
