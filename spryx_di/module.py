from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from spryx_di.container import Container
from spryx_di.errors import (
    CircularModuleError,
    ExportWithoutProviderError,
    ModuleBoundaryError,
    ModuleNotFoundError,
)
from spryx_di.provider import _MISSING, ForwardRef, Provider, Scope

logger = logging.getLogger("spryx_di")


@dataclass
class Module:
    """Declarative module definition inspired by NestJS."""

    name: str
    providers: list[Provider | type] = field(default_factory=list)
    exports: list[type] = field(default_factory=list)
    imports: list[Module | ForwardRef] = field(default_factory=list)
    on_destroy: Any | None = None  # Callable[[Container], Awaitable[None]] | None


def _register_provider(container: Container, provider: Provider) -> None:
    if provider.use_value is not _MISSING:
        container.instance(provider.provide, provider.use_value)
    elif provider.use_factory is not None:
        container.factory(provider.provide, provider.use_factory)
    elif provider.use_class is not None:
        if provider.scope == Scope.SINGLETON:
            container.singleton(provider.provide, provider.use_class)
        else:
            container.register(provider.provide, provider.use_class)


def _normalize_provider(item: Provider | type) -> Provider:
    if isinstance(item, type):
        return Provider(provide=item, use_class=item)
    return item


def _detect_circular_modules(
    modules: list[Module],
    resolved_imports: dict[str, list[Module]],
    forward_ref_edges: set[tuple[str, str]],
) -> None:
    def _visit(name: str, path: list[str], visited: set[str]) -> None:
        if name in path:
            cycle = path[path.index(name) :] + [name]
            raise CircularModuleError(cycle)
        if name in visited:
            return
        path.append(name)
        for imp in resolved_imports.get(name, []):
            if (name, imp.name) not in forward_ref_edges:
                _visit(imp.name, path, visited)
        path.pop()
        visited.add(name)

    visited: set[str] = set()
    for mod in modules:
        _visit(mod.name, [], visited)

    for src, dst in forward_ref_edges:
        if (dst, src) in forward_ref_edges or _has_path(
            dst, src, resolved_imports, forward_ref_edges
        ):
            logger.warning(
                "Circular dependency between modules '%s' <-> '%s' "
                "(resolved via forward_ref). Consider extracting shared types "
                "into a separate module if this grows.",
                src,
                dst,
            )


def _has_path(
    start: str,
    end: str,
    resolved_imports: dict[str, list[Module]],
    forward_ref_edges: set[tuple[str, str]],
) -> bool:
    visited: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current == end:
            return True
        if current in visited:
            continue
        visited.add(current)
        for imp in resolved_imports.get(current, []):
            stack.append(imp.name)
    return False


class ApplicationContext:
    """Composes modules with boundary enforcement."""

    def __init__(
        self,
        modules: list[Module],
        globals: list[Provider] | None = None,
    ) -> None:
        self._modules = modules
        self._globals = globals or []
        self._container = Container()
        self._module_containers: dict[str, Container] = {}
        self._provider_to_module: dict[type, str] = {}
        self._exported_types: dict[str, set[type]] = {}
        self._resolved_imports: dict[str, list[Module]] = {}
        self._forward_ref_edges: set[tuple[str, str]] = set()
        self._managed_instances: list[Any] = []
        self._boot()

    def _boot(self) -> None:
        module_map: dict[str, Module] = {m.name: m for m in self._modules}
        module_ids = {id(m) for m in self._modules}

        for module in self._modules:
            provider_types = {_normalize_provider(p).provide for p in module.providers}
            for export in module.exports:
                if export not in provider_types:
                    raise ExportWithoutProviderError(module.name, export)

        for module in self._modules:
            resolved: list[Module] = []
            for imp in module.imports:
                if isinstance(imp, ForwardRef):
                    target = module_map.get(imp.module_name)
                    if target is None:
                        raise ModuleNotFoundError(module.name, imp.module_name)
                    resolved.append(target)
                    self._forward_ref_edges.add((module.name, imp.module_name))
                elif isinstance(imp, Module):
                    if id(imp) not in module_ids:
                        raise ModuleNotFoundError(module.name, imp.name)
                    resolved.append(imp)
            self._resolved_imports[module.name] = resolved

        _detect_circular_modules(self._modules, self._resolved_imports, self._forward_ref_edges)

        for item in self._globals:
            _register_provider(self._container, _normalize_provider(item))

        for module in self._modules:
            self._exported_types[module.name] = set(module.exports)
            for item in module.providers:
                provider = _normalize_provider(item)
                _register_provider(self._container, provider)
                self._provider_to_module[provider.provide] = module.name

        for module in self._modules:
            self._module_containers[module.name] = self._build_module_container(module)

        self._collect_managed_instances()

    def _build_module_container(self, module: Module) -> Container:
        mod_container = Container()

        for item in self._globals:
            _register_provider(mod_container, _normalize_provider(item))

        for item in module.providers:
            _register_provider(mod_container, _normalize_provider(item))

        for imp in self._resolved_imports[module.name]:
            for export_type in self._exported_types.get(imp.name, set()):
                mod_container.instance(export_type, self._container.resolve(export_type))

        return mod_container

    def resolve(self, type_: type[Any]) -> Any:
        return self._container.resolve(type_)

    def resolve_within(self, module: Module, type_: type[Any]) -> Any:
        mod_container = self._module_containers.get(module.name)
        if mod_container is None:
            raise ModuleNotFoundError("(caller)", module.name)

        owner = self._provider_to_module.get(type_)
        if owner is not None and owner != module.name:
            imported_exports: set[type] = set()
            for imp in self._resolved_imports.get(module.name, []):
                imported_exports |= self._exported_types.get(imp.name, set())

            if type_ not in imported_exports:
                raise ModuleBoundaryError(
                    type_=type_,
                    module_name=module.name,
                    owner_module=owner,
                    exported=self._exported_types.get(owner, set()),
                )

        return mod_container.resolve(type_)

    @property
    def container(self) -> Container:
        return self._container

    def _collect_managed_instances(self) -> None:
        seen: set[int] = set()
        for obj in self._container._instances.values():
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if hasattr(obj, "__aexit__") or hasattr(obj, "aclose") or hasattr(obj, "close"):
                self._managed_instances.append(obj)

    def on_shutdown(self, hook: Any) -> None:
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
            if hasattr(instance, "__aexit__"):
                await instance.__aexit__(None, None, None)
            elif hasattr(instance, "aclose"):
                await instance.aclose()
            elif hasattr(instance, "close"):
                result = instance.close()
                if asyncio.iscoroutine(result):
                    await result
        self._managed_instances.clear()

        await self._container.shutdown()

    def create_scope(self) -> Any:
        return self._container.create_scope()
