from __future__ import annotations

from modules.orders.events import OrderCreated
from spryx_di import EventHandler


class OnOrderCreatedNotifyUser(EventHandler[OrderCreated]):
    async def handle(self, event: OrderCreated) -> None:
        print(
            f"  [NOTIFICATION] -> user {event.user_id}: "
            f"Pedido #{event.order_id} confirmado ({event.quantity}x {event.product})"
        )
