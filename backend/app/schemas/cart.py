from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.domain import CartItem


class AddToCartRequest(BaseModel):
    product_id: str
    selected_size: str = Field(..., min_length=1)
    quantity: int = Field(1, ge=1, le=50)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=0, le=50)


class CartSummaryResponse(BaseModel):
    items: List[CartItem]
    subtotal: int
    shipping_amount: int
    grand_total: int
    total_count: int
    free_shipping_threshold: int = 799
