from __future__ import annotations

from spryx_di import ApplicationContext, ClassProvider, Module
from spryx_di.analysis import (
    _check_orphan_providers,
    _check_unconsumed_exports,
    _check_unused_dependencies,
)


class Database:
    pass


class RepoPort:
    pass


class PgRepo(RepoPort):
    pass


class ServicePort:
    pass


class MyService:
    def __init__(self, repo: RepoPort) -> None:
        self.repo = repo


class UnusedService:
    pass


class TestCheckUnusedDependencies:
    def test_warns_for_unused_dependency(self) -> None:
        mod = Module(name="a", providers=[], dependencies=[RepoPort])
        # Need to create a valid context so RepoPort is exported
        exporter = Module(
            name="exporter",
            providers=[ClassProvider(provide=RepoPort, use_class=PgRepo, export=True)],
        )
        ctx = ApplicationContext(modules=[exporter, mod])
        warnings = _check_unused_dependencies(ctx._modules)
        assert any("RepoPort" in w and "a" in w for w in warnings)

    def test_no_warning_when_dependency_used(self) -> None:
        exporter = Module(
            name="exporter",
            providers=[ClassProvider(provide=RepoPort, use_class=PgRepo, export=True)],
        )
        consumer = Module(
            name="consumer",
            providers=[ClassProvider(provide=MyService)],
            dependencies=[RepoPort],
        )
        ctx = ApplicationContext(modules=[exporter, consumer])
        warnings = _check_unused_dependencies(ctx._modules)
        consumer_warnings = [w for w in warnings if "consumer" in w]
        assert len(consumer_warnings) == 0


class TestCheckUnconsumedExports:
    def test_warns_for_unconsumed_export(self) -> None:
        mod = Module(
            name="billing",
            providers=[ClassProvider(provide=RepoPort, use_class=PgRepo, export=True)],
        )
        ctx = ApplicationContext(modules=[mod])
        warnings = _check_unconsumed_exports(ctx)
        assert any("RepoPort" in w and "billing" in w for w in warnings)

    def test_no_warning_when_export_consumed(self) -> None:
        exporter = Module(
            name="exporter",
            providers=[ClassProvider(provide=RepoPort, use_class=PgRepo, export=True)],
        )
        consumer = Module(
            name="consumer",
            providers=[ClassProvider(provide=MyService)],
            dependencies=[RepoPort],
        )
        ctx = ApplicationContext(modules=[exporter, consumer])
        warnings = _check_unconsumed_exports(ctx)
        assert len(warnings) == 0


class TestCheckOrphanProviders:
    def test_warns_for_orphan(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=UnusedService)],
        )
        warnings = _check_orphan_providers([mod])
        assert any("UnusedService" in w and "orphan" in w for w in warnings)

    def test_no_warning_for_exported(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=RepoPort, use_class=PgRepo, export=True)],
        )
        warnings = _check_orphan_providers([mod])
        assert len(warnings) == 0

    def test_no_warning_for_public(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=MyService, public=True)],
        )
        warnings = _check_orphan_providers([mod])
        assert len(warnings) == 0

    def test_no_warning_when_used_internally(self) -> None:
        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=RepoPort, use_class=PgRepo),
                ClassProvider(provide=MyService, export=True),
            ],
        )
        warnings = _check_orphan_providers([mod])
        assert len(warnings) == 0


class TestAnalyze:
    def test_returns_all_warnings(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=UnusedService)],
        )
        ctx = ApplicationContext(modules=[mod])
        warnings = ctx.analyze()
        assert any("orphan" in w for w in warnings)

    def test_clean_context_returns_empty(self) -> None:
        ctx = ApplicationContext(modules=[])
        assert ctx.analyze() == []
