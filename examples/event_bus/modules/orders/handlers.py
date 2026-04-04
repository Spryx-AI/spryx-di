from __future__ import annotations

import uuid
from decimal import Decimal

from modules.orders.events import OrderCreated
from modules.orders.ports import Order, OrderRepository
from spryx_di.events import EventBus


class CreateOrderHandler:
    def __init__(self, order_repo: OrderRepository, event_bus: EventBus) -> None:
        self._order_repo = order_repo
        self._event_bus = event_bus

    async def handle(self, user_id: str, product: str, quantity: int, price: Decimal) -> Order:
        order = Order(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            product=product,
            quantity=quantity,
            total=price * quantity,
        )
        self._order_repo.save(order)

        await self._event_bus.publish(
            OrderCreated(
                order_id=order.id,
                user_id=order.user_id,
                product=order.product,
                quantity=order.quantity,
                total=order.total,
            )
        )
        return order
