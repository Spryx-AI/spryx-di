from __future__ import annotations

import logging

import pytest

from spryx_di import (
    AmbiguousExportError,
    ApplicationContext,
    CircularDependencyError,
    ClassProvider,
    ExistingProvider,
    FactoryProvider,
    Module,
    ModuleBoundaryError,
    Scope,
    UnresolvedDependencyError,
    ValueProvider,
    public,
)


class Database:
    pass


class TeamRepository:
    pass


class PgTeamRepository(TeamRepository):
    def __init__(self, db: Database) -> None:
        self.db = db


class TeamReader:
    pass


class PgTeamReader(TeamReader):
    def __init__(self, db: Database) -> None:
        self.db = db


class UserReader:
    pass


class PgUserReader(UserReader):
    pass


class HttpUserReader(UserReader):
    pass


class ConversationRepo:
    pass


class PgConversationRepo(ConversationRepo):
    pass


class ListHandler:
    def __init__(self, reader: TeamReader) -> None:
        self.reader = reader


class BillingGateway:
    pass


class StripeBillingGateway(BillingGateway):
    pass


# --- Ports (ABCs/Protocols used as dependency types) ---


class TeamReaderPort:
    """Port for cross-module dependency of TeamReader."""

    pass


class BillingGatewayPort:
    """Port for cross-module dependency of BillingGateway."""

    pass


class TestModuleDefinition:
    def test_define_module(self) -> None:
        module = Module(
            name="identity",
            providers=[
                ClassProvider(
                    provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON, export=True
                ),
            ],
        )
        assert module.name == "identity"
        assert len(module.providers) == 1

    def test_class_provider_defaults_use_class_to_provide(self) -> None:
        p = ClassProvider(provide=PgTeamReader)
        assert p.use_class is PgTeamReader
        assert p.scope == Scope.SINGLETON
        assert p.export is False

        module = Module(
            name="test",
            providers=[ClassProvider(provide=PgTeamReader)],
        )
        assert len(module.providers) == 1

    def test_normalize_provider_creates_non_exported_class_provider(self) -> None:
        """Bare type in providers list creates ClassProvider with export=False."""
        module = Module(
            name="test",
            providers=[PgTeamReader],
        )
        ctx = ApplicationContext(modules=[module])
        reader = ctx.resolve(PgTeamReader)
        assert isinstance(reader, PgTeamReader)


class TestProvider:
    def test_use_class(self) -> None:
        p = ClassProvider(provide=TeamReader, use_class=PgTeamReader)
        assert p.provide == TeamReader
        assert p.use_class == PgTeamReader
        assert p.scope == Scope.SINGLETON
        assert p.export is False

    def test_use_value(self) -> None:
        db = Database()
        p = ValueProvider(provide=Database, use_value=db)
        assert p.provide == Database
        assert p.export is False

    def test_use_factory(self) -> None:
        p = FactoryProvider(
            provide=TeamReader,
            use_factory=lambda c: PgTeamReader(c.resolve(Database)),
        )
        assert p.provide == TeamReader
        assert p.export is False

    def test_use_existing(self) -> None:
        p = ExistingProvider(provide=TeamReader, use_existing=PgTeamReader)
        assert p.provide == TeamReader
        assert p.use_existing == PgTeamReader
        assert p.export is False

    def test_export_flag(self) -> None:
        p = ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True)
        assert p.export is True

        p2 = FactoryProvider(provide=TeamReader, use_factory=lambda c: None, export=True)
        assert p2.export is True

        p3 = ValueProvider(provide=Database, use_value=Database(), export=True)
        assert p3.export is True

        p4 = ExistingProvider(provide=TeamReader, use_existing=PgTeamReader, export=True)
        assert p4.export is True


class TestApplicationContext:
    def test_compose_modules(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True),
                ClassProvider(provide=UserReader, use_class=PgUserReader, export=True),
            ],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)

    def test_globals_available_to_modules(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True),
            ],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)

    def test_cross_module_dependencies_via_ports(self) -> None:
        """Modules declare dependencies on ports (types), not other modules."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        conversations = Module(
            name="conversations",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, conversations],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        # The dependency port is available in the module container
        port = ctx.resolve_within(conversations, TeamReaderPort)
        assert isinstance(port, PgTeamReader)

    def test_provider_without_export_not_visible_to_other_modules(self) -> None:
        """Providers without export=True should not be visible to other modules."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),  # not exported
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        # Can access exported port
        port = ctx.resolve_within(consumer, TeamReaderPort)
        assert isinstance(port, PgTeamReader)

        # Cannot access non-exported provider from another module
        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(consumer, TeamReader)


class TestModuleBoundary:
    def test_boundary_violation_raises(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        conversations = Module(
            name="conversations",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, conversations],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        with pytest.raises(ModuleBoundaryError) as exc_info:
            ctx.resolve_within(conversations, TeamRepository)
        assert "TeamRepository" in str(exc_info.value)
        assert "identity" in str(exc_info.value)
        assert "not exported" in str(exc_info.value)


class TestUnresolvedDependency:
    def test_unresolved_dependency_raises(self) -> None:
        mod = Module(
            name="consumer",
            providers=[],
            dependencies=[TeamReaderPort],
        )
        with pytest.raises(UnresolvedDependencyError) as exc_info:
            ApplicationContext(modules=[mod])
        assert "TeamReaderPort" in str(exc_info.value)
        assert "consumer" in str(exc_info.value)

    def test_unresolved_dependency_shows_available_exports(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            dependencies=[BillingGatewayPort],
        )
        db = Database()
        with pytest.raises(UnresolvedDependencyError) as exc_info:
            ApplicationContext(
                modules=[identity, consumer],
                globals=[ValueProvider(provide=Database, use_value=db)],
            )
        assert "BillingGatewayPort" in str(exc_info.value)
        assert "TeamReaderPort" in str(exc_info.value)

    def test_dependency_satisfied_by_global_is_valid(self) -> None:
        """Globals serve as provider of last resort for dependencies."""
        consumer = Module(
            name="consumer",
            providers=[],
            dependencies=[Database],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        resolved = ctx.resolve_within(consumer, Database)
        assert resolved is db


class TestAmbiguousExport:
    def test_ambiguous_export_raises(self) -> None:
        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=TeamReaderPort, export=True)],
        )
        mod_b = Module(
            name="b",
            providers=[ClassProvider(provide=TeamReaderPort, export=True)],
        )
        with pytest.raises(AmbiguousExportError) as exc_info:
            ApplicationContext(modules=[mod_a, mod_b])
        assert "TeamReaderPort" in str(exc_info.value)
        assert "a" in str(exc_info.value)
        assert "b" in str(exc_info.value)


class TestCircularDependencies:
    def test_direct_circular_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """A depends on B, B depends on A → warning, not error."""
        mod_a = Module(
            name="a",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
            dependencies=[BillingGatewayPort],
        )
        mod_b = Module(
            name="b",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
                ExistingProvider(
                    provide=BillingGatewayPort, use_existing=BillingGateway, export=True
                ),
            ],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            ctx = ApplicationContext(
                modules=[mod_a, mod_b],
                globals=[ValueProvider(provide=Database, use_value=db)],
            )
        cycle_warnings = [r for r in caplog.records if "Circular dependency" in r.message]
        assert len(cycle_warnings) >= 1
        assert "a" in cycle_warnings[0].message
        assert "b" in cycle_warnings[0].message
        assert ctx.container is not None

    def test_indirect_circular_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """A→B→C→A cycle emits warning, boots successfully."""

        class PortA:
            pass

        class PortB:
            pass

        class PortC:
            pass

        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=PortA, export=True)],
            dependencies=[PortC],
        )
        mod_b = Module(
            name="b",
            providers=[ClassProvider(provide=PortB, export=True)],
            dependencies=[PortA],
        )
        mod_c = Module(
            name="c",
            providers=[ClassProvider(provide=PortC, export=True)],
            dependencies=[PortB],
        )
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            ctx = ApplicationContext(modules=[mod_a, mod_b, mod_c])
        cycle_warnings = [r for r in caplog.records if "Circular dependency" in r.message]
        assert len(cycle_warnings) >= 1
        assert "a" in cycle_warnings[0].message
        assert ctx.container is not None

    def test_provider_circular_dependency_detected_at_boot(self) -> None:
        """A.__init__ needs B, B.__init__ needs A → error at boot, not at resolve."""

        class ServiceA:
            def __init__(self, b: ServiceB) -> None:
                self.b = b

        class ServiceB:
            def __init__(self, a: ServiceA) -> None:
                self.a = a

        mod = Module(
            name="circular",
            providers=[
                ClassProvider(provide=ServiceA),
                ClassProvider(provide=ServiceB),
            ],
        )
        with pytest.raises(CircularDependencyError):
            ApplicationContext(modules=[mod])

    def test_no_cycle_when_unidirectional(self) -> None:
        """A→B is fine when B doesn't depend on A."""
        mod_a = Module(
            name="a",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        mod_b = Module(
            name="b",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[mod_a, mod_b],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        assert isinstance(ctx.resolve(BillingGateway), StripeBillingGateway)


class TestDependencyResolution:
    def test_dependency_port_resolved_in_module_container(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        port = ctx.resolve_within(consumer, TeamReaderPort)
        assert isinstance(port, PgTeamReader)

    def test_module_container_no_access_to_undeclared_ports(self) -> None:
        """A module can't access exports it didn't declare in dependencies."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        billing = Module(
            name="billing",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
                ExistingProvider(
                    provide=BillingGatewayPort, use_existing=BillingGateway, export=True
                ),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            dependencies=[TeamReaderPort],  # only depends on TeamReaderPort, not BillingGatewayPort
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, billing, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        # Can access declared dependency
        port = ctx.resolve_within(consumer, TeamReaderPort)
        assert isinstance(port, PgTeamReader)

        # Cannot access undeclared dependency
        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(consumer, BillingGatewayPort)

    def test_dependency_port_is_same_singleton(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        first = ctx.resolve_within(consumer, TeamReaderPort)
        second = ctx.resolve_within(consumer, TeamReaderPort)
        assert first is second


class TestUseFactory:
    def test_factory_provider(self) -> None:
        db = Database()
        identity = Module(
            name="identity",
            providers=[
                FactoryProvider(
                    provide=TeamReader,
                    use_factory=lambda c: PgTeamReader(c.resolve(Database)),
                    export=True,
                ),
            ],
        )
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)
        assert reader.db is db

    def test_factory_singleton_caches_result(self) -> None:
        call_count = 0

        def counting_factory(c: object) -> Database:
            nonlocal call_count
            call_count += 1
            return Database()

        mod = Module(
            name="test",
            providers=[
                FactoryProvider(provide=Database, use_factory=counting_factory),
            ],
        )
        ctx = ApplicationContext(modules=[mod])
        a = ctx.resolve(Database)
        b = ctx.resolve(Database)
        assert a is b
        assert call_count == 1

    def test_factory_transient_creates_new_instances(self) -> None:
        mod = Module(
            name="test",
            providers=[
                FactoryProvider(
                    provide=Database,
                    use_factory=lambda c: Database(),
                    scope=Scope.TRANSIENT,
                ),
            ],
        )
        ctx = ApplicationContext(modules=[mod])
        a = ctx.resolve(Database)
        b = ctx.resolve(Database)
        assert a is not b


class TestFactoryProviderDepsArgs:
    def test_deps_resolves_types(self) -> None:
        db = Database()
        mod = Module(
            name="test",
            providers=[
                FactoryProvider(
                    provide=PgTeamReader,
                    deps={"db": Database},
                    export=True,
                ),
            ],
        )
        ctx = ApplicationContext(
            modules=[mod],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(PgTeamReader)
        assert isinstance(reader, PgTeamReader)
        assert reader.db is db

    def test_deps_and_args_combined(self) -> None:
        class Config:
            def __init__(self, db: Database, table_name: str) -> None:
                self.db = db
                self.table_name = table_name

        db = Database()
        mod = Module(
            name="test",
            providers=[
                FactoryProvider(
                    provide=Config,
                    deps={"db": Database},
                    args={"table_name": lambda c: "users"},
                ),
            ],
        )
        ctx = ApplicationContext(
            modules=[mod],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        config = ctx.resolve(Config)
        assert config.db is db
        assert config.table_name == "users"

    def test_validation_requires_factory_or_deps(self) -> None:
        with pytest.raises(ValueError, match="requires use_factory or deps/args"):
            FactoryProvider(provide=Database)

    def test_validation_rejects_factory_with_deps(self) -> None:
        with pytest.raises(ValueError, match="cannot combine"):
            FactoryProvider(
                provide=Database,
                use_factory=lambda c: Database(),
                deps={"db": Database},
            )

    def test_deps_tracked_by_analyzer(self) -> None:
        """Deps types appear in orphan analysis — no false positives."""
        mod = Module(
            name="test",
            providers=[
                ClassProvider(provide=Database),
                FactoryProvider(
                    provide=PgTeamReader,
                    deps={"db": Database},
                    public=True,
                ),
            ],
        )
        warnings = ApplicationContext(modules=[mod]).analyze()
        assert not any("Database" in w and "orphan" in w for w in warnings)


class TestUseExisting:
    def test_use_existing_resolves_to_target(self) -> None:
        db = Database()
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True),
                ExistingProvider(provide=UserReader, use_existing=TeamReader, export=True),
            ],
        )
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(TeamReader)
        alias = ctx.resolve(UserReader)
        assert isinstance(reader, PgTeamReader)
        assert alias is reader

    def test_use_existing_returns_same_singleton(self) -> None:
        db = Database()
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=UserReader, use_existing=TeamReader),
            ],
        )
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        assert ctx.resolve(UserReader) is ctx.resolve(UserReader)

    def test_use_existing_cross_module(self) -> None:
        db = Database()
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ExistingProvider(provide=UserReader, use_existing=TeamReaderPort),
            ],
            dependencies=[TeamReaderPort],
        )
        ctx = ApplicationContext(
            modules=[identity, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        assert isinstance(ctx.resolve(UserReader), PgTeamReader)


class FakeResource:
    def __init__(self) -> None:
        self.closed = False

    async def __aenter__(self) -> FakeResource:
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.closed = True


class FakeClient:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class TestModuleOnDestroy:
    @pytest.mark.asyncio
    async def test_on_destroy_called_on_shutdown(self) -> None:
        destroyed: list[str] = []

        async def destroy_identity(container: object) -> None:
            destroyed.append("identity")

        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True),
            ],
            on_destroy=destroy_identity,
        )
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=Database())],
        )
        await ctx.shutdown()
        assert destroyed == ["identity"]

    @pytest.mark.asyncio
    async def test_on_destroy_reverse_order(self) -> None:
        order: list[str] = []

        mod_a = Module(name="a", providers=[], on_destroy=lambda _: order.append("a"))
        mod_b = Module(name="b", providers=[], on_destroy=lambda _: order.append("b"))

        ctx = ApplicationContext(modules=[mod_a, mod_b])
        await ctx.shutdown()
        assert order == ["b", "a"]


class TestManagedInstances:
    @pytest.mark.asyncio
    async def test_aexit_called_on_shutdown(self) -> None:
        resource = FakeResource()
        ctx = ApplicationContext(
            modules=[],
            globals=[ValueProvider(provide=FakeResource, use_value=resource)],
        )
        await ctx.shutdown()
        assert resource.closed is True

    @pytest.mark.asyncio
    async def test_aclose_called_on_shutdown(self) -> None:
        client = FakeClient()
        ctx = ApplicationContext(
            modules=[],
            globals=[ValueProvider(provide=FakeClient, use_value=client)],
        )
        await ctx.shutdown()
        assert client.closed is True

    @pytest.mark.asyncio
    async def test_on_destroy_before_managed_instances(self) -> None:

        order: list[str] = []

        class TrackedResource:
            closed = False

            async def aclose(self) -> None:
                self.closed = True
                order.append("resource_closed")

        resource = TrackedResource()

        async def destroy(container: object) -> None:
            order.append("on_destroy")

        mod = Module(
            name="test",
            providers=[ValueProvider(provide=TrackedResource, use_value=resource)],
            on_destroy=destroy,
        )
        ctx = ApplicationContext(modules=[mod])
        await ctx.shutdown()
        assert order == ["on_destroy", "resource_closed"]

    @pytest.mark.asyncio
    async def test_sync_close_called_on_shutdown(self) -> None:
        class SyncCloseable:
            closed = False

            def close(self) -> None:
                self.closed = True

        obj = SyncCloseable()
        ctx = ApplicationContext(
            modules=[],
            globals=[ValueProvider(provide=SyncCloseable, use_value=obj)],
        )
        await ctx.shutdown()
        assert obj.closed is True


class TestApplicationContextHelpers:
    def test_on_shutdown_delegates_to_container(self) -> None:
        ctx = ApplicationContext(modules=[])
        called = False

        def hook() -> None:
            nonlocal called
            called = True

        ctx.on_shutdown(hook)
        import asyncio

        asyncio.run(ctx.shutdown())
        assert called is True

    def test_create_scope(self) -> None:
        ctx = ApplicationContext(modules=[])
        scope = ctx.create_scope()
        assert scope is not None

    def test_container_property(self) -> None:
        ctx = ApplicationContext(modules=[])
        assert ctx.container is not None


class TestDeadCodeWarnings:
    # --- Unused provider warnings ---

    def test_unused_provider_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Provider not exported and not depended on by any other provider in the module."""
        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),  # nobody needs this
                ClassProvider(
                    provide=ConversationRepo, use_class=PgConversationRepo
                ),  # nobody needs this
            ],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(
                modules=[mod],
                globals=[ValueProvider(provide=Database, use_value=Database())],
            )
        unused = [r for r in caplog.records if "orphan provider" in r.message]
        names = {r.message.split("'")[3] for r in unused}
        assert "TeamReader" in names
        assert "ConversationRepo" in names

    def test_exported_provider_no_unused_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Exported provider should NOT trigger unused warning even if no internal consumer."""
        mod = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True),
            ],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(
                modules=[mod],
                globals=[ValueProvider(provide=Database, use_value=Database())],
            )
        unused = [r for r in caplog.records if "orphan provider" in r.message]
        assert len(unused) == 0

    def test_internally_used_provider_no_unused_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Provider consumed by another provider's __init__ should NOT trigger unused warning."""

        class AgentRepository:
            pass

        class CreateAgent:
            def __init__(self, repo: AgentRepository) -> None:
                self.repo = repo

        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=AgentRepository),
                ClassProvider(provide=CreateAgent, export=True),
            ],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(modules=[mod])
        unused = [r for r in caplog.records if "orphan provider" in r.message]
        assert len(unused) == 0

    # --- Unused dependency warnings ---

    def test_unused_dependency_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Module declares a dependency that none of its providers need."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReaderPort, export=True),
            ],
        )
        # consumer declares dependency on TeamReaderPort but has no provider that uses it
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            dependencies=[TeamReaderPort],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(modules=[identity, consumer])
        assert any(
            "consumer" in r.message
            and "TeamReaderPort" in r.message
            and "none of its providers" in r.message
            for r in caplog.records
        )

    def test_unconsumed_export_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Module exports a type but no module depends on it."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReaderPort, export=True),
            ],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(modules=[identity])
        assert any(
            "identity" in r.message
            and "TeamReaderPort" in r.message
            and "no module depends" in r.message
            for r in caplog.records
        )

    def test_no_warning_when_dependency_is_used(self, caplog: pytest.LogCaptureFixture) -> None:
        """No warning when dependency is actually consumed by a provider's __init__."""

        class ServicePort:
            pass

        class MyService(ServicePort):
            pass

        class Consumer:
            def __init__(self, svc: ServicePort) -> None:
                self.svc = svc

        provider_mod = Module(
            name="provider",
            providers=[ClassProvider(provide=ServicePort, use_class=MyService, export=True)],
        )
        consumer_mod = Module(
            name="consumer",
            providers=[ClassProvider(provide=Consumer)],
            dependencies=[ServicePort],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(modules=[provider_mod, consumer_mod])
        unused_dep_warnings = [r for r in caplog.records if "none of its providers" in r.message]
        assert len(unused_dep_warnings) == 0

    def test_no_warning_when_export_is_consumed(self, caplog: pytest.LogCaptureFixture) -> None:
        """No warning when another module depends on the exported type."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReaderPort, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo)],
            dependencies=[TeamReaderPort],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(modules=[identity, consumer])
        unconsumed_warnings = [r for r in caplog.records if "no module depends" in r.message]
        assert len(unconsumed_warnings) == 0

    def test_unused_dependency_with_existing_provider(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Dependency used via ExistingProvider.use_existing should not warn."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader, export=True),
            ],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ExistingProvider(provide=UserReader, use_existing=TeamReaderPort),
            ],
            dependencies=[TeamReaderPort],
        )
        db = Database()
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(
                modules=[identity, consumer],
                globals=[ValueProvider(provide=Database, use_value=db)],
            )
        unused_dep_warnings = [
            r
            for r in caplog.records
            if "none of its providers" in r.message and "consumer" in r.message
        ]
        assert len(unused_dep_warnings) == 0

    def test_public_provider_no_unused_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Public provider should NOT trigger unused warning even if no internal consumer."""
        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, public=True),
            ],
        )
        with caplog.at_level("WARNING", logger="spryx_di"):
            ApplicationContext(
                modules=[mod],
                globals=[ValueProvider(provide=Database, use_value=Database())],
            )
        unused = [r for r in caplog.records if "orphan provider" in r.message]
        assert len(unused) == 0


class TestPublicHelper:
    def test_public_creates_class_providers(self) -> None:
        providers = public(TeamReader, ConversationRepo)
        assert len(providers) == 2
        assert all(isinstance(p, ClassProvider) for p in providers)
        assert all(p.public is True for p in providers)
        assert all(p.export is False for p in providers)
        assert providers[0].provide is TeamReader
        assert providers[0].use_class is TeamReader
        assert providers[1].provide is ConversationRepo
        assert providers[1].use_class is ConversationRepo

    def test_public_providers_resolvable(self) -> None:
        mod = Module(
            name="agent",
            providers=[
                *public(PgConversationRepo),
            ],
        )
        ctx = ApplicationContext(modules=[mod])
        assert isinstance(ctx.resolve(PgConversationRepo), PgConversationRepo)


class TestIsPublic:
    def test_is_public_returns_true_for_public_provider(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader, public=True)],
        )
        ctx = ApplicationContext(
            modules=[mod],
            globals=[ValueProvider(provide=Database, use_value=Database())],
        )
        assert ctx.is_public(TeamReader) is True

    def test_is_public_returns_false_for_internal_provider(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
        )
        ctx = ApplicationContext(
            modules=[mod],
            globals=[ValueProvider(provide=Database, use_value=Database())],
        )
        assert ctx.is_public(TeamReader) is False

    def test_is_public_returns_false_for_export_only(self) -> None:
        mod = Module(
            name="agent",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True)],
        )
        ctx = ApplicationContext(
            modules=[mod],
            globals=[ValueProvider(provide=Database, use_value=Database())],
        )
        assert ctx.is_public(TeamReader) is False

    def test_is_public_returns_true_for_export_and_public(self) -> None:
        mod = Module(
            name="agent",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, export=True, public=True)
            ],
        )
        ctx = ApplicationContext(
            modules=[mod],
            globals=[ValueProvider(provide=Database, use_value=Database())],
        )
        assert ctx.is_public(TeamReader) is True

    def test_is_public_returns_true_for_public_global(self) -> None:
        ctx = ApplicationContext(
            modules=[],
            globals=[ValueProvider(provide=Database, use_value=Database(), public=True)],
        )
        assert ctx.is_public(Database) is True

    def test_is_public_returns_false_for_non_public_global(self) -> None:
        ctx = ApplicationContext(
            modules=[],
            globals=[ValueProvider(provide=Database, use_value=Database())],
        )
        assert ctx.is_public(Database) is False
