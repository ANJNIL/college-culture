from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.cart import router as cart_router
from app.routes.wishlist import router as wishlist_router
from app.routes.orders import router as orders_router
from app.routes.payment import router as payment_router
from app.routes.ai import router as ai_router
from app.routes.config import router as config_router
from app.routes.unstop import router as unstop_router

__all__ = [
    "auth_router",
    "products_router",
    "cart_router",
    "wishlist_router",
    "orders_router",
    "payment_router",
    "ai_router",
    "config_router",
    "unstop_router",
]

