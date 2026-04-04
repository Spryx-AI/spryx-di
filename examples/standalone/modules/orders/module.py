from __future__ import annotations

from modules.identity.module import identity_module
from modules.notifications.module import notifications_module
from modules.orders.adapters import InMemoryOrderRepository
from modules.orders.ports import OrderRepository
from spryx_di import Module, Provider, Scope

# orders importa identity e notifications via referencia direta (sem ciclo)
# Handlers NAO precisam de registro — sao auto-wired via type hints
orders_module = Module(
    name="orders",
    providers=[
        Provider(provide=OrderRepository, use_class=InMemoryOrderRepository, scope=Scope.SINGLETON),
    ],
    exports=[],
    imports=[identity_module, notifications_module],
)
