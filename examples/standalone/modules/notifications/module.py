from __future__ import annotations

from modules.notifications.adapters import ConsoleNotificationSender
from modules.notifications.ports import NotificationSender
from spryx_di import Module, Provider, Scope, forward_ref

notifications_module = Module(
    name="notifications",
    providers=[
        Provider(
            provide=NotificationSender,
            use_class=ConsoleNotificationSender,
            scope=Scope.SINGLETON,
        ),
    ],
    exports=[NotificationSender],
    imports=[forward_ref("identity")],
)
