"""Catalog handlers — notice: ZERO imports from spryx_di.

These handlers declare their dependencies via __init__ type hints.
The container auto-wires them at resolution time.
"""

from __future__ import annotations

from modules.catalog.domain import Product
from modules.catalog.ports import ProductReader


class ListProductsHandler:
    """Lists all products in the catalog."""

    def __init__(self, reader: ProductReader) -> None:
        self._reader = reader

    def handle(self) -> list[Product]:
        return self._reader.list_all()


class GetProductHandler:
    """Gets a single product by ID."""

    def __init__(self, reader: ProductReader) -> None:
        self._reader = reader

    def handle(self, product_id: str) -> Product | None:
        return self._reader.get_by_id(product_id)
