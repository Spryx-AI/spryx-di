from __future__ import annotations

from modules.catalog.domain import Product
from modules.catalog.ports import ProductReader


class ListProductsHandler:
    def __init__(self, reader: ProductReader) -> None:
        self._reader = reader

    def handle(self) -> list[Product]:
        return self._reader.list_all()


class GetProductHandler:
    def __init__(self, reader: ProductReader) -> None:
        self._reader = reader

    def handle(self, product_id: str) -> Product | None:
        return self._reader.get_by_id(product_id)
