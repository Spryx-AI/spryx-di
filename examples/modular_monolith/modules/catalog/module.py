from __future__ import annotations

from modules.catalog.adapters import InMemoryProductReader, InMemoryProductRepository
from modules.catalog.ports import ProductReader, ProductRepository
from spryx_di import ClassProvider, Module

catalog_module = Module(
    name="catalog",
    providers=[
        ClassProvider(provide=ProductRepository, use_class=InMemoryProductRepository),
        ClassProvider(provide=ProductReader, use_class=InMemoryProductReader),
    ],
    exports=[ProductReader],
)
