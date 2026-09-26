from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.domain import Order, OrderItem, ShippingAddress


class OrderItemRequest(BaseModel):
    product_id: str
    selected_size: str
    quantity: int = Field(..., ge=1, le=50)


class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest] = Field(..., min_length=1)
    shipping_address: ShippingAddress
    payment_method: str = Field("razorpay", pattern="^(razorpay|cod)$")


class OrderListResponse(BaseModel):
    orders: List[Order]
    total: int
