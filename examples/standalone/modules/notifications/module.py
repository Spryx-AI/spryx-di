from __future__ import annotations

from modules.identity.ports import UserReader
from modules.notifications.adapters import ConsoleNotificationSender
from modules.notifications.ports import NotificationSender
from spryx_di import ClassProvider, Module

notifications_module = Module(
    name="notifications",
    providers=[
        ClassProvider(provide=NotificationSender, use_class=ConsoleNotificationSender),
    ],
    exports=[NotificationSender],
    imports=[UserReader],
)
