"""
Composition root — EventBus com sync e async listeners.

Demonstra:
  1. Evento OrderCreated publicado pelo handler de orders
  2. Sync listener: billing gera invoice imediatamente
  3. Async listener: notifications despacha pro backend
  4. InMemoryEventBackend captura eventos async (pra teste)
  5. Mesmo evento, multiplos listeners, modulos desacoplados
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from modules.billing.module import billing_module
from modules.notifications.module import notifications_module
from modules.orders.handlers import CreateOrderHandler
from modules.orders.module import orders_module

from spryx_di import ApplicationContext
from spryx_di.events.backends.memory import InMemoryEventBackend


async def main() -> None:
    print("=" * 60)
    print("spryx-di — EventBus Example")
    print("=" * 60)

    # ── 1. Compose modules com event backend ──
    print("\n[1] Composing modules with InMemoryEventBackend...")
    backend = InMemoryEventBackend()
    ctx = ApplicationContext(
        modules=[orders_module, billing_module, notifications_module],
        event_backend=backend,
    )
    print("    Modules: orders, billing, notifications")
    print("    Listeners:")
    print("      billing  -> OnOrderCreatedGenerateInvoice (SYNC)")
    print("      notifications -> OnOrderCreatedNotifyUser (ASYNC)")

    # ── 2. Resolve handler (auto-wired com EventBus) ──
    print("\n[2] Resolving CreateOrderHandler (deps: OrderRepository, EventBus)...")
    create_order = ctx.resolve(CreateOrderHandler)

    # ── 3. Criar pedido — dispara evento ──
    print("\n[3] Creating order — publishes OrderCreated event...")
    order = await create_order.handle("u1", "Notebook Dell", 2, Decimal("3500.00"))
    print(f"\n    Order #{order.id} created (total: R${order.total})")

    # ── 4. Verificar async backend ──
    print("\n[4] Checking async backend (InMemoryEventBackend)...")
    print(f"    Events dispatched to backend: {len(backend.dispatched)}")
    for payload, metadata in backend.dispatched:
        print(f"    - {metadata.event_type} -> {metadata.handler_type}")
        print(f"      payload: {payload}")

    # ── 5. Segundo pedido ──
    print("\n[5] Creating second order...")
    order2 = await create_order.handle("u2", "Monitor LG 27'", 1, Decimal("2200.00"))
    print(f"\n    Order #{order2.id} created (total: R${order2.total})")

    print(f"\n    Total async events: {len(backend.dispatched)}")
    backend.assert_published("OrderCreated", order_id=order.id)
    backend.assert_published("OrderCreated", order_id=order2.id)
    print("    assert_published passed for both orders!")

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
