from __future__ import annotations

import logging

import pytest

from spryx_di import Container


class Database:
    pass


class TeamReader:
    def __init__(self, db: Database) -> None:
        self.db = db


class PgTeamReader(TeamReader):
    pass


class FakeTeamReader(TeamReader):
    pass


class HttpTeamReader(TeamReader):
    pass


class SimpleService:
    pass


class TestContainerInstantiation:
    def test_create_empty_container(self) -> None:
        c = Container()
        assert c is not None


class TestTransientRegistration:
    def test_register_returns_new_instance_each_time(self, container: Container) -> None:
        container.instance(Database, Database())
        container.register(TeamReader, PgTeamReader)
        a = container.resolve(TeamReader)
        b = container.resolve(TeamReader)
        assert isinstance(a, PgTeamReader)
        assert isinstance(b, PgTeamReader)
        assert a is not b

    def test_register_concrete_to_itself(self, container: Container) -> None:
        container.register(SimpleService, SimpleService)
        a = container.resolve(SimpleService)
        b = container.resolve(SimpleService)
        assert isinstance(a, SimpleService)
        assert a is not b


class TestSingletonRegistration:
    def test_singleton_returns_same_instance(self, container: Container) -> None:
        container.instance(Database, Database())
        container.singleton(TeamReader, PgTeamReader)
        a = container.resolve(TeamReader)
        b = container.resolve(TeamReader)
        assert isinstance(a, PgTeamReader)
        assert a is b


class TestInstanceRegistration:
    def test_instance_returns_exact_object(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        resolved = container.resolve(Database)
        assert resolved is db


class TestFactoryRegistration:
    def test_factory_called_with_container(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        container.factory(TeamReader, lambda c: PgTeamReader(c.resolve(Database)))
        result = container.resolve(TeamReader)
        assert isinstance(result, PgTeamReader)
        assert result.db is db


class TestDictStyleAccess:
    def test_bracket_access_resolves_type(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        assert container[Database] is db


class TestHasCheck:
    def test_has_registered_type(self, container: Container) -> None:
        container.instance(Database, Database())
        assert container.has(Database) is True

    def test_has_unregistered_type(self, container: Container) -> None:
        assert container.has(Database) is False


class TestOverride:
    def test_override_replaces_registration(self, container: Container) -> None:
        container.instance(Database, Database())
        container.singleton(TeamReader, PgTeamReader)
        container.override(TeamReader, FakeTeamReader)
        result = container.resolve(TeamReader)
        assert isinstance(result, FakeTeamReader)

    def test_override_with_instance(self, container: Container) -> None:
        container.singleton(TeamReader, PgTeamReader)
        fake = FakeTeamReader(Database())
        container.override(TeamReader, fake)
        assert container.resolve(TeamReader) is fake


class TestDuplicateWarning:
    def test_duplicate_registration_logs_warning(
        self, container: Container, caplog: pytest.LogCaptureFixture
    ) -> None:
        container.instance(Database, Database())
        with caplog.at_level(logging.WARNING, logger="spryx_di"):
            container.singleton(TeamReader, PgTeamReader)
            container.singleton(TeamReader, HttpTeamReader)
        assert "Overwriting registration" in caplog.text


class TestShutdown:
    @pytest.mark.asyncio
    async def test_shutdown_runs_hooks_in_reverse(self, container: Container) -> None:
        order: list[str] = []
        container.on_shutdown(lambda: order.append("first"))
        container.on_shutdown(lambda: order.append("second"))
        await container.shutdown()
        assert order == ["second", "first"]

    @pytest.mark.asyncio
    async def test_shutdown_supports_async_hooks(self, container: Container) -> None:
        closed = False

        async def close_resource() -> None:
            nonlocal closed
            closed = True

        container.on_shutdown(close_resource)
        await container.shutdown()
        assert closed is True

    @pytest.mark.asyncio
    async def test_shutdown_clears_hooks(self, container: Container) -> None:
        counter: list[int] = []
        container.on_shutdown(lambda: counter.append(1))
        await container.shutdown()
        await container.shutdown()
        assert len(counter) == 1
