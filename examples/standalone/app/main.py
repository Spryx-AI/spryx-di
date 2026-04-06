"""
Composition root — sem FastAPI, uso direto do container.

Demonstra:
  1. ApplicationContext com 3 modulos
  2. Port-based imports (types como contratos entre modulos)
  3. resolve() para obter handlers auto-wired
  4. resolve_within() com boundary enforcement
  5. ModuleBoundaryError quando fronteira e violada
  6. Teste inline sem mocks — Container com fakes
"""

from __future__ import annotations

from modules.identity.module import identity_module
from modules.identity.ports import User, UserReader, UserRepository
from modules.notifications.module import notifications_module
from modules.notifications.ports import NotificationSender
from modules.orders.handlers import CreateOrderHandler, ListUserOrdersHandler
from modules.orders.module import orders_module
from modules.orders.ports import OrderRepository

from spryx_di import ApplicationContext, Container, ModuleBoundaryError


def main() -> None:
    print("=" * 60)
    print("spryx-di — Standalone Example (sem FastAPI)")
    print("=" * 60)

    # ── 1. Compose modules ──
    print("\n[1] Composing modules...")
    ctx = ApplicationContext(
        modules=[identity_module, notifications_module, orders_module],
    )
    print("    Modules: identity, notifications, orders")
    print("    imports: notifications -> UserReader, orders -> UserReader + NotificationSender")

    # ── 2. Seed data ──
    print("\n[2] Seeding data...")
    user_repo = ctx.resolve(UserRepository)
    user_repo.save(User(id="u1", name="Ana Silva", email="ana@spryx.ai"))
    user_repo.save(User(id="u2", name="Carlos Lima", email="carlos@spryx.ai"))
    print("    Users: Ana Silva, Carlos Lima")

    # ── 3. Resolve handlers (auto-wired) ──
    print("\n[3] Resolving handlers (auto-wired via type hints)...")
    create_order = ctx.resolve(CreateOrderHandler)
    list_orders = ctx.resolve(ListUserOrdersHandler)
    print("    CreateOrderHandler deps: OrderRepository, UserReader, NotificationSender")
    print("    ListUserOrdersHandler deps: OrderRepository")

    # ── 4. Use handlers ──
    print("\n[4] Creating orders...")
    order1 = create_order.handle("u1", "Notebook Dell", 1)
    order2 = create_order.handle("u2", "Monitor LG 27'", 2)
    order3 = create_order.handle("u1", "Teclado Mecanico", 1)

    print(f"\n    Orders created: {order1.id}, {order2.id}, {order3.id}")

    # ── 5. List orders ──
    print("\n[5] Listing orders for Ana (u1)...")
    ana_orders = list_orders.handle("u1")
    for o in ana_orders:
        print(f"    #{o.id}: {o.quantity}x {o.product}")

    # ── 6. Boundary enforcement ──
    print("\n[6] Testing module boundaries...")

    # OK: orders module can access UserReader (exported by identity, imported by orders)
    reader = ctx.resolve_within(orders_module, UserReader)
    print(f"    resolve_within(orders, UserReader) -> OK ({type(reader).__name__})")

    # FAIL: orders module cannot access UserRepository (private to identity)
    try:
        ctx.resolve_within(orders_module, UserRepository)
        print("    resolve_within(orders, UserRepository) -> ERROR: should have raised!")
    except ModuleBoundaryError as e:
        print("    resolve_within(orders, UserRepository) -> ModuleBoundaryError")
        print(f"      {e}")

    # ── 7. Testing with fakes (sem mocks) ──
    print("\n[7] Testing with fakes (Container puro)...")

    class FakeUserReader(UserReader):
        def get_by_id(self, user_id: str) -> User | None:
            return User(id=user_id, name="Fake User", email="fake@test.com")

    class FakeNotificationSender(NotificationSender):
        def __init__(self) -> None:
            self.sent: list[tuple[str, str]] = []

        def send(self, user_id: str, message: str) -> None:
            self.sent.append((user_id, message))

    class FakeOrderRepo(OrderRepository):
        def __init__(self) -> None:
            self.orders: list[object] = []

        def save(self, order: object) -> None:
            self.orders.append(order)

        def list_by_user(self, user_id: str) -> list:
            return []

    # Container puro — sem ApplicationContext, sem modulos
    test_container = Container()
    test_container.instance(UserReader, FakeUserReader())
    fake_notifier = FakeNotificationSender()
    test_container.instance(NotificationSender, fake_notifier)
    test_container.instance(OrderRepository, FakeOrderRepo())

    handler = test_container.resolve(CreateOrderHandler)
    order = handler.handle("u99", "Test Product", 3)

    assert order.product == "Test Product"
    assert order.quantity == 3
    assert len(fake_notifier.sent) == 1
    assert "u99" in fake_notifier.sent[0][0]
    print("    All assertions passed!")

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
