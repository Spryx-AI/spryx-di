from __future__ import annotations

import inspect
import logging
from typing import Any, TypeVar, overload

from spryx_di.errors import (
    CircularDependencyError,
    TypeHintRequiredError,
    UnresolvableTypeError,
)

logger = logging.getLogger("spryx_di")

T = TypeVar("T")


class Container:
    """Lightweight type-based dependency injection container."""

    def __init__(self) -> None:
        self._instances: dict[type, Any] = {}
        self._factories: dict[type, Any] = {}
        self._singletons: dict[type, type] = {}
        self._transients: dict[type, type] = {}
        self._singleton_cache: dict[type, Any] = {}
        self._shutdown_hooks: list[Any] = []

    def register(self, interface: type, implementation: type) -> None:
        self._warn_duplicate(interface)
        self._transients[interface] = implementation

    def singleton(self, interface: type, implementation: type) -> None:
        self._warn_duplicate(interface)
        self._singletons[interface] = implementation

    def instance(self, type_: type[T], obj: T) -> None:
        self._warn_duplicate(type_)
        self._instances[type_] = obj

    def factory(self, type_: type[T], func: Any) -> None:
        self._warn_duplicate(type_)
        self._factories[type_] = func

    def has(self, type_: type) -> bool:
        return (
            type_ in self._instances
            or type_ in self._factories
            or type_ in self._singletons
            or type_ in self._transients
        )

    def override(self, type_: type, implementation: Any) -> None:
        self._instances.pop(type_, None)
        self._factories.pop(type_, None)
        self._singletons.pop(type_, None)
        self._transients.pop(type_, None)
        self._singleton_cache.pop(type_, None)

        if isinstance(implementation, type):
            self._transients[type_] = implementation
        else:
            self._instances[type_] = implementation

    @overload
    def resolve(self, type_: type[T]) -> T: ...

    @overload
    def resolve(self, type_: type[T], _resolving: frozenset[type]) -> T: ...

    def resolve(self, type_: type[T], _resolving: frozenset[type] | None = None) -> T:  # noqa: C901
        resolving = _resolving or frozenset()

        if type_ in self._instances:
            return self._instances[type_]  # type: ignore[return-value]

        if type_ in self._factories:
            result = self._factories[type_](self)
            if type_ in self._singletons:
                self._singleton_cache[type_] = result
            return result  # type: ignore[return-value]

        if type_ in self._singleton_cache:
            return self._singleton_cache[type_]  # type: ignore[return-value]

        is_singleton = type_ in self._singletons
        if is_singleton:
            impl = self._singletons[type_]
        elif type_ in self._transients:
            impl = self._transients[type_]
        elif self._is_auto_wireable(type_):
            impl = type_
        else:
            raise UnresolvableTypeError(type_, "", type_)

        if impl in resolving:
            chain = [*self._build_chain(resolving, impl), impl]
            raise CircularDependencyError(chain)

        obj = self._auto_wire(type_, impl, resolving | {impl})

        if is_singleton:
            self._singleton_cache[type_] = obj

        return obj  # type: ignore[return-value]

    def _auto_wire(self, requested: type, impl: type, resolving: frozenset[type]) -> Any:
        hints = self._get_init_hints(impl)
        params = inspect.signature(impl.__init__).parameters  # type: ignore[misc]

        kwargs: dict[str, Any] = {}
        for name, param in params.items():
            if name == "self":
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            if name not in hints:
                if param.default is not inspect.Parameter.empty:
                    continue
                raise TypeHintRequiredError(impl, name)

            hint = hints[name]
            if hint is inspect.Parameter.empty:
                if param.default is not inspect.Parameter.empty:
                    continue
                raise TypeHintRequiredError(impl, name)

            try:
                kwargs[name] = self.resolve(hint, resolving)
            except (UnresolvableTypeError, TypeHintRequiredError):
                if param.default is not inspect.Parameter.empty:
                    continue
                raise UnresolvableTypeError(requested, name, hint) from None

        return impl(**kwargs)

    @staticmethod
    def _is_auto_wireable(type_: type) -> bool:
        return type_.__module__ != "builtins"

    def _get_init_hints(self, cls: type) -> dict[str, Any]:
        import typing

        try:
            raw = typing.get_type_hints(cls.__init__)  # type: ignore[misc]
            return {k: v for k, v in raw.items() if k != "return"}
        except Exception:
            pass

        try:
            raw = inspect.get_annotations(cls.__init__, eval_str=True)  # type: ignore[misc]
            return {k: v for k, v in raw.items() if k != "return"}
        except Exception:
            return {}

    def _build_chain(self, resolving: frozenset[type], target: type) -> list[type]:
        return list(resolving) if target in resolving else [*resolving]

    def _warn_duplicate(self, type_: type) -> None:
        if self.has(type_):
            logger.warning("Overwriting registration for '%s'", type_.__name__)

    def on_shutdown(self, hook: Any) -> None:
        """Register an async or sync callable to run on shutdown."""
        self._shutdown_hooks.append(hook)

    async def shutdown(self) -> None:
        """Run all shutdown hooks in reverse registration order."""
        import asyncio

        for hook in reversed(self._shutdown_hooks):
            result = hook()
            if asyncio.iscoroutine(result):
                await result
        self._shutdown_hooks.clear()

    def create_scope(self) -> ScopedContainer:
        return ScopedContainer(parent=self)

    def __getitem__(self, type_: type[T]) -> T:
        return self.resolve(type_)


class ScopedContainer(Container):
    """A scoped container that inherits registrations from a parent."""

    def __init__(self, parent: Container) -> None:
        super().__init__()
        self._parent = parent

    def has(self, type_: type) -> bool:
        return super().has(type_) or self._parent.has(type_)

    def _is_local(self, type_: type) -> bool:
        return (
            type_ in self._instances
            or type_ in self._factories
            or type_ in self._singletons
            or type_ in self._transients
            or type_ in self._singleton_cache
        )

    @overload
    def resolve(self, type_: type[T]) -> T: ...

    @overload
    def resolve(self, type_: type[T], _resolving: frozenset[type]) -> T: ...

    def resolve(self, type_: type[T], _resolving: frozenset[type] | None = None) -> T:  # noqa: C901
        resolving = _resolving or frozenset()

        if self._is_local(type_):
            return super().resolve(type_, resolving)

        if type_ in self._parent._instances:
            return self._parent._instances[type_]  # type: ignore[return-value]

        if type_ in self._parent._factories:
            return self._parent._factories[type_](self)  # type: ignore[return-value]

        if type_ in self._parent._singleton_cache:
            return self._parent._singleton_cache[type_]  # type: ignore[return-value]

        is_singleton = type_ in self._parent._singletons
        if is_singleton:
            impl = self._parent._singletons[type_]
        elif type_ in self._parent._transients:
            impl = self._parent._transients[type_]
        elif self._is_auto_wireable(type_):
            impl = type_
        else:
            raise UnresolvableTypeError(type_, "", type_)

        if impl in resolving:
            chain = [*self._build_chain(resolving, impl), impl]
            raise CircularDependencyError(chain)

        obj = self._auto_wire(type_, impl, resolving | {impl})

        if is_singleton:
            self._parent._singleton_cache[type_] = obj

        return obj  # type: ignore[return-value]
