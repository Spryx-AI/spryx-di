from __future__ import annotations

from modules.billing.handlers import OnOrderCreatedGenerateInvoice
from modules.orders.events import OrderCreated
from spryx_di import EventListener, Module

billing_module = Module(
    name="billing",
    providers=[],
    listeners=[
        EventListener(event=OrderCreated, handler=OnOrderCreatedGenerateInvoice),
    ],
)
