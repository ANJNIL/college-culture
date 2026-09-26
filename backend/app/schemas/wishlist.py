from typing import List
from pydantic import BaseModel
from app.models.domain import Product


class WishlistToggleRequest(BaseModel):
    product_id: str


class WishlistResponse(BaseModel):
    product_ids: List[str]
    items: List[Product]
    total: int
