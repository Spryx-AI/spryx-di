from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationSender(ABC):
    @abstractmethod
    def send(self, user_id: str, message: str) -> None: ...
