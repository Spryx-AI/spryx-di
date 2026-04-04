from __future__ import annotations

from abc import ABC, abstractmethod

from modules.catalog.domain import Product


class ProductReader(ABC):
    """Inbound port — read-only access to products."""

    @abstractmethod
    def get_by_id(self, product_id: str) -> Product | None: ...

    @abstractmethod
    def list_all(self) -> list[Product]: ...


class ProductRepository(ABC):
    """Outbound port — full CRUD for products."""

    @abstractmethod
    def save(self, product: Product) -> None: ...

    @abstractmethod
    def get_by_id(self, product_id: str) -> Product | None: ...
