from __future__ import annotations

import pytest

from spryx_di import (
    CircularDependencyError,
    Container,
    TypeHintRequiredError,
    UnresolvableTypeError,
)


class Database:
    pass


class ConversationRepo:
    def __init__(self, db: Database) -> None:
        self.db = db


class TeamReader:
    pass


class PgTeamReader(TeamReader):
    def __init__(self, db: Database) -> None:
        self.db = db


class ListHandler:
    def __init__(self, repo: ConversationRepo, reader: TeamReader) -> None:
        self.repo = repo
        self.reader = reader


class SimpleClass:
    pass


class ServiceWithDefault:
    def __init__(self, repo: ConversationRepo, limit: int = 100) -> None:
        self.repo = repo
        self.limit = limit


class ServiceA:
    def __init__(self, b: ServiceB) -> None:
        self.b = b


class ServiceB:
    def __init__(self, a: ServiceA) -> None:
        self.a = a


class ChainA:
    def __init__(self, b: ChainB) -> None:
        self.b = b


class ChainB:
    def __init__(self, c: ChainC) -> None:
        self.c = c


class ChainC:
    def __init__(self, a: ChainA) -> None:
        self.a = a


class ServiceNeedingPort:
    def __init__(self, port: int) -> None:
        self.port = port


class HandlerWithUnresolvableDep:
    def __init__(self, svc: ServiceNeedingPort) -> None:
        self.svc = svc


class NoHintService:
    def __init__(self, db) -> None:  # type: ignore[no-untyped-def]
        self.db = db


class TestAutoWiring:
    def test_resolve_with_typed_dependencies(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        container.register(ConversationRepo, ConversationRepo)
        container.register(TeamReader, PgTeamReader)
        handler = container.resolve(ListHandler)
        assert isinstance(handler, ListHandler)
        assert isinstance(handler.repo, ConversationRepo)
        assert isinstance(handler.reader, PgTeamReader)

    def test_resolve_no_dependencies(self, container: Container) -> None:
        result = container.resolve(SimpleClass)
        assert isinstance(result, SimpleClass)


class TestRecursiveResolution:
    def test_nested_dependency_chain(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        container.register(ConversationRepo, ConversationRepo)
        container.register(TeamReader, PgTeamReader)
        handler = container.resolve(ListHandler)
        assert handler.repo.db is db
        assert handler.reader.db is db  # type: ignore[attr-defined]


class TestDefaultValueFallback:
    def test_uses_default_for_unregistered_type(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        container.register(ConversationRepo, ConversationRepo)
        svc = container.resolve(ServiceWithDefault)
        assert svc.limit == 100


class TestCircularDependencyDetection:
    def test_direct_circular(self, container: Container) -> None:
        container.register(ServiceA, ServiceA)
        container.register(ServiceB, ServiceB)
        with pytest.raises(CircularDependencyError) as exc_info:
            container.resolve(ServiceA)
        assert "ServiceA" in str(exc_info.value)
        assert "ServiceB" in str(exc_info.value)

    def test_indirect_circular(self, container: Container) -> None:
        container.register(ChainA, ChainA)
        container.register(ChainB, ChainB)
        container.register(ChainC, ChainC)
        with pytest.raises(CircularDependencyError) as exc_info:
            container.resolve(ChainA)
        assert "ChainA" in str(exc_info.value)


class TestUnresolvableType:
    def test_missing_dependency(self, container: Container) -> None:
        with pytest.raises(UnresolvableTypeError) as exc_info:
            container.resolve(HandlerWithUnresolvableDep)
        assert "int" in str(exc_info.value) or "port" in str(exc_info.value)
        assert "Hint" in str(exc_info.value)


class TestTypeHintRequired:
    def test_missing_type_hint(self, container: Container) -> None:
        with pytest.raises(TypeHintRequiredError) as exc_info:
            container.resolve(NoHintService)
        assert "db" in str(exc_info.value)
        assert "NoHintService" in str(exc_info.value)


class TestInterfaceMapping:
    def test_resolve_via_interface(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        container.register(TeamReader, PgTeamReader)
        handler = container.resolve(ListHandler)
        assert isinstance(handler.reader, PgTeamReader)


class TestSingletonFactoryCache:
    def test_factory_with_singleton_caches(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        container.singleton(TeamReader, PgTeamReader)
        container.factory(TeamReader, lambda c: PgTeamReader(c.resolve(Database)))
        a = container.resolve(TeamReader)
        assert isinstance(a, PgTeamReader)


class TestTransientProvider:
    def test_transient_scope_in_module(self) -> None:
        from spryx_di import ApplicationContext, Module, Provider, Scope

        mod = Module(
            name="test",
            providers=[
                Provider(provide=SimpleClass, use_class=SimpleClass, scope=Scope.TRANSIENT),
            ],
        )
        ctx = ApplicationContext(modules=[mod])
        a = ctx.resolve(SimpleClass)
        b = ctx.resolve(SimpleClass)
        assert a is not b
