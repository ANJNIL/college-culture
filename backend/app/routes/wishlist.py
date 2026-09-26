from fastapi import APIRouter, Depends
from app.schemas.wishlist import WishlistToggleRequest, WishlistResponse
from app.security.auth import get_optional_current_user
from app.database.supabase import db

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


@router.get("", response_model=WishlistResponse)
async def get_wishlist(current_user: dict = Depends(get_optional_current_user)):
    """Fetch customer's saved pieces."""
    user_id = current_user["id"]
    product_ids = await db.get_wishlist(user_id)
    items = []
    for pid in product_ids:
        p = await db.get_product_by_id(pid)
        if p:
            items.append(p)

    return WishlistResponse(
        product_ids=product_ids,
        items=items,
        total=len(items)
    )


@router.post("/toggle")
async def toggle_wishlist(
    body: WishlistToggleRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Toggle a piece in wishlist."""
    user_id = current_user["id"]
    is_saved = await db.toggle_wishlist(user_id, body.product_id)
    return {
        "success": True,
        "is_saved": is_saved,
        "product_id": body.product_id,
        "message": "Saved to wishlist" if is_saved else "Removed from wishlist"
    }
