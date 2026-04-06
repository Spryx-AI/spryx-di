from __future__ import annotations

from modules.orders.events import OrderCreated
from spryx_di import EventHandler


class OnOrderCreatedGenerateInvoice(EventHandler[OrderCreated]):
    async def handle(self, event: OrderCreated) -> None:
        print(
            f"  [BILLING] Invoice generated for order #{event.order_id}: "
            f"R${event.total} ({event.quantity}x {event.product})"
        )
