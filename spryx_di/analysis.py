from __future__ import annotations

from typing import TYPE_CHECKING

from spryx_di.module import _collect_needed_types, _normalize_provider
from spryx_di.provider import ExistingProvider

if TYPE_CHECKING:
    from spryx_di.module import ApplicationContext, Module


def _check_unused_dependencies(modules: list[Module]) -> list[str]:
    warnings: list[str] = []
    for module in modules:
        if not module.dependencies:
            continue
        needed_types = _collect_needed_types(module)
        for dep_type in module.dependencies:
            if dep_type not in needed_types:
                warnings.append(
                    f"Module '{module.name}' declares dependency '{dep_type.__name__}' "
                    f"but none of its providers depend on it. "
                    f"Consider removing it from dependencies."
                )
    return warnings


def _check_unconsumed_exports(ctx: ApplicationContext) -> list[str]:
    warnings: list[str] = []
    all_dependencies: set[type] = set()
    for module in ctx._modules:
        all_dependencies.update(module.dependencies)
    for export_type, module_name in ctx._export_registry.items():
        if export_type not in all_dependencies:
            warnings.append(
                f"Module '{module_name}' exports '{export_type.__name__}' "
                f"but no module depends on it. "
                f"Consider removing export=True from the provider."
            )
    return warnings


def _is_needed(provider_type: type, needed_types: set[type]) -> bool:
    if provider_type in needed_types:
        return True
    for hint in needed_types:
        if not isinstance(hint, type):
            continue
        try:
            if issubclass(provider_type, hint):
                return True
        except TypeError:
            continue
    return False


def _check_orphan_providers(modules: list[Module]) -> list[str]:
    warnings: list[str] = []
    for module in modules:
        if not module.providers:
            continue
        needed_types = _collect_needed_types(module)

        existing_targets: set[type] = set()
        for item in module.providers:
            p = _normalize_provider(item)
            if isinstance(p, ExistingProvider):
                existing_targets.add(p.use_existing)

        for item in module.providers:
            provider = _normalize_provider(item)
            if provider.export:
                continue
            if provider.provide in existing_targets:
                continue
            if not _is_needed(provider.provide, needed_types):
                warnings.append(
                    f"Module '{module.name}' has orphan provider "
                    f"'{provider.provide.__name__}' "
                    f"(not used, not exported). "
                    f"Consider removing it."
                )
    return warnings


def analyze(ctx: ApplicationContext) -> list[str]:
    warnings: list[str] = []
    warnings.extend(_check_unused_dependencies(ctx._modules))
    warnings.extend(_check_unconsumed_exports(ctx))
    warnings.extend(_check_orphan_providers(ctx._modules))
    return warnings
