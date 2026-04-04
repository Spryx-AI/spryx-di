from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from spryx_di import (
    ApplicationContext,
    EventBus,
    EventHandler,
    EventListener,
    EventMetadata,
    InvalidListenerError,
    ListenerScope,
    MissingEventBackendError,
    Module,
    ValueProvider,
)
from spryx_di.events.backends.memory import InMemoryEventBackend
from spryx_di.events.handler import extract_event_type


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    amount: float


@dataclass(frozen=True)
class OrderCancelled:
    order_id: str


class NotificationService:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def notify(self, message: str) -> None:
        self.sent.append(message)


class OnOrderPlaced(EventHandler[OrderPlaced]):
    def __init__(self, notifications: NotificationService) -> None:
        self._notifications = notifications

    async def handle(self, event: OrderPlaced) -> None:
        await self._notifications.notify(f"Order {event.order_id} placed")


class OnOrderPlacedBilling(EventHandler[OrderPlaced]):
    def __init__(self) -> None:
        self.processed: list[str] = []

    async def handle(self, event: OrderPlaced) -> None:
        self.processed.append(event.order_id)


class OnOrderCancelled(EventHandler[OrderCancelled]):
    def __init__(self) -> None:
        self.cancelled: list[str] = []

    async def handle(self, event: OrderCancelled) -> None:
        self.cancelled.append(event.order_id)


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.get_event_loop().run_until_complete(coro)


class TestEventHandler:
    def test_base_handle_raises_not_implemented(self) -> None:
        handler: EventHandler[OrderPlaced] = EventHandler()
        with pytest.raises(NotImplementedError):
            _run(handler.handle(OrderPlaced(order_id="1", amount=10.0)))

    def test_subclass_is_valid_event_handler(self) -> None:
        assert issubclass(OnOrderPlaced, EventHandler)

    def test_extract_event_type(self) -> None:
        assert extract_event_type(OnOrderPlaced) is OrderPlaced

    def test_extract_event_type_different_handler(self) -> None:
        assert extract_event_type(OnOrderCancelled) is OrderCancelled

    def test_extract_event_type_fails_for_raw_base(self) -> None:
        with pytest.raises(TypeError, match="Cannot extract event type"):
            extract_event_type(EventHandler)  # type: ignore[arg-type]

    def test_extract_event_type_fails_for_non_generic_subclass(self) -> None:
        class BadHandler(EventHandler):  # type: ignore[type-arg]
            pass

        with pytest.raises(TypeError, match="Cannot extract event type"):
            extract_event_type(BadHandler)


class TestEventBusSyncDispatch:
    def test_publish_to_single_sync_handler(self) -> None:
        notifications = NotificationService()
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[
                        ValueProvider(provide=NotificationService, use_value=notifications),
                        OnOrderPlaced,
                    ],
                    listeners=[
                        EventListener(event=OrderPlaced, handler=OnOrderPlaced),
                    ],
                ),
            ],
        )
        bus = ctx.resolve(EventBus)
        _run(bus.publish(OrderPlaced(order_id="ord_1", amount=99.0)))
        assert notifications.sent == ["Order ord_1 placed"]

    def test_publish_to_multiple_sync_handlers(self) -> None:
        notifications = NotificationService()
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[
                        ValueProvider(provide=NotificationService, use_value=notifications),
                        OnOrderPlaced,
                        OnOrderPlacedBilling,
                    ],
                    listeners=[
                        EventListener(event=OrderPlaced, handler=OnOrderPlaced),
                        EventListener(event=OrderPlaced, handler=OnOrderPlacedBilling),
                    ],
                ),
            ],
        )
        bus = ctx.resolve(EventBus)
        _run(bus.publish(OrderPlaced(order_id="ord_2", amount=50.0)))
        assert notifications.sent == ["Order ord_2 placed"]

    def test_publish_with_no_handlers(self) -> None:
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[OnOrderPlaced, NotificationService],
                    listeners=[
                        EventListener(event=OrderPlaced, handler=OnOrderPlaced),
                    ],
                ),
            ],
        )
        bus = ctx.resolve(EventBus)
        _run(bus.publish(OrderCancelled(order_id="ord_3")))


class TestEventBusAsyncDispatch:
    def test_async_handler_dispatches_to_backend(self) -> None:
        backend = InMemoryEventBackend()
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[OnOrderPlaced, NotificationService],
                    listeners=[
                        EventListener(
                            event=OrderPlaced,
                            handler=OnOrderPlaced,
                            scope=ListenerScope.ASYNC,
                        ),
                    ],
                ),
            ],
            event_backend=backend,
        )
        bus = ctx.resolve(EventBus)
        _run(bus.publish(OrderPlaced(order_id="ord_async", amount=25.0)))

        assert len(backend.dispatched) == 1
        event, metadata = backend.dispatched[0]
        assert isinstance(event, OrderPlaced)
        assert metadata == EventMetadata(
            event_type="OrderPlaced",
            handler_type="OnOrderPlaced",
        )

    def test_mixed_sync_and_async_handlers(self) -> None:
        backend = InMemoryEventBackend()
        notifications = NotificationService()
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[
                        ValueProvider(provide=NotificationService, use_value=notifications),
                        OnOrderPlaced,
                        OnOrderPlacedBilling,
                    ],
                    listeners=[
                        EventListener(
                            event=OrderPlaced,
                            handler=OnOrderPlaced,
                            scope=ListenerScope.SYNC,
                        ),
                        EventListener(
                            event=OrderPlaced,
                            handler=OnOrderPlacedBilling,
                            scope=ListenerScope.ASYNC,
                        ),
                    ],
                ),
            ],
            event_backend=backend,
        )
        bus = ctx.resolve(EventBus)
        _run(bus.publish(OrderPlaced(order_id="ord_mix", amount=75.0)))
        assert notifications.sent == ["Order ord_mix placed"]
        assert len(backend.dispatched) == 1


class TestInMemoryEventBackend:
    def test_capture_dispatched_event(self) -> None:
        backend = InMemoryEventBackend()
        event = OrderPlaced(order_id="1", amount=10.0)
        metadata = EventMetadata(event_type="OrderPlaced", handler_type="OnOrderPlaced")
        _run(backend.dispatch(event, metadata))
        assert len(backend.dispatched) == 1
        assert backend.dispatched[0] == (event, metadata)

    def test_assert_published_passes(self) -> None:
        backend = InMemoryEventBackend()
        event = OrderPlaced(order_id="ord_1", amount=10.0)
        metadata = EventMetadata(event_type="OrderPlaced", handler_type="OnOrderPlaced")
        _run(backend.dispatch(event, metadata))
        backend.assert_published(OrderPlaced, order_id="ord_1")

    def test_assert_published_fails(self) -> None:
        backend = InMemoryEventBackend()
        event = OrderPlaced(order_id="ord_1", amount=10.0)
        metadata = EventMetadata(event_type="OrderPlaced", handler_type="OnOrderPlaced")
        _run(backend.dispatch(event, metadata))
        with pytest.raises(AssertionError, match="No OrderPlaced event"):
            backend.assert_published(OrderPlaced, order_id="ord_99")

    def test_clear(self) -> None:
        backend = InMemoryEventBackend()
        event = OrderPlaced(order_id="1", amount=10.0)
        metadata = EventMetadata(event_type="OrderPlaced", handler_type="OnOrderPlaced")
        _run(backend.dispatch(event, metadata))
        backend.clear()
        assert backend.dispatched == []


class TestEventListenerAndScope:
    def test_listener_scope_values(self) -> None:
        assert ListenerScope.SYNC.value == "sync"
        assert ListenerScope.ASYNC.value == "async"
        assert len(ListenerScope) == 2

    def test_create_sync_listener_default_scope(self) -> None:
        listener = EventListener(event=OrderPlaced, handler=OnOrderPlaced)
        assert listener.event is OrderPlaced
        assert listener.handler is OnOrderPlaced
        assert listener.scope is ListenerScope.SYNC

    def test_create_async_listener(self) -> None:
        listener = EventListener(
            event=OrderPlaced,
            handler=OnOrderPlaced,
            scope=ListenerScope.ASYNC,
        )
        assert listener.scope is ListenerScope.ASYNC

    def test_listener_is_frozen(self) -> None:
        listener = EventListener(event=OrderPlaced, handler=OnOrderPlaced)
        with pytest.raises(AttributeError):
            listener.event = OrderCancelled  # type: ignore[misc]


class TestBootValidation:
    def test_invalid_handler_not_extending_event_handler(self) -> None:
        class NotAHandler:
            pass

        with pytest.raises(InvalidListenerError, match="must extend EventHandler"):
            ApplicationContext(
                modules=[
                    Module(
                        name="bad",
                        providers=[NotAHandler],
                        listeners=[
                            EventListener(event=OrderPlaced, handler=NotAHandler),  # type: ignore[arg-type]
                        ],
                    ),
                ],
            )

    def test_async_listener_without_backend(self) -> None:
        with pytest.raises(MissingEventBackendError, match="no event_backend"):
            ApplicationContext(
                modules=[
                    Module(
                        name="orders",
                        providers=[OnOrderPlaced, NotificationService],
                        listeners=[
                            EventListener(
                                event=OrderPlaced,
                                handler=OnOrderPlaced,
                                scope=ListenerScope.ASYNC,
                            ),
                        ],
                    ),
                ],
            )

    def test_async_listener_with_backend_succeeds(self) -> None:
        backend = InMemoryEventBackend()
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[OnOrderPlaced, NotificationService],
                    listeners=[
                        EventListener(
                            event=OrderPlaced,
                            handler=OnOrderPlaced,
                            scope=ListenerScope.ASYNC,
                        ),
                    ],
                ),
            ],
            event_backend=backend,
        )
        assert ctx.resolve(EventBus) is not None

    def test_no_event_bus_when_no_listeners(self) -> None:
        ctx = ApplicationContext(
            modules=[
                Module(name="empty", providers=[]),
            ],
        )
        assert not ctx.container.has(EventBus)


class TestIntegration:
    def test_full_module_event_flow(self) -> None:
        notifications = NotificationService()
        backend = InMemoryEventBackend()

        order_module = Module(
            name="orders",
            providers=[
                ValueProvider(provide=NotificationService, use_value=notifications),
                OnOrderPlaced,
                OnOrderCancelled,
            ],
            exports=[NotificationService],
            listeners=[
                EventListener(
                    event=OrderPlaced,
                    handler=OnOrderPlaced,
                    scope=ListenerScope.SYNC,
                ),
                EventListener(
                    event=OrderCancelled,
                    handler=OnOrderCancelled,
                    scope=ListenerScope.ASYNC,
                ),
            ],
        )

        ctx = ApplicationContext(
            modules=[order_module],
            event_backend=backend,
        )

        bus = ctx.resolve(EventBus)

        _run(bus.publish(OrderPlaced(order_id="int_1", amount=100.0)))
        assert notifications.sent == ["Order int_1 placed"]

        _run(bus.publish(OrderCancelled(order_id="int_2")))
        assert len(backend.dispatched) == 1
        backend.assert_published(OrderCancelled, order_id="int_2")

    def test_event_bus_is_singleton(self) -> None:
        ctx = ApplicationContext(
            modules=[
                Module(
                    name="orders",
                    providers=[OnOrderPlaced, NotificationService],
                    listeners=[
                        EventListener(event=OrderPlaced, handler=OnOrderPlaced),
                    ],
                ),
            ],
        )
        bus1 = ctx.resolve(EventBus)
        bus2 = ctx.resolve(EventBus)
        assert bus1 is bus2
