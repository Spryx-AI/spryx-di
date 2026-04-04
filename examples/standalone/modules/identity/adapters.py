from __future__ import annotations

from modules.identity.ports import User, UserReader, UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def get_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)


class InMemoryUserReader(UserReader):
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get_by_id(self, user_id: str) -> User | None:
        return self._repo.get_by_id(user_id)
