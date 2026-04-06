from __future__ import annotations

from modules.notifications.handlers import OnOrderCreatedNotifyUser
from modules.orders.events import OrderCreated
from spryx_di import EventListener, ListenerScope, Module

notifications_module = Module(
    name="notifications",
    providers=[],
    listeners=[
        EventListener(
            event=OrderCreated,
            handler=OnOrderCreatedNotifyUser,
            scope=ListenerScope.ASYNC,
        ),
    ],
)
