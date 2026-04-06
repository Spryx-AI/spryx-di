from __future__ import annotations

import pytest

from spryx_di import (
    AmbiguousExportError,
    ApplicationContext,
    CircularImportError,
    ClassProvider,
    ExistingProvider,
    ExportWithoutProviderError,
    FactoryProvider,
    Module,
    ModuleBoundaryError,
    Scope,
    UnresolvedImportError,
    ValueProvider,
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


# --- Ports (ABCs/Protocols used as import types) ---


class TeamReaderPort:
    """Port for cross-module import of TeamReader."""

    pass


class BillingGatewayPort:
    """Port for cross-module import of BillingGateway."""

    pass


class TestModuleDefinition:
    def test_define_module(self) -> None:
        module = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader],
        )
        assert module.name == "identity"
        assert len(module.providers) == 1
        assert module.exports == [TeamReader]

    def test_class_provider_defaults_use_class_to_provide(self) -> None:
        p = ClassProvider(provide=PgTeamReader)
        assert p.use_class is PgTeamReader
        assert p.scope == Scope.SINGLETON

        module = Module(
            name="test",
            providers=[ClassProvider(provide=PgTeamReader)],
        )
        assert len(module.providers) == 1


class TestProvider:
    def test_use_class(self) -> None:
        p = ClassProvider(provide=TeamReader, use_class=PgTeamReader)
        assert p.provide == TeamReader
        assert p.use_class == PgTeamReader
        assert p.scope == Scope.SINGLETON

    def test_use_value(self) -> None:
        db = Database()
        p = ValueProvider(provide=Database, use_value=db)
        assert p.provide == Database

    def test_use_factory(self) -> None:
        p = FactoryProvider(
            provide=TeamReader,
            use_factory=lambda c: PgTeamReader(c.resolve(Database)),
        )
        assert p.provide == TeamReader

    def test_use_existing(self) -> None:
        p = ExistingProvider(provide=TeamReader, use_existing=PgTeamReader)
        assert p.provide == TeamReader
        assert p.use_existing == PgTeamReader


class TestApplicationContext:
    def test_compose_modules(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ClassProvider(provide=UserReader, use_class=PgUserReader),
            ],
            exports=[TeamReader, UserReader],
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
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)

    def test_cross_module_imports_via_ports(self) -> None:
        """Modules import ports (types), not other modules."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        conversations = Module(
            name="conversations",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, conversations],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        # The imported port is available in the module container
        port = ctx.resolve_within(conversations, TeamReaderPort)
        assert isinstance(port, PgTeamReader)


class TestModuleBoundary:
    def test_boundary_violation_raises(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        conversations = Module(
            name="conversations",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[TeamReaderPort],
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

    def test_export_without_provider_raises(self) -> None:
        with pytest.raises(ExportWithoutProviderError) as exc_info:
            ApplicationContext(
                modules=[
                    Module(
                        name="bad",
                        providers=[],
                        exports=[TeamReader],
                    )
                ]
            )
        assert "TeamReader" in str(exc_info.value)
        assert "Hint" in str(exc_info.value)


class TestUnresolvedImport:
    def test_unresolved_import_raises(self) -> None:
        mod = Module(
            name="consumer",
            providers=[],
            imports=[TeamReaderPort],
        )
        with pytest.raises(UnresolvedImportError) as exc_info:
            ApplicationContext(modules=[mod])
        assert "TeamReaderPort" in str(exc_info.value)
        assert "consumer" in str(exc_info.value)

    def test_unresolved_import_shows_available_exports(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            imports=[BillingGatewayPort],
        )
        db = Database()
        with pytest.raises(UnresolvedImportError) as exc_info:
            ApplicationContext(
                modules=[identity, consumer],
                globals=[ValueProvider(provide=Database, use_value=db)],
            )
        assert "BillingGatewayPort" in str(exc_info.value)
        assert "TeamReaderPort" in str(exc_info.value)


class TestAmbiguousExport:
    def test_ambiguous_export_raises(self) -> None:
        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=TeamReaderPort)],
            exports=[TeamReaderPort],
        )
        mod_b = Module(
            name="b",
            providers=[ClassProvider(provide=TeamReaderPort)],
            exports=[TeamReaderPort],
        )
        with pytest.raises(AmbiguousExportError) as exc_info:
            ApplicationContext(modules=[mod_a, mod_b])
        assert "TeamReaderPort" in str(exc_info.value)
        assert "a" in str(exc_info.value)
        assert "b" in str(exc_info.value)


class TestCircularImports:
    def test_direct_circular_raises(self) -> None:
        """A imports from B, B imports from A → cycle."""
        mod_a = Module(
            name="a",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
            imports=[BillingGatewayPort],
        )
        mod_b = Module(
            name="b",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
                ExistingProvider(provide=BillingGatewayPort, use_existing=BillingGateway),
            ],
            exports=[BillingGatewayPort],
            imports=[TeamReaderPort],
        )
        db = Database()
        with pytest.raises(CircularImportError) as exc_info:
            ApplicationContext(
                modules=[mod_a, mod_b],
                globals=[ValueProvider(provide=Database, use_value=db)],
            )
        assert "a" in str(exc_info.value)
        assert "b" in str(exc_info.value)
        assert "Hint" in str(exc_info.value)

    def test_indirect_circular_raises(self) -> None:
        """A→B→C→A cycle."""

        class PortA:
            pass

        class PortB:
            pass

        class PortC:
            pass

        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=PortA)],
            exports=[PortA],
            imports=[PortC],
        )
        mod_b = Module(
            name="b",
            providers=[ClassProvider(provide=PortB)],
            exports=[PortB],
            imports=[PortA],
        )
        mod_c = Module(
            name="c",
            providers=[ClassProvider(provide=PortC)],
            exports=[PortC],
            imports=[PortB],
        )
        with pytest.raises(CircularImportError) as exc_info:
            ApplicationContext(modules=[mod_a, mod_b, mod_c])
        assert "a" in str(exc_info.value)

    def test_no_cycle_when_unidirectional(self) -> None:
        """A→B is fine when B doesn't import from A."""
        mod_a = Module(
            name="a",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        mod_b = Module(
            name="b",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            imports=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[mod_a, mod_b],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        assert isinstance(ctx.resolve(BillingGateway), StripeBillingGateway)


class TestImportResolution:
    def test_imported_port_resolved_in_module_container(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[TeamReaderPort],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        port = ctx.resolve_within(consumer, TeamReaderPort)
        assert isinstance(port, PgTeamReader)

    def test_module_container_no_access_to_undeclared_ports(self) -> None:
        """A module can't access exports it didn't declare in imports."""
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        billing = Module(
            name="billing",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
                ExistingProvider(provide=BillingGatewayPort, use_existing=BillingGateway),
            ],
            exports=[BillingGatewayPort],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[TeamReaderPort],  # only imports TeamReaderPort, not BillingGatewayPort
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, billing, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        # Can access declared import
        port = ctx.resolve_within(consumer, TeamReaderPort)
        assert isinstance(port, PgTeamReader)

        # Cannot access undeclared import
        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(consumer, BillingGatewayPort)

    def test_imported_port_is_same_singleton(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            imports=[TeamReaderPort],
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
                ),
            ],
            exports=[TeamReader],
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


class TestUseExisting:
    def test_use_existing_resolves_to_target(self) -> None:
        db = Database()
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ExistingProvider(provide=UserReader, use_existing=TeamReader),
            ],
            exports=[TeamReader, UserReader],
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
                ExistingProvider(provide=TeamReaderPort, use_existing=TeamReader),
            ],
            exports=[TeamReaderPort],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ExistingProvider(provide=UserReader, use_existing=TeamReaderPort),
            ],
            imports=[TeamReaderPort],
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
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
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
