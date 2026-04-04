from __future__ import annotations

from modules.identity.adapters import InMemoryUserReader, InMemoryUserRepository
from modules.identity.ports import UserReader, UserRepository
from spryx_di import ClassProvider, Module, forward_ref

identity_module = Module(
    name="identity",
    providers=[
        ClassProvider(provide=UserRepository, use_class=InMemoryUserRepository),
        ClassProvider(provide=UserReader, use_class=InMemoryUserReader),
    ],
    exports=[UserReader],
    imports=[forward_ref("notifications")],
)
