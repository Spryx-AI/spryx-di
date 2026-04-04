# Quick Start

A working example in under 50 lines. Copy, paste, run.

```python
from spryx_di import ApplicationContext, ClassProvider, Module, ModuleBoundaryError


# --- Ports (interfaces) ---

class UserReader:
    def get(self, user_id: str) -> str:
        raise NotImplementedError

class UserRepository:
    def save(self, user_id: str) -> None:
        raise NotImplementedError


# --- Implementations ---

class PgUserReader(UserReader):
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get(self, user_id: str) -> str:
        return f"user:{user_id}"

class PgUserRepository(UserRepository):
    def save(self, user_id: str) -> None:
        print(f"saved {user_id}")


# --- Modules ---

identity_module = Module(
    name="identity",
    providers=[
        ClassProvider(provide=UserRepository, use_class=PgUserRepository),
        ClassProvider(provide=UserReader, use_class=PgUserReader),
    ],
    exports=[UserReader],  # UserRepository stays private
)


class OrderHandler:
    def __init__(self, reader: UserReader) -> None:
        self._reader = reader

    def handle(self) -> str:
        return self._reader.get("u1")

orders_module = Module(
    name="orders",
    providers=[],
    imports=[identity_module],
)


# --- Compose ---

ctx = ApplicationContext(modules=[identity_module, orders_module])

handler = ctx.resolve(OrderHandler)
print(handler.handle())  # "user:u1"

# Boundary enforcement
try:
    ctx.resolve_within(orders_module, UserRepository)
except ModuleBoundaryError as e:
    print(e)
    # Cannot resolve 'UserRepository' in module 'orders'.
    #   'UserRepository' is a provider of 'identity' but is not exported.
```
