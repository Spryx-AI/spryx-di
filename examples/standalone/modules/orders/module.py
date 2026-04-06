from __future__ import annotations

from modules.identity.ports import UserReader
from modules.notifications.ports import NotificationSender
from modules.orders.adapters import InMemoryOrderRepository
from modules.orders.ports import OrderRepository
from spryx_di import ClassProvider, Module

orders_module = Module(
    name="orders",
    providers=[
        ClassProvider(provide=OrderRepository, use_class=InMemoryOrderRepository),
    ],
    exports=[],
    imports=[UserReader, NotificationSender],
)
