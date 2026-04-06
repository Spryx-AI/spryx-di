from __future__ import annotations

import logging
import sys
import typing
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

from spryx_di.container import Container, ScopedContainer
from spryx_di.errors import (
    AmbiguousExportError,
    CircularDependencyInModulesError,
    InvalidListenerError,
    MissingEventBackendError,
    ModuleBoundaryError,
    UnresolvedDependencyError,
)
from spryx_di.provider import (
    ClassProvider,
    ExistingProvider,
    FactoryProvider,
    Provider,
    Scope,
    ValueProvider,
)

if TYPE_CHECKING:
    from spryx_di.events.backend import AsyncEventBackend
    from spryx_di.events.handler import EventHandler
    from spryx_di.events.listener import EventListener

logger = logging.getLogger("spryx_di")

T = TypeVar("T")

OnDestroyHook = Callable[[Container], Awaitable[None]] | Callable[[Container], None]
ShutdownHook = Callable[[], Awaitable[None]] | Callable[[], None]


@dataclass
class Module:
    """Declarative module definition."""

    name: str
    providers: list[Provider | type] = field(default_factory=list)
    dependencies: list[type] = field(default_factory=list)
    on_destroy: OnDestroyHook | None = None
    listeners: list[EventListener] = field(default_factory=list)


def _normalize_provider(p: Provider | type) -> Provider:
    if isinstance(p, type):
        return ClassProvider(provide=p)
    return p


def _get_init_hint_types(cls: type, extra_ns: dict[str, type] | None = None) -> set[type]:
    init = getattr(cls, "__init__", None)
    if init is None:
        return set()
    try:
        raw = typing.get_type_hints(init)
    except Exception:
        mod = sys.modules.get(cls.__module__)
        globalns: dict[str, object] = dict(vars(mod)) if mod else {}
        if extra_ns:
            globalns.update(extra_ns)
        try:
            raw = typing.get_type_hints(init, globalns=globalns)
        except Exception:
            return set()
    raw.pop("return", None)
    result: set[type] = set()
    for hint in raw.values():
        unwrapped = Container._unwrap_optional(hint)
        if unwrapped is not None:
            result.add(unwrapped)
    return result


def _collect_needed_types(module: Module) -> set[type]:
    extra_ns = {t.__name__: t for t in module.dependencies}
    needed: set[type] = set()
    for item in module.providers:
        provider = _normalize_provider(item)
        extra_ns[provider.provide.__name__] = provider.provide
    for item in module.providers:
        provider = _normalize_provider(item)
        if isinstance(provider, ClassProvider) and provider.use_class is not None:
            needed.update(_get_init_hint_types(provider.use_class, extra_ns))
        elif isinstance(provider, ExistingProvider):
            needed.add(provider.use_existing)
    return needed


def _register_provider(container: Container, provider: Provider) -> None:
    match provider:
        case ValueProvider(provide=iface, use_value=val):
            container.instance(iface, val)
        case FactoryProvider(provide=iface, use_factory=fn, scope=scope):
            if scope == Scope.SINGLETON:
                _cached: list[object] = []

                def memoized(
                    c: Container,
                    _fn: Callable[[Container], object] = fn,
                ) -> object:
                    if _cached:
                        return _cached[0]
                    result = _fn(c)
                    _cached.append(result)
                    return result

                container.factory(iface, memoized)
            else:
                container.factory(iface, fn)
        case ExistingProvider(provide=iface, use_existing=target):
            container.factory(iface, lambda c, _t=target: c.resolve(_t))
        case ClassProvider(provide=iface, use_class=impl, scope=scope):
            assert impl is not None  # guaranteed by __post_init__
            if scope == Scope.SINGLETON:
                container.singleton(iface, impl)
            else:
                container.register(iface, impl)


class ApplicationContext:
    """Composes modules with boundary enforcement."""

    def __init__(
        self,
        modules: list[Module],
        globals: list[Provider | type] | None = None,
        event_backend: AsyncEventBackend | None = None,
    ) -> None:
        self._modules = modules
        self._globals = globals or []
        self._event_backend = event_backend
        self._container = Container()
        self._module_containers: dict[str, Container] = {}
        self._provider_to_module: dict[type, str] = {}
        self._export_registry: dict[type, str] = {}
        self._public_types: set[type] = set()
        self._managed_instances: list[object] = []
        self._event_registry: dict[str, type] = {}
        self._handler_registry: dict[str, type[EventHandler]] = {}
        self._boot()

    def _boot(self) -> None:
        # 1. Build export registry and public set from providers
        for module in self._modules:
            for item in module.providers:
                provider = _normalize_provider(item)
                if provider.export:
                    if provider.provide in self._export_registry:
                        raise AmbiguousExportError(
                            provider.provide,
                            self._export_registry[provider.provide],
                            module.name,
                        )
                    self._export_registry[provider.provide] = module.name
                if provider.public:
                    self._public_types.add(provider.provide)

        # 2. Collect global types for dependency validation
        global_types: set[type] = set()
        for item in self._globals:
            provider = _normalize_provider(item)
            global_types.add(provider.provide)
            if provider.public:
                self._public_types.add(provider.provide)

        # 3. Validate every dependency is satisfied by some export or global
        for module in self._modules:
            for dep_type in module.dependencies:
                if dep_type not in self._export_registry and dep_type not in global_types:
                    raise UnresolvedDependencyError(
                        module_name=module.name,
                        dependency_type=dep_type,
                        available_exports=self._export_registry,
                    )

        # 4. Detect cycles in the dependency graph
        self._detect_dependency_cycles(self._modules, self._export_registry)

        # 5. Register globals
        for item in self._globals:
            _register_provider(self._container, _normalize_provider(item))

        # 6. Register providers from all modules
        for module in self._modules:
            for item in module.providers:
                provider = _normalize_provider(item)
                _register_provider(self._container, provider)
                self._provider_to_module[provider.provide] = module.name

        # 7. Build per-module containers
        for module in self._modules:
            self._module_containers[module.name] = self._build_module_container(module)

        # 8. Warn about dead code
        for warning in self.analyze():
            logger.warning(warning)

        # 9. Event system + managed instances
        self._boot_event_system()
        self._collect_managed_instances()

    def _build_module_container(
        self,
        module: Module,
    ) -> Container:
        mod_container = Container()

        # Globals
        for item in self._globals:
            _register_provider(mod_container, _normalize_provider(item))

        # Own providers
        for item in module.providers:
            _register_provider(mod_container, _normalize_provider(item))

        # Dependencies — resolve each port from the main container
        for dep_type in module.dependencies:
            instance = self._container.resolve(dep_type)
            mod_container.instance(dep_type, instance)

        return mod_container

    def _detect_dependency_cycles(
        self,
        modules: list[Module],
        export_registry: dict[type, str],
    ) -> None:
        # Build graph: module_name -> set of module_names it depends on
        depends_on: dict[str, set[str]] = {}
        for module in modules:
            deps: set[str] = set()
            for dep_type in module.dependencies:
                provider_module = export_registry.get(dep_type)
                if provider_module and provider_module != module.name:
                    deps.add(provider_module)
            depends_on[module.name] = deps

        # DFS cycle detection
        def _visit(name: str, path: list[str], visited: set[str]) -> None:
            if name in path:
                cycle = path[path.index(name) :] + [name]
                raise CircularDependencyInModulesError(cycle)
            if name in visited:
                return
            path.append(name)
            for dep in depends_on.get(name, set()):
                _visit(dep, path, visited)
            path.pop()
            visited.add(name)

        visited: set[str] = set()
        for module in modules:
            _visit(module.name, [], visited)

    def analyze(self) -> list[str]:
        from spryx_di.analysis import analyze

        return analyze(self)

    def _boot_event_system(self) -> None:
        from spryx_di.events.bus import EventBus
        from spryx_di.events.handler import EventHandler
        from spryx_di.events.listener import ListenerScope

        all_listeners: list[EventListener] = []
        for module in self._modules:
            for listener in module.listeners:
                if not issubclass(listener.handler, EventHandler):
                    raise InvalidListenerError(listener.handler.__name__)

                if listener.scope == ListenerScope.ASYNC and self._event_backend is None:
                    raise MissingEventBackendError(module.name, listener.handler.__name__)

                all_listeners.append(listener)

        if not all_listeners:
            return

        event_bus = EventBus(
            container=self._container,
            async_backend=self._event_backend,
        )
        self._container.instance(EventBus, event_bus)

        for listener in all_listeners:
            event_bus.register_handler(
                event_type=listener.event,
                handler_type=listener.handler,
                scope=listener.scope,
            )
            event_key = f"{listener.event.__module__}.{listener.event.__qualname__}"
            handler_key = f"{listener.handler.__module__}.{listener.handler.__qualname__}"
            self._event_registry[event_key] = listener.event
            self._handler_registry[handler_key] = listener.handler

    def resolve(self, type_: type[T]) -> T:
        return self._container.resolve(type_)

    def resolve_within(self, module: Module, type_: type[T]) -> T:
        mod_container = self._module_containers.get(module.name)
        if mod_container is None:
            msg = f"Module '{module.name}' is not registered in the ApplicationContext."
            raise ValueError(msg)

        owner = self._provider_to_module.get(type_)
        if owner is not None and owner != module.name and type_ not in set(module.dependencies):
            owner_exports = {t for t, m in self._export_registry.items() if m == owner}
            raise ModuleBoundaryError(
                type_=type_,
                module_name=module.name,
                owner_module=owner,
                exported=owner_exports,
            )

        return mod_container.resolve(type_)

    @property
    def container(self) -> Container:
        return self._container

    @property
    def event_registry(self) -> dict[str, type]:
        return self._event_registry

    @property
    def handler_registry(self) -> dict[str, type[EventHandler]]:
        return self._handler_registry

    def is_public(self, type_: type) -> bool:
        return type_ in self._public_types

    def _collect_managed_instances(self) -> None:
        seen: set[int] = set()
        for obj in self._container._instances.values():
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if hasattr(obj, "__aexit__") or hasattr(obj, "aclose") or hasattr(obj, "close"):
                self._managed_instances.append(obj)

    def on_shutdown(self, hook: ShutdownHook) -> None:
        self._container.on_shutdown(hook)

    async def shutdown(self) -> None:
        import asyncio

        for module in reversed(self._modules):
            if module.on_destroy is not None:
                mod_container = self._module_containers[module.name]
                result = module.on_destroy(mod_container)
                if asyncio.iscoroutine(result):
                    await result

        for instance in reversed(self._managed_instances):
            aexit = getattr(instance, "__aexit__", None)
            aclose = getattr(instance, "aclose", None)
            close = getattr(instance, "close", None)

            if callable(aexit):
                await aexit(None, None, None)
            elif callable(aclose):
                await aclose()
            elif callable(close):
                result = close()
                if asyncio.iscoroutine(result):
                    await result
        self._managed_instances.clear()

        await self._container.shutdown()

    def create_scope(self) -> ScopedContainer:
        return self._container.create_scope()
