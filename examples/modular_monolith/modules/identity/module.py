from __future__ import annotations

from modules.identity.adapters import InMemoryUserReader, InMemoryUserRepository
from modules.identity.ports import UserReader, UserRepository
from spryx_di import Module, Provider, Scope

identity_module = Module(
    name="identity",
    providers=[
        Provider(provide=UserRepository, use_class=InMemoryUserRepository, scope=Scope.SINGLETON),
        Provider(provide=UserReader, use_class=InMemoryUserReader, scope=Scope.SINGLETON),
    ],
    exports=[UserReader],  # Only UserReader is public — UserRepository stays private
)
