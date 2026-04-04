from __future__ import annotations

from fastapi import APIRouter
from modules.catalog.handlers import GetProductHandler, ListProductsHandler
from modules.orders.handlers import CreateOrderHandler, CreateOrderRequest, ListUserOrdersHandler

from spryx_di.ext.fastapi import Inject

router = APIRouter()


@router.get("/products")
def list_products(handler: ListProductsHandler = Inject(ListProductsHandler)) -> dict:
    products = handler.handle()
    return {"products": [p.__dict__ for p in products]}


@router.get("/products/{product_id}")
def get_product(
    product_id: str,
    handler: GetProductHandler = Inject(GetProductHandler),
) -> dict:
    product = handler.handle(product_id)
    if product is None:
        return {"error": "Product not found"}
    return {"product": product.__dict__}


@router.post("/orders")
def create_order(
    user_id: str,
    items: list[dict],
    handler: CreateOrderHandler = Inject(CreateOrderHandler),
) -> dict:
    request = CreateOrderRequest(
        user_id=user_id,
        items=[(i["product_id"], i["quantity"]) for i in items],
    )
    order = handler.handle(request)
    return {"order_id": order.id, "user": order.user_name, "total": str(order.total)}


@router.get("/users/{user_id}/orders")
def list_user_orders(
    user_id: str,
    handler: ListUserOrdersHandler = Inject(ListUserOrdersHandler),
) -> dict:
    orders = handler.handle(user_id)
    return {"orders": [{"id": o.id, "items": len(o.items)} for o in orders]}
