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
    CircularDependencyError,
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
        elif isinstance(provider, FactoryProvider):
            if provider.deps:
                needed.update(provider.deps.values())
            else:
                needed.update(_get_init_hint_types(provider.provide, extra_ns))
        elif isinstance(provider, ExistingProvider):
            needed.add(provider.use_existing)
    return needed


def _detect_provider_cycles(
    modules: list[Module],
    globals: list[Provider | type],
) -> None:
    all_providers: list[Provider] = []
    extra_ns: dict[str, type] = {}

    for item in globals:
        p = _normalize_provider(item)
        all_providers.append(p)
        extra_ns[p.provide.__name__] = p.provide

    for module in modules:
        for dep_type in module.dependencies:
            extra_ns[dep_type.__name__] = dep_type
        for item in module.providers:
            p = _normalize_provider(item)
            all_providers.append(p)
            extra_ns[p.provide.__name__] = p.provide

    registered: set[type] = {p.provide for p in all_providers}

    depends_on: dict[type, set[type]] = {}
    for provider in all_providers:
        provider_deps: set[type] = set()
        if isinstance(provider, ClassProvider) and provider.use_class is not None:
            for hint in _get_init_hint_types(provider.use_class, extra_ns):
                if hint in registered:
                    provider_deps.add(hint)
        elif isinstance(provider, FactoryProvider):
            if provider.deps:
                for dep_type in provider.deps.values():
                    if dep_type in registered:
                        provider_deps.add(dep_type)
            else:
                for hint in _get_init_hint_types(provider.provide, extra_ns):
                    if hint in registered:
                        provider_deps.add(hint)
        elif isinstance(provider, ExistingProvider) and provider.use_existing in registered:
            provider_deps.add(provider.use_existing)
        depends_on[provider.provide] = provider_deps

    visited: set[type] = set()

    def _visit(node: type, path: list[type]) -> None:
        if node in path:
            cycle = path[path.index(node) :] + [node]
            raise CircularDependencyError(cycle)
        if node in visited:
            return
        path.append(node)
        for dep in depends_on.get(node, set()):
            _visit(dep, path)
        path.pop()
        visited.add(node)

    for t in depends_on:
        _visit(t, [])


def _build_factory(fp: FactoryProvider) -> Callable[[Container], object]:
    cls = fp.provide
    deps = fp.deps
    args = fp.args

    def factory(c: Container) -> object:
        kwargs: dict[str, object] = {}
        for name, dep_type in deps.items():
            kwargs[name] = c.resolve(dep_type)
        for name, fn in args.items():
            kwargs[name] = fn(c)
        return cls(**kwargs)

    return factory


def _register_provider(container: Container, provider: Provider) -> None:
    match provider:
        case ValueProvider(provide=iface, use_value=val):
            container.instance(iface, val)
        case FactoryProvider(provide=iface, scope=scope) as fp:
            fn = fp.use_factory or _build_factory(fp)
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
        self._boot_container = Container()
        self._container = self._boot_container
        self._module_containers: dict[str, Container] = {}
        self._provider_to_module: dict[type, str] = {}
        self._export_registry: dict[type, str] = {}
        self._managed_instances: list[object] = []
        self._event_registry: dict[str, type] = {}
        self._handler_registry: dict[str, type[EventHandler]] = {}
        self._boot()

    def _boot(self) -> None:
        # 1. Build export registry from providers
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

        # 2. Collect global types for dependency validation
        global_types: set[type] = set()
        for item in self._globals:
            provider = _normalize_provider(item)
            global_types.add(provider.provide)

        # 3. Validate every dependency is satisfied by some export or global
        for module in self._modules:
            for dep_type in module.dependencies:
                if dep_type not in self._export_registry and dep_type not in global_types:
                    raise UnresolvedDependencyError(
                        module_name=module.name,
                        dependency_type=dep_type,
                        available_exports=self._export_registry,
                    )

        # 4. Warn about cycles in the module dependency graph
        for cycle in self._detect_dependency_cycles(self._modules, self._export_registry):
            chain = " → ".join(cycle)
            logger.warning(
                "Circular dependency detected between modules: %s. "
                "This works but may indicate tight coupling. "
                "Consider using the event bus to break the cycle if it grows.",
                chain,
            )

        # 5. Detect circular dependencies between providers (fail-fast)
        _detect_provider_cycles(self._modules, self._globals)

        # 6. Register globals
        for item in self._globals:
            _register_provider(self._boot_container, _normalize_provider(item))

        # 7. Register providers from all modules
        for module in self._modules:
            for item in module.providers:
                provider = _normalize_provider(item)
                _register_provider(self._boot_container, provider)
                self._provider_to_module[provider.provide] = module.name

        # 8. Build per-module containers
        for module in self._modules:
            self._module_containers[module.name] = self._build_module_container(module)

        # 8b. Eagerly resolve exported ExistingProviders and pin as instances
        #     so the lazy factory (which re-resolves on every call) is replaced.
        for module in self._modules:
            for item in module.providers:
                provider = _normalize_provider(item)
                if not (isinstance(provider, ExistingProvider) and provider.export):
                    continue
                resolved = self._boot_container.resolve(provider.use_existing)
                self._boot_container._factories.pop(provider.provide, None)
                self._boot_container._instances[provider.provide] = resolved

        # 8c. Eagerly resolve all providers in each module container to
        #     fail-fast on missing dependencies instead of deferring to runtime.
        for module in self._modules:
            mod_container = self._module_containers[module.name]
            for item in module.providers:
                provider = _normalize_provider(item)
                mod_container.resolve(provider.provide)

        # 9. Warn about dead code
        for warning in self.analyze():
            logger.warning(warning)

        # 10. Event system + managed instances
        self._boot_event_system()
        self._collect_managed_instances()

        # 11. Build public container (only globals + exports).
        #     The boot container keeps all providers for internal use
        #     (EventBus handler resolution, module containers, etc.).
        self._container = self._build_public_container()

    def _build_public_container(self) -> Container:
        from spryx_di.events.bus import EventBus

        allowed: set[type] = set()
        for item in self._globals:
            allowed.add(_normalize_provider(item).provide)
        allowed.update(self._export_registry)
        if self._boot_container.has(EventBus):
            allowed.add(EventBus)

        pub = Container(auto_wire=False)
        transient_types = self._transient_exported_types()
        for t in allowed:
            if t in self._boot_container._instances:
                pub._instances[t] = self._boot_container._instances[t]
            elif t in transient_types:
                pub._factories[t] = lambda c, _t=t: self._boot_container.resolve(_t)
            else:
                instance = self._boot_container.resolve(t)
                pub._instances[t] = instance
        return pub

    def _transient_exported_types(self) -> set[type]:
        result: set[type] = set()
        for module in self._modules:
            for item in module.providers:
                provider = _normalize_provider(item)
                if (
                    provider.export
                    and isinstance(provider, (ClassProvider, FactoryProvider))
                    and provider.scope == Scope.TRANSIENT
                ):
                    result.add(provider.provide)
        return result

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

        # Dependencies — resolve each port from the boot container
        for dep_type in module.dependencies:
            instance = self._boot_container.resolve(dep_type)
            mod_container.instance(dep_type, instance)

        return mod_container

    def _detect_dependency_cycles(
        self,
        modules: list[Module],
        export_registry: dict[type, str],
    ) -> list[list[str]]:
        depends_on: dict[str, set[str]] = {}
        for module in modules:
            deps: set[str] = set()
            for dep_type in module.dependencies:
                provider_module = export_registry.get(dep_type)
                if provider_module and provider_module != module.name:
                    deps.add(provider_module)
            depends_on[module.name] = deps

        cycles: list[list[str]] = []

        def _visit(name: str, path: list[str], visited: set[str]) -> None:
            if name in path:
                cycle = path[path.index(name) :] + [name]
                cycles.append(cycle)
                return
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

        return cycles

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
            container=self._boot_container,
            async_backend=self._event_backend,
        )
        self._boot_container.instance(EventBus, event_bus)

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

    def _collect_managed_instances(self) -> None:
        seen: set[int] = set()
        for obj in self._boot_container._instances.values():
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if hasattr(obj, "__aexit__") or hasattr(obj, "aclose") or hasattr(obj, "close"):
                self._managed_instances.append(obj)

    def on_shutdown(self, hook: ShutdownHook) -> None:
        self._boot_container.on_shutdown(hook)

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

        await self._boot_container.shutdown()

    def create_scope(self) -> ScopedContainer:
        return self._container.create_scope()
