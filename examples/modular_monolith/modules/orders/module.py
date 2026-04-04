from __future__ import annotations

from modules.catalog.module import catalog_module
from modules.identity.module import identity_module
from modules.orders.adapters import InMemoryOrderRepository
from modules.orders.ports import OrderRepository
from spryx_di import Module, Provider, Scope

orders_module = Module(
    name="orders",
    providers=[
        Provider(provide=OrderRepository, use_class=InMemoryOrderRepository, scope=Scope.SINGLETON),
    ],
    exports=[],
    imports=[identity_module, catalog_module],  # References, not strings
    # Handlers (CreateOrderHandler, ListUserOrdersHandler) are NOT registered.
    # They are auto-wired on resolve — their __init__ type hints are enough.
)
