from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.domain import Product


class ProductListResponse(BaseModel):
    total: int
    categories: List[str]
    products: List[Product]


class ProductDetailResponse(BaseModel):
    product: Product
    related_products: List[Product] = Field(default_factory=list)


class ProductFilterQuery(BaseModel):
    category: Optional[str] = None
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    sort_by: Optional[str] = "default"  # default, priceLow, priceHigh, rating
    search: Optional[str] = None
