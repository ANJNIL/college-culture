from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    category: str
    price: int
    description: str
    material: str
    color: Optional[str] = "Steel / Metallic"
    style: Optional[str] = "Luxury Minimalist"
    image_url: str
    gallery: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    rating: float = 4.9
    reviews_count: int = 100
    stock: int = 50
    is_active: bool = True
    is_new: bool = False
    is_trending: bool = False
    created_at: Optional[str] = None


class User(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str = "customer"
    password_hash: str
    created_at: Optional[str] = None


class CartItem(BaseModel):
    id: str
    user_id: str
    product_id: str
    selected_size: str
    quantity: int = 1
    created_at: Optional[str] = None
    # Joined product info
    product: Optional[Product] = None


class WishlistItem(BaseModel):
    id: str
    user_id: str
    product_id: str
    created_at: Optional[str] = None
    product: Optional[Product] = None


class OrderItem(BaseModel):
    id: Optional[str] = None
    order_id: Optional[str] = None
    product_id: str
    product_name: str
    price: int
    quantity: int
    selected_size: str
    image_url: Optional[str] = None


class ShippingAddress(BaseModel):
    first_name: str
    last_name: str
    address: str
    city: str
    pincode: str
    phone: Optional[str] = None


class Order(BaseModel):
    id: str
    user_id: str
    order_number: str
    subtotal: int
    shipping_amount: int
    grand_total: int
    status: str = "pending"  # pending, confirmed, processing, shipped, delivered, cancelled
    payment_status: str = "pending"  # pending, paid, failed, refunded
    payment_method: str = "razorpay"  # razorpay, cod
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    shipping_address: Dict[str, Any] = Field(default_factory=dict)
    items: List[OrderItem] = Field(default_factory=list)
    created_at: Optional[str] = None
