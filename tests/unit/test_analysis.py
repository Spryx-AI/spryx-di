from __future__ import annotations

from typing import Protocol, runtime_checkable

from spryx_di import ApplicationContext, ClassProvider, ExistingProvider, FactoryProvider, Module
from spryx_di.analysis import (
    _check_orphan_providers,
    _check_unconsumed_exports,
    _check_unused_dependencies,
)
from spryx_di.container import Container


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


class EvaluatorAbc:
    pass


class DeterministicEvaluator(EvaluatorAbc):
    pass


class Pipeline:
    def __init__(self, evaluator: EvaluatorAbc) -> None:
        self.evaluator = evaluator


class WebhookRepo:
    pass


class DriveSubscription:
    def __init__(self, repo: WebhookRepo) -> None:
        self.repo = repo


@runtime_checkable
class HasName(Protocol):
    name: str


class ProtocolConsumer:
    def __init__(self, item: HasName) -> None:
        self.item = item


class Named:
    def __init__(self, name: str) -> None:
        self.name = name


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

    def test_no_warning_for_existing_provider_target(self) -> None:
        """PgRepo is target of ExistingProvider — not orphan."""
        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=PgRepo),
                ExistingProvider(provide=RepoPort, use_existing=PgRepo, export=True),
            ],
        )
        warnings = _check_orphan_providers([mod])
        assert not any("PgRepo" in w for w in warnings)

    def test_warns_for_unused_existing_provider(self) -> None:
        """ExistingProvider whose port nobody uses is orphan."""

        class UsageReaderPort:
            pass

        class PgUsageReader:
            pass

        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=PgUsageReader),
                ExistingProvider(provide=UsageReaderPort, use_existing=PgUsageReader),
            ],
        )
        warnings = _check_orphan_providers([mod])
        assert any("UsageReaderPort" in w for w in warnings)

    def test_no_warning_for_subclass_satisfying_base_hint(self) -> None:
        """Provider registers concrete, consumer __init__ asks for ABC."""
        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=DeterministicEvaluator),
                ClassProvider(provide=Pipeline, public=True),
            ],
        )
        warnings = _check_orphan_providers([mod])
        assert not any("DeterministicEvaluator" in w for w in warnings)

    def test_no_warning_for_provider_used_by_factory(self) -> None:
        """FactoryProvider's provide type __init__ hints are inspected."""

        def _factory(c: Container) -> DriveSubscription:
            return DriveSubscription(repo=c.resolve(WebhookRepo))

        mod = Module(
            name="drive",
            providers=[
                ClassProvider(provide=WebhookRepo),
                FactoryProvider(provide=DriveSubscription, use_factory=_factory, public=True),
            ],
        )
        warnings = _check_orphan_providers([mod])
        assert not any("WebhookRepo" in w for w in warnings)

    def test_no_crash_with_protocol_hint(self) -> None:
        """Protocols with non-method members don't support issubclass()."""
        mod = Module(
            name="test",
            providers=[
                ClassProvider(provide=ProtocolConsumer, public=True),
                ClassProvider(provide=Named),
            ],
        )
        # Without the try/except in _is_needed, this raises:
        # TypeError: Protocols with non-method members don't support issubclass()
        _check_orphan_providers([mod])

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
