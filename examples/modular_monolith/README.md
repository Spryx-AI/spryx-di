# Modular Monolith Example

A realistic e-commerce application demonstrating `spryx-di` with modular architecture.

## Structure

```
modules/
├── identity/       # User management (ports + adapters)
│   ├── ports.py    # Abstract interfaces (UserReader, UserRepository)
│   ├── adapters.py # Concrete implementations (InMemory*)
│   ├── domain.py   # Domain models
│   └── module.py   # ModuleDefinition — registers all identity bindings
├── catalog/        # Product catalog
│   ├── ports.py
│   ├── adapters.py
│   ├── domain.py
│   ├── handlers.py # Use case handlers (auto-wired, no DI imports)
│   └── module.py
└── orders/         # Order management (depends on identity + catalog)
    ├── ports.py
    ├── adapters.py
    ├── domain.py
    ├── handlers.py
    └── module.py

api/
├── main.py         # App composition — compose_modules + FastAPI configure
├── settings.py     # pydantic-settings integration
└── routes.py       # FastAPI routes using Inject()
```

## Key Concepts

1. **Modules are self-contained** — each defines its own ports (interfaces) and adapters (implementations)
2. **Handlers have zero DI imports** — they just declare typed `__init__` params, spryx-di auto-wires them
3. **Cross-module dependencies** — `orders` depends on `identity.UserReader` and `catalog.ProductReader`, resolved automatically
4. **Module registration** — each module has a `ModuleDefinition` that registers its bindings
5. **App composition** — `compose_modules()` wires everything together at the entry point

## Running

```bash
cd examples/modular_monolith
uvicorn api.main:app --reload
```

## Testing

Modules are trivially testable — just create a `Container`, register fakes, and resolve handlers:

```python
from spryx_di import Container
from modules.orders.handlers import CreateOrderHandler
from modules.catalog.ports import ProductReader
from modules.identity.ports import UserReader

container = Container()
container.instance(UserReader, FakeUserReader())
container.instance(ProductReader, FakeProductReader())
container.instance(OrderRepository, FakeOrderRepository())

handler = container.resolve(CreateOrderHandler)
# handler is fully wired with fakes — no mocks needed
```
