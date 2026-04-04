from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from spryx_di import Container
from spryx_di.ext.fastapi import Inject, ScopedInject, configure


class Database:
    pass


class Handler:
    def __init__(self, db: Database) -> None:
        self.db = db


class ScopedHandler:
    def __init__(self, db: Database) -> None:
        self.db = db


class TestConfigure:
    def test_configure_attaches_container(self) -> None:
        app = FastAPI()
        container = Container()
        configure(app, container)
        assert app.state.container is container


class TestInject:
    def test_inject_resolves_from_container(self) -> None:
        app = FastAPI()
        container = Container()
        db = Database()
        container.instance(Database, db)
        configure(app, container)

        @app.get("/test")
        def endpoint(handler: Handler = Inject(Handler)) -> dict[str, str]:
            return {"db_id": str(id(handler.db))}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert resp.json()["db_id"] == str(id(db))


class TestScopedInject:
    def test_scoped_inject_resolves_from_request_scope(self) -> None:
        app = FastAPI()
        container = Container()
        db = Database()
        container.instance(Database, db)
        configure(app, container)

        @app.get("/test")
        def endpoint(handler: ScopedHandler = ScopedInject(ScopedHandler)) -> dict[str, str]:
            return {"db_id": str(id(handler.db))}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert resp.json()["db_id"] == str(id(db))


class TestRequestScopeMiddleware:
    def test_each_request_gets_separate_scope(self) -> None:
        app = FastAPI()
        container = Container()
        container.instance(Database, Database())
        configure(app, container)

        @app.get("/test")
        def endpoint(handler: Handler = ScopedInject(Handler)) -> dict[str, int]:
            # Each request creates a new scope, so transient resolves differ
            return {"handler_id": id(handler)}

        client = TestClient(app)
        r1 = client.get("/test")
        r2 = client.get("/test")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Different handler instances from different scopes
        assert r1.json()["handler_id"] != r2.json()["handler_id"]


class TestImportPaths:
    def test_imports(self) -> None:
        from spryx_di.ext.fastapi import Inject, ScopedInject, configure

        assert callable(configure)
        assert callable(Inject)
        assert callable(ScopedInject)
