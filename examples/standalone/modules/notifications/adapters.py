from __future__ import annotations

from modules.identity.ports import UserReader
from modules.notifications.ports import NotificationSender


class ConsoleNotificationSender(NotificationSender):
    """Sends notifications to stdout — depends on UserReader from identity module."""

    def __init__(self, user_reader: UserReader) -> None:
        self._user_reader = user_reader

    def send(self, user_id: str, message: str) -> None:
        user = self._user_reader.get_by_id(user_id)
        name = user.name if user else "Unknown"
        print(f"  [NOTIFICATION] -> {name}: {message}")
