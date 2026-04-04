from __future__ import annotations

from modules.catalog.adapters import InMemoryProductReader, InMemoryProductRepository
from modules.catalog.ports import ProductReader, ProductRepository
from spryx_di import Module, Provider, Scope

catalog_module = Module(
    name="catalog",
    providers=[
        Provider(
            provide=ProductRepository,
            use_class=InMemoryProductRepository,
            scope=Scope.SINGLETON,
        ),
        Provider(provide=ProductReader, use_class=InMemoryProductReader, scope=Scope.SINGLETON),
    ],
    exports=[ProductReader],  # Only ProductReader is public
)
