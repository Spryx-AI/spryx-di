from __future__ import annotations

import logging

import pytest

from spryx_di import (
    ApplicationContext,
    CircularModuleError,
    ClassProvider,
    ExistingProvider,
    ExportWithoutProviderError,
    FactoryProvider,
    Module,
    ModuleBoundaryError,
    ModuleNotFoundError,
    Scope,
    ValueProvider,
    forward_ref,
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

    def test_bare_type_as_provider(self) -> None:
        module = Module(
            name="test",
            providers=[PgTeamReader],
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

    def test_cross_module_imports(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
        )
        conversations = Module(
            name="conversations",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            exports=[],
            imports=[identity],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, conversations],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        handler = ctx.resolve_within(conversations, ListHandler)
        assert isinstance(handler.reader, PgTeamReader)

    def test_last_module_provider_wins(self) -> None:
        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=UserReader, use_class=PgUserReader)],
            exports=[UserReader],
        )
        mod_b = Module(
            name="b",
            providers=[ClassProvider(provide=UserReader, use_class=HttpUserReader)],
            exports=[UserReader],
        )
        ctx = ApplicationContext(modules=[mod_a, mod_b])
        assert isinstance(ctx.resolve(UserReader), HttpUserReader)


class TestModuleBoundary:
    def test_boundary_violation_raises(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
        )
        conversations = Module(
            name="conversations",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[identity],
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

    def test_module_not_found_raises(self) -> None:
        orphan = Module(name="orphan", providers=[], exports=[])
        with pytest.raises(ModuleNotFoundError) as exc_info:
            ApplicationContext(
                modules=[
                    Module(
                        name="consumer",
                        providers=[],
                        imports=[orphan],
                    )
                ]
            )
        assert "orphan" in str(exc_info.value)
        assert "Hint" in str(exc_info.value)


class TestCircularModules:
    def test_direct_circular_raises(self) -> None:
        mod_a: Module = Module(name="a", providers=[], imports=[])
        mod_b: Module = Module(name="b", providers=[], imports=[mod_a])
        mod_a.imports = [mod_b]

        with pytest.raises(CircularModuleError) as exc_info:
            ApplicationContext(modules=[mod_a, mod_b])
        assert "a" in str(exc_info.value)
        assert "b" in str(exc_info.value)
        assert "Hint" in str(exc_info.value)

    def test_indirect_circular_raises(self) -> None:
        mod_a: Module = Module(name="a", providers=[], imports=[])
        mod_b: Module = Module(name="b", providers=[], imports=[mod_a])
        mod_c: Module = Module(name="c", providers=[], imports=[mod_b])
        mod_a.imports = [mod_c]

        with pytest.raises(CircularModuleError) as exc_info:
            ApplicationContext(modules=[mod_a, mod_b, mod_c])
        assert "a" in str(exc_info.value)


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
            ],
            exports=[TeamReader],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ExistingProvider(provide=UserReader, use_existing=TeamReader),
            ],
            imports=[identity],
        )
        ctx = ApplicationContext(
            modules=[identity, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )
        assert isinstance(ctx.resolve(UserReader), PgTeamReader)


class BillingGateway:
    pass


class StripeBillingGateway(BillingGateway):
    pass


class TestForwardRef:
    def test_forward_ref_resolves_circular(self) -> None:

        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
            imports=[forward_ref("billing")],
        )
        billing = Module(
            name="billing",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            exports=[BillingGateway],
            imports=[forward_ref("identity")],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, billing],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        assert isinstance(ctx.resolve(TeamReader), PgTeamReader)
        assert isinstance(ctx.resolve(BillingGateway), StripeBillingGateway)

    def test_forward_ref_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:

        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
            imports=[forward_ref("b")],
        )
        mod_b = Module(
            name="b",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            exports=[BillingGateway],
            imports=[forward_ref("a")],
        )
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            ApplicationContext(
                modules=[mod_a, mod_b],
                globals=[ValueProvider(provide=Database, use_value=Database())],
            )
        assert "Circular dependency between modules" in caplog.text

    def test_forward_ref_not_found_raises(self) -> None:

        mod = Module(
            name="test",
            providers=[],
            imports=[forward_ref("nonexistent")],
        )
        with pytest.raises(ModuleNotFoundError) as exc_info:
            ApplicationContext(modules=[mod])
        assert "nonexistent" in str(exc_info.value)

    def test_direct_circular_still_raises(self) -> None:

        mod_a: Module = Module(name="a", providers=[], imports=[])
        mod_b: Module = Module(name="b", providers=[], imports=[mod_a])
        mod_a.imports = [mod_b]

        with pytest.raises(CircularModuleError):
            ApplicationContext(modules=[mod_a, mod_b])

    def test_forward_ref_cross_module_boundary(self) -> None:

        identity = Module(
            name="identity",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
            imports=[forward_ref("billing")],
        )
        billing = Module(
            name="billing",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            exports=[BillingGateway],
            imports=[forward_ref("identity")],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, billing],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve_within(billing, TeamReader)
        assert isinstance(reader, PgTeamReader)

        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(billing, TeamRepository)


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


class TestForwardRefIndirectCycle:
    def test_indirect_forward_ref_cycle_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:

        mod_a = Module(
            name="a",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
        )
        mod_b = Module(
            name="b",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            exports=[BillingGateway],
            imports=[mod_a, forward_ref("a")],
        )
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            ApplicationContext(
                modules=[mod_a, mod_b],
                globals=[ValueProvider(provide=Database, use_value=Database())],
            )


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


class TestReExports:
    def test_reexport_specific_type(self) -> None:
        child = Module(
            name="child",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[child],
            exports=[TeamReader],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[parent],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[child, parent, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        handler = ctx.resolve_within(consumer, ListHandler)
        assert isinstance(handler.reader, PgTeamReader)

    def test_reexport_entire_module(self) -> None:
        child = Module(
            name="child",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ClassProvider(provide=UserReader, use_class=PgUserReader),
            ],
            exports=[TeamReader, UserReader],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[child],
            exports=[child],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            imports=[parent],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[child, parent, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve_within(consumer, TeamReader)
        assert isinstance(reader, PgTeamReader)
        user_reader = ctx.resolve_within(consumer, UserReader)
        assert isinstance(user_reader, PgUserReader)

    def test_reexport_module_not_imported_raises(self) -> None:
        orphan = Module(
            name="orphan",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[],
            exports=[orphan],
        )
        with pytest.raises(ExportWithoutProviderError) as exc_info:
            ApplicationContext(modules=[parent, orphan])
        assert "orphan" in str(exc_info.value)
        assert "does not import" in str(exc_info.value)

    def test_reexport_type_not_in_providers_or_imports_raises(self) -> None:
        child = Module(
            name="child",
            providers=[ClassProvider(provide=UserReader, use_class=PgUserReader)],
            exports=[UserReader],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[child],
            exports=[TeamReader],
        )
        with pytest.raises(ExportWithoutProviderError):
            ApplicationContext(
                modules=[child, parent],
                globals=[ValueProvider(provide=Database, use_value=Database())],
            )

    def test_reexport_boundary_blocks_non_reexported(self) -> None:
        child = Module(
            name="child",
            providers=[
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
            ],
            exports=[TeamReader, TeamRepository],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[child],
            exports=[TeamReader],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            imports=[parent],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[child, parent, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve_within(consumer, TeamReader)
        assert isinstance(reader, PgTeamReader)

        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(consumer, TeamRepository)

    def test_reexport_transitive(self) -> None:
        grandchild = Module(
            name="grandchild",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
        )
        child = Module(
            name="child",
            providers=[],
            imports=[grandchild],
            exports=[grandchild],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[child],
            exports=[child],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            imports=[parent],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[grandchild, child, parent, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve_within(consumer, TeamReader)
        assert isinstance(reader, PgTeamReader)

    def test_parent_aggregates_submodules(self) -> None:
        config_module = Module(
            name="agent.config",
            providers=[
                ClassProvider(provide=TeamRepository, use_class=PgTeamRepository),
                ClassProvider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
        )
        billing_module = Module(
            name="agent.billing",
            providers=[
                ClassProvider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            exports=[BillingGateway],
        )
        agent_module = Module(
            name="agent",
            providers=[],
            imports=[config_module, billing_module],
            exports=[TeamReader, BillingGateway],
        )
        consumer = Module(
            name="consumer",
            providers=[
                ClassProvider(provide=ConversationRepo, use_class=PgConversationRepo),
            ],
            imports=[agent_module],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[config_module, billing_module, agent_module, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve_within(consumer, TeamReader)
        assert isinstance(reader, PgTeamReader)
        gateway = ctx.resolve_within(consumer, BillingGateway)
        assert isinstance(gateway, StripeBillingGateway)

        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(consumer, TeamRepository)

    def test_reexport_singleton_identity(self) -> None:
        child = Module(
            name="child",
            providers=[ClassProvider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
        )
        parent = Module(
            name="parent",
            providers=[],
            imports=[child],
            exports=[child],
        )
        consumer = Module(
            name="consumer",
            providers=[],
            imports=[parent],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[child, parent, consumer],
            globals=[ValueProvider(provide=Database, use_value=db)],
        )

        first = ctx.resolve_within(consumer, TeamReader)
        second = ctx.resolve_within(consumer, TeamReader)
        assert first is second
        assert isinstance(first, PgTeamReader)
