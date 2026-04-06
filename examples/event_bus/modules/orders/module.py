from __future__ import annotations

from modules.orders.adapters import InMemoryOrderRepository
from modules.orders.ports import OrderRepository
from spryx_di import ClassProvider, Module

orders_module = Module(
    name="orders",
    providers=[
        ClassProvider(provide=OrderRepository, use_class=InMemoryOrderRepository),
    ],
    exports=[],
)
