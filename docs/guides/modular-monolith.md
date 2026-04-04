# Modular Monolith Architecture

How to structure a Python application with spryx-di using ports & adapters per module.

## Structure

```
modules/
├── identity/
│   ├── ports.py      # UserReader (ABC), UserRepository (ABC)
│   ├── adapters.py   # PgUserReader, PgUserRepository
│   └── module.py     # Module definition
├── orders/
│   ├── ports.py      # OrderRepository (ABC)
│   ├── adapters.py   # PgOrderRepository
│   ├── handlers.py   # CreateOrderHandler (zero DI imports)
│   └── module.py     # Module definition
app/
└── main.py           # Composition root
```

## Module Definition

Each module registers its own providers and declares what it exports:

```python
# modules/identity/module.py
from spryx_di import Module, Provider

identity_module = Module(
    name="identity",
    providers=[
        Provider(provide=UserRepository, use_class=PgUserRepository),
        Provider(provide=UserReader, use_class=PgUserReader),
    ],
    exports=[UserReader],
)
```

## Cross-Module Dependencies

Handlers declare dependencies via type hints. No DI imports needed:

```python
# modules/orders/handlers.py
class CreateOrderHandler:
    def __init__(self, repo: OrderRepository, reader: UserReader) -> None:
        self._repo = repo
        self._reader = reader
```

The orders module imports identity to get access to `UserReader`:

```python
# modules/orders/module.py
orders_module = Module(
    name="orders",
    providers=[Provider(provide=OrderRepository, use_class=PgOrderRepository)],
    imports=[identity_module],
)
```

## Composition Root

One file that wires everything:

```python
# app/main.py
ctx = ApplicationContext(
    modules=[identity_module, orders_module],
    globals=[Provider(provide=Database, use_value=db)],
)

handler = ctx.resolve(CreateOrderHandler)
```

The handler gets `OrderRepository` from its own module, `UserReader` from identity (via import), and `Database` from globals. All auto-wired.
