from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_session
from .pricing import PricingClient, get_pricing_client

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}")
def read_order(
    order_id: str,
    session: Session = Depends(get_session),
    pricing: PricingClient = Depends(get_pricing_client),
):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    order.total = pricing.quote(order.items)
    return order


@router.post("", status_code=201)
def create_order(
    payload: OrderCreate,
    session: Session = Depends(get_session),
    pricing: PricingClient = Depends(get_pricing_client),
):
    order = Order(items=payload.items, total=pricing.quote(payload.items))
    session.add(order)
    session.commit()
    return order
