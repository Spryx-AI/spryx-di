from __future__ import annotations

import inspect
import logging
import sys
import types
import typing
from typing import Any, TypeVar, Union, cast, get_args, get_origin

from spryx_di.errors import (
    CircularDependencyError,
    TypeHintRequiredError,
    UnresolvableTypeError,
)

logger = logging.getLogger("spryx_di")

T = TypeVar("T")


class Container:
    """Lightweight type-based dependency injection container."""

    def __init__(self, *, auto_wire: bool = True) -> None:
        self._instances: dict[type, Any] = {}
        self._factories: dict[type, Any] = {}
        self._singletons: dict[type, type] = {}
        self._transients: dict[type, type] = {}
        self._singleton_cache: dict[type, Any] = {}
        self._shutdown_hooks: list[Any] = []
        self._allow_auto_wire = auto_wire

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

    def resolve(self, type_: type[T]) -> T:
        return cast(T, self._resolve_untyped(type_, frozenset()))

    def _resolve_untyped(self, type_: type, resolving: frozenset[type]) -> object:
        if type_ in self._instances:
            return self._instances[type_]

        if type_ in self._singleton_cache:
            return self._singleton_cache[type_]

        if type_ in self._factories:
            result = self._factories[type_](self)
            if type_ in self._singletons:
                self._singleton_cache[type_] = result
            return result

        impl = self._find_implementation(type_)
        if impl is None:
            raise UnresolvableTypeError(type_, "", type_)

        if impl in resolving:
            raise CircularDependencyError([*resolving, impl])

        obj = self._auto_wire(type_, impl, resolving | {impl})

        if type_ in self._singletons:
            self._singleton_cache[type_] = obj

        return obj

    def _find_implementation(self, type_: type) -> type | None:
        if type_ in self._singletons:
            return self._singletons[type_]
        if type_ in self._transients:
            return self._transients[type_]
        if self._allow_auto_wire and self._is_auto_wireable(type_):
            return type_
        return None

    def _auto_wire(self, requested: type, impl: type, resolving: frozenset[type]) -> object:
        hints = self._get_init_hints(impl)
        init = getattr(impl, "__init__", None)
        if init is None:
            return impl()

        params = inspect.signature(init).parameters

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

            raw_hint = hints[name]
            if raw_hint is inspect.Parameter.empty:
                if param.default is not inspect.Parameter.empty:
                    continue
                raise TypeHintRequiredError(impl, name)

            hint = self._unwrap_optional(raw_hint)
            if hint is None:
                if param.default is not inspect.Parameter.empty:
                    continue
                raise TypeHintRequiredError(impl, name)

            try:
                kwargs[name] = self._resolve_untyped(hint, resolving)
            except (UnresolvableTypeError, TypeHintRequiredError):
                if param.default is not inspect.Parameter.empty:
                    continue
                raise UnresolvableTypeError(requested, name, hint) from None

        return impl(**kwargs)

    @staticmethod
    def _unwrap_optional(hint: Any) -> type | None:
        if hint is typing.Any:
            return None

        origin = get_origin(hint)
        if isinstance(hint, types.UnionType) or origin is Union:
            non_none = [a for a in get_args(hint) if a is not type(None)]
            if len(non_none) == 1 and isinstance(non_none[0], type):
                return non_none[0]
            return None

        if isinstance(hint, type):
            return hint

        return None

    @staticmethod
    def _is_auto_wireable(type_: type) -> bool:
        if type_.__module__ == "builtins":
            return False
        if getattr(type_, "_is_protocol", False):
            return False
        return not getattr(type_, "__abstractmethods__", None)

    def _get_init_hints(self, cls: type) -> dict[str, type]:
        init = getattr(cls, "__init__", None)
        if init is None:
            return {}
        try:
            raw = typing.get_type_hints(init)
            raw.pop("return", None)
            return raw
        except Exception:
            mod = sys.modules.get(cls.__module__)
            globalns = dict(vars(mod)) if mod else {}
            for source in (self._instances, self._singletons, self._transients, self._factories):
                for registered_type in source:
                    if not isinstance(registered_type, type):
                        continue
                    name = registered_type.__name__
                    if name in globalns and globalns[name] is not registered_type:
                        logger.warning(
                            "Name collision in auto-wiring namespace: '%s' already exists. "
                            "Use FactoryProvider for disambiguation.",
                            name,
                        )
                        continue
                    globalns.setdefault(name, registered_type)
            try:
                raw = typing.get_type_hints(init, globalns=globalns)
                raw.pop("return", None)
                return raw
            except Exception:
                return {}

    def _warn_duplicate(self, type_: type) -> None:
        if self.has(type_):
            logger.warning("Overwriting registration for '%s'", type_.__name__)

    def on_shutdown(self, hook: Any) -> None:
        self._shutdown_hooks.append(hook)

    async def shutdown(self) -> None:
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

    def resolve(self, type_: type[T]) -> T:
        return cast(T, self._resolve_untyped(type_, frozenset()))

    def _resolve_untyped(self, type_: type, resolving: frozenset[type]) -> object:
        if self._is_local(type_):
            return super()._resolve_untyped(type_, resolving)
        return self._resolve_from_parent(type_, resolving)

    def _resolve_from_parent(self, type_: type, resolving: frozenset[type]) -> object:
        if type_ in self._parent._instances:
            return self._parent._instances[type_]

        if type_ in self._parent._singleton_cache:
            return self._parent._singleton_cache[type_]

        if type_ in self._parent._factories:
            return self._parent._factories[type_](self)

        impl = self._parent._find_implementation(type_)
        if impl is None:
            raise UnresolvableTypeError(type_, "", type_)

        if impl in resolving:
            raise CircularDependencyError([*resolving, impl])

        obj = self._auto_wire(type_, impl, resolving | {impl})

        if type_ in self._parent._singletons:
            self._parent._singleton_cache[type_] = obj

        return obj
