from __future__ import annotations

from abc import ABC, abstractmethod

from modules.identity.domain import User


class UserReader(ABC):
    """Inbound port — read-only access to users."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def list_all(self) -> list[User]: ...


class UserRepository(ABC):
    """Outbound port — full CRUD for users."""

    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...
