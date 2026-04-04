# Testing

spryx-di makes testing straightforward: create a `Container`, register fakes, resolve your handler. No mocks.

## Unit Tests with Fakes

```python
from spryx_di import Container

class FakeUserReader(UserReader):
    def get_by_id(self, user_id: str) -> User | None:
        return User(id=user_id, name="Fake User", email="fake@test.com")

def test_create_order():
    container = Container()
    container.instance(UserReader, FakeUserReader())
    container.instance(OrderRepository, FakeOrderRepository())

    handler = container.resolve(CreateOrderHandler)
    order = handler.handle("u1", "Product", 2)

    assert order.user_id == "u1"
```

## override() Context Manager

Temporarily replace registrations during a test:

```python
from spryx_di.testing import override

def test_with_override(container):
    container.singleton(UserReader, PgUserReader)

    with override(container, {UserReader: FakeUserReader}):
        result = container.resolve(UserReader)
        assert isinstance(result, FakeUserReader)

    # Original registration restored
    result = container.resolve(UserReader)
    assert isinstance(result, PgUserReader)
```

Values can be types (registered as transient) or instances (registered as instance).

## FastAPI Integration Tests

```python
from fastapi.testclient import TestClient

def test_endpoint():
    app = FastAPI()
    container = Container()
    container.instance(UserReader, FakeUserReader())
    configure(app, container)

    @app.get("/test")
    def endpoint(handler: Handler = Inject(Handler)):
        return {"result": handler.handle()}

    client = TestClient(app)
    resp = client.get("/test")
    assert resp.status_code == 200
```
