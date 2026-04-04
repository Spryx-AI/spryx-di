"""Order handlers — demonstrate CROSS-MODULE dependency injection.

CreateOrderHandler depends on:
  - OrderRepository   (from orders module)
  - UserReader        (from identity module)
  - ProductReader     (from catalog module)

spryx-di resolves all of these automatically via __init__ type hints.
No manual wiring. No DI imports in this file.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.catalog.ports import ProductReader
from modules.identity.ports import UserReader
from modules.orders.domain import Order, OrderItem
from modules.orders.ports import OrderRepository


@dataclass(frozen=True)
class CreateOrderRequest:
    user_id: str
    items: list[tuple[str, int]]  # (product_id, quantity)


class CreateOrderHandler:
    """Creates an order — auto-wired with deps from 3 different modules."""

    def __init__(
        self,
        order_repo: OrderRepository,
        user_reader: UserReader,
        product_reader: ProductReader,
    ) -> None:
        self._order_repo = order_repo
        self._user_reader = user_reader
        self._product_reader = product_reader

    def handle(self, request: CreateOrderRequest) -> Order:
        # Resolve user from identity module
        user = self._user_reader.get_by_id(request.user_id)
        if user is None:
            msg = f"User {request.user_id} not found"
            raise ValueError(msg)

        # Resolve products from catalog module
        order_items: list[OrderItem] = []
        for product_id, quantity in request.items:
            product = self._product_reader.get_by_id(product_id)
            if product is None:
                msg = f"Product {product_id} not found"
                raise ValueError(msg)
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )

        # Create and persist order
        order = Order(
            id=str(uuid.uuid4()),
            user_id=user.id,
            user_name=user.name,
            items=order_items,
        )
        self._order_repo.save(order)
        return order


class ListUserOrdersHandler:
    """Lists orders for a user — depends on orders module only."""

    def __init__(self, order_repo: OrderRepository) -> None:
        self._order_repo = order_repo

    def handle(self, user_id: str) -> list[Order]:
        return self._order_repo.list_by_user(user_id)
