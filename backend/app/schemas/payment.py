from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.orders import OrderItemRequest
from app.models.domain import ShippingAddress


class CreatePaymentOrderRequest(BaseModel):
    items: List[OrderItemRequest] = Field(..., min_length=1)
    shipping_address: ShippingAddress


class CreatePaymentOrderResponse(BaseModel):
    order_id: str
    razorpay_order_id: str
    amount_in_paise: int
    amount_in_inr: int
    currency: str = "INR"
    razorpay_key_id: str


class VerifyPaymentRequest(BaseModel):
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    success: bool
    message: str
    order_id: str
    status: str
