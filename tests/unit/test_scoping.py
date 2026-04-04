from __future__ import annotations

from spryx_di import Container


class Database:
    pass


class TeamReader:
    pass


class PgTeamReader(TeamReader):
    pass


class FakeTeamReader:
    pass


class Transaction:
    pass


class Cache:
    pass


class RedisCache(Cache):
    pass


class Handler:
    def __init__(self, db: Database, tx: Transaction) -> None:
        self.db = db
        self.tx = tx


class TestScopeInheritsParent:
    def test_scope_resolves_parent_registration(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        scope = container.create_scope()
        assert scope.resolve(Database) is db


class TestScopeLocalOverrides:
    def test_scope_override_does_not_affect_parent(self, container: Container) -> None:
        container.instance(Database, Database())
        container.singleton(TeamReader, PgTeamReader)
        scope = container.create_scope()
        fake = FakeTeamReader()
        scope.instance(TeamReader, fake)
        assert scope.resolve(TeamReader) is fake
        assert isinstance(container.resolve(TeamReader), PgTeamReader)


class TestScopedSingletonsAreLocal:
    def test_singleton_in_scope_not_in_parent(self, container: Container) -> None:
        scope = container.create_scope()
        scope.singleton(Cache, RedisCache)
        scope.resolve(Cache)
        assert not container.has(Cache)
        assert scope.has(Cache)


class TestMixedResolution:
    def test_handler_with_parent_and_scope_deps(self, container: Container) -> None:
        db = Database()
        container.instance(Database, db)
        scope = container.create_scope()
        tx = Transaction()
        scope.instance(Transaction, tx)
        handler = scope.resolve(Handler)
        assert handler.db is db
        assert handler.tx is tx
