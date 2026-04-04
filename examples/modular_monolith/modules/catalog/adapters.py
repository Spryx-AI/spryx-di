from __future__ import annotations

from modules.catalog.domain import Product
from modules.catalog.ports import ProductReader, ProductRepository


class InMemoryProductRepository(ProductRepository):
    def __init__(self) -> None:
        self._products: dict[str, Product] = {}

    def save(self, product: Product) -> None:
        self._products[product.id] = product

    def get_by_id(self, product_id: str) -> Product | None:
        return self._products.get(product_id)


class InMemoryProductReader(ProductReader):
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def get_by_id(self, product_id: str) -> Product | None:
        return self._repo.get_by_id(product_id)

    def list_all(self) -> list[Product]:
        return []
