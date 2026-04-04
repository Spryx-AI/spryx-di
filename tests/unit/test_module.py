from __future__ import annotations

import logging

import pytest

from spryx_di import (
    ApplicationContext,
    CircularModuleError,
    ExportWithoutProviderError,
    Module,
    ModuleBoundaryError,
    ModuleNotFoundError,
    Provider,
    Scope,
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
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
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
        p = Provider(provide=TeamReader, use_class=PgTeamReader)
        assert p.provide == TeamReader
        assert p.use_class == PgTeamReader
        assert p.scope == Scope.SINGLETON

    def test_use_value(self) -> None:
        db = Database()
        p = Provider(provide=Database, use_value=db)
        assert p.provide == Database

    def test_use_factory(self) -> None:
        p = Provider(provide=TeamReader, use_factory=lambda c: PgTeamReader(c.resolve(Database)))
        assert p.provide == TeamReader

    def test_no_source_raises(self) -> None:
        with pytest.raises(ValueError, match="must specify exactly one"):
            Provider(provide=TeamReader)

    def test_multiple_sources_raises(self) -> None:
        with pytest.raises(ValueError, match="must specify exactly one"):
            Provider(provide=TeamReader, use_class=PgTeamReader, use_value="fake")


class TestApplicationContext:
    def test_compose_modules(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                Provider(provide=TeamRepository, use_class=PgTeamRepository, scope=Scope.SINGLETON),
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
                Provider(provide=UserReader, use_class=PgUserReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader, UserReader],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity],
            globals=[Provider(provide=Database, use_value=db)],
        )

        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)

    def test_globals_available_to_modules(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity],
            globals=[Provider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)

    def test_cross_module_imports(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader],
        )
        conversations = Module(
            name="conversations",
            providers=[
                Provider(
                    provide=ConversationRepo,
                    use_class=PgConversationRepo,
                    scope=Scope.SINGLETON,
                ),
            ],
            exports=[],
            imports=[identity],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, conversations],
            globals=[Provider(provide=Database, use_value=db)],
        )

        # TeamReader is available in conversations module via import
        handler = ctx.resolve_within(conversations, ListHandler)
        assert isinstance(handler.reader, PgTeamReader)

    def test_last_module_provider_wins(self) -> None:
        mod_a = Module(
            name="a",
            providers=[Provider(provide=UserReader, use_class=PgUserReader, scope=Scope.SINGLETON)],
            exports=[UserReader],
        )
        mod_b = Module(
            name="b",
            providers=[
                Provider(provide=UserReader, use_class=HttpUserReader, scope=Scope.SINGLETON)
            ],
            exports=[UserReader],
        )
        ctx = ApplicationContext(modules=[mod_a, mod_b])
        assert isinstance(ctx.resolve(UserReader), HttpUserReader)


class TestModuleBoundary:
    def test_boundary_violation_raises(self) -> None:
        identity = Module(
            name="identity",
            providers=[
                Provider(
                    provide=TeamRepository,
                    use_class=PgTeamRepository,
                    scope=Scope.SINGLETON,
                ),
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader],  # TeamRepository NOT exported
        )
        conversations = Module(
            name="conversations",
            providers=[
                Provider(
                    provide=ConversationRepo,
                    use_class=PgConversationRepo,
                    scope=Scope.SINGLETON,
                ),
            ],
            imports=[identity],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, conversations],
            globals=[Provider(provide=Database, use_value=db)],
        )

        # TeamRepository is a provider of identity but NOT exported
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
                        exports=[TeamReader],  # Not a provider!
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
                        imports=[orphan],  # orphan is not in modules list
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
                Provider(
                    provide=TeamReader,
                    use_factory=lambda c: PgTeamReader(c.resolve(Database)),
                ),
            ],
            exports=[TeamReader],
        )
        ctx = ApplicationContext(
            modules=[identity],
            globals=[Provider(provide=Database, use_value=db)],
        )
        reader = ctx.resolve(TeamReader)
        assert isinstance(reader, PgTeamReader)
        assert reader.db is db


class BillingGateway:
    pass


class StripeBillingGateway(BillingGateway):
    pass


class TestForwardRef:
    def test_forward_ref_resolves_circular(self) -> None:
        """Two modules that depend on each other via forward_ref — should work."""
        identity = Module(
            name="identity",
            providers=[
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader],
            imports=[forward_ref("billing")],
        )
        billing = Module(
            name="billing",
            providers=[
                Provider(
                    provide=BillingGateway,
                    use_class=StripeBillingGateway,
                    scope=Scope.SINGLETON,
                ),
            ],
            exports=[BillingGateway],
            imports=[forward_ref("identity")],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, billing],
            globals=[Provider(provide=Database, use_value=db)],
        )

        # Both resolve correctly
        assert isinstance(ctx.resolve(TeamReader), PgTeamReader)
        assert isinstance(ctx.resolve(BillingGateway), StripeBillingGateway)

    def test_forward_ref_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Circular via forward_ref should log a warning."""
        mod_a = Module(
            name="a",
            providers=[Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON)],
            exports=[TeamReader],
            imports=[forward_ref("b")],
        )
        mod_b = Module(
            name="b",
            providers=[
                Provider(
                    provide=BillingGateway,
                    use_class=StripeBillingGateway,
                    scope=Scope.SINGLETON,
                ),
            ],
            exports=[BillingGateway],
            imports=[forward_ref("a")],
        )
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            ApplicationContext(
                modules=[mod_a, mod_b],
                globals=[Provider(provide=Database, use_value=Database())],
            )
        assert "Circular dependency between modules" in caplog.text

    def test_forward_ref_not_found_raises(self) -> None:
        """forward_ref to non-existent module should raise."""
        mod = Module(
            name="test",
            providers=[],
            imports=[forward_ref("nonexistent")],
        )
        with pytest.raises(ModuleNotFoundError) as exc_info:
            ApplicationContext(modules=[mod])
        assert "nonexistent" in str(exc_info.value)

    def test_direct_circular_still_raises(self) -> None:
        """Direct refs (not forward_ref) still raise CircularModuleError."""
        mod_a: Module = Module(name="a", providers=[], imports=[])
        mod_b: Module = Module(name="b", providers=[], imports=[mod_a])
        mod_a.imports = [mod_b]

        with pytest.raises(CircularModuleError):
            ApplicationContext(modules=[mod_a, mod_b])

    def test_forward_ref_cross_module_boundary(self) -> None:
        """forward_ref imports respect exports — boundary enforcement works."""
        identity = Module(
            name="identity",
            providers=[
                Provider(provide=TeamRepository, use_class=PgTeamRepository, scope=Scope.SINGLETON),
                Provider(provide=TeamReader, use_class=PgTeamReader, scope=Scope.SINGLETON),
            ],
            exports=[TeamReader],  # TeamRepository NOT exported
            imports=[forward_ref("billing")],
        )
        billing = Module(
            name="billing",
            providers=[
                Provider(
                    provide=BillingGateway,
                    use_class=StripeBillingGateway,
                    scope=Scope.SINGLETON,
                ),
            ],
            exports=[BillingGateway],
            imports=[forward_ref("identity")],
        )
        db = Database()
        ctx = ApplicationContext(
            modules=[identity, billing],
            globals=[Provider(provide=Database, use_value=db)],
        )

        # TeamReader is exported — billing can access it
        reader = ctx.resolve_within(billing, TeamReader)
        assert isinstance(reader, PgTeamReader)

        # TeamRepository is NOT exported — billing cannot access it
        with pytest.raises(ModuleBoundaryError):
            ctx.resolve_within(billing, TeamRepository)


class FakeResource:
    """Simulates an async resource with __aexit__."""

    def __init__(self) -> None:
        self.closed = False

    async def __aenter__(self) -> FakeResource:
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.closed = True


class FakeClient:
    """Simulates an async client with aclose."""

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
                Provider(provide=TeamReader, use_class=PgTeamReader),
            ],
            exports=[TeamReader],
            on_destroy=destroy_identity,
        )
        ctx = ApplicationContext(
            modules=[identity],
            globals=[Provider(provide=Database, use_value=Database())],
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
            globals=[Provider(provide=FakeResource, use_value=resource)],
        )
        await ctx.shutdown()
        assert resource.closed is True

    @pytest.mark.asyncio
    async def test_aclose_called_on_shutdown(self) -> None:
        client = FakeClient()
        ctx = ApplicationContext(
            modules=[],
            globals=[Provider(provide=FakeClient, use_value=client)],
        )
        await ctx.shutdown()
        assert client.closed is True

    @pytest.mark.asyncio
    async def test_on_destroy_before_managed_instances(self) -> None:
        """on_destroy runs before context managers are closed."""
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
            providers=[Provider(provide=TrackedResource, use_value=resource)],
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
            globals=[Provider(provide=SyncCloseable, use_value=obj)],
        )
        await ctx.shutdown()
        assert obj.closed is True


class TestForwardRefIndirectCycle:
    def test_indirect_forward_ref_cycle_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A -> B (direct), B -> A (forward_ref) — indirect cycle via _has_path."""
        mod_a = Module(
            name="a",
            providers=[Provider(provide=TeamReader, use_class=PgTeamReader)],
            exports=[TeamReader],
        )
        mod_b = Module(
            name="b",
            providers=[
                Provider(provide=BillingGateway, use_class=StripeBillingGateway),
            ],
            exports=[BillingGateway],
            imports=[mod_a, forward_ref("a")],
        )
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            ApplicationContext(
                modules=[mod_a, mod_b],
                globals=[Provider(provide=Database, use_value=Database())],
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

        asyncio.get_event_loop().run_until_complete(ctx.shutdown())
        assert called is True

    def test_create_scope(self) -> None:
        ctx = ApplicationContext(modules=[])
        scope = ctx.create_scope()
        assert scope is not None

    def test_container_property(self) -> None:
        ctx = ApplicationContext(modules=[])
        assert ctx.container is not None
