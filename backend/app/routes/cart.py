from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.cart import AddToCartRequest, UpdateCartItemRequest, CartSummaryResponse
from app.security.auth import get_optional_current_user
from app.database.supabase import db
from app.services.products import FREE_SHIPPING_THRESHOLD, STANDARD_SHIPPING_FEE

router = APIRouter(prefix="/api/cart", tags=["Cart"])


@router.get("", response_model=CartSummaryResponse)
async def get_cart(current_user: dict = Depends(get_optional_current_user)):
    """Retrieve items in customer's cart with calculated subtotal and shipping."""
    user_id = current_user["id"]
    items = await db.get_cart(user_id)

    subtotal = sum(item.product.price * item.quantity for item in items if item.product)
    total_count = sum(item.quantity for item in items)
    shipping_amount = 0 if (subtotal >= FREE_SHIPPING_THRESHOLD or subtotal == 0) else STANDARD_SHIPPING_FEE
    grand_total = subtotal + shipping_amount

    return CartSummaryResponse(
        items=items,
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        grand_total=grand_total,
        total_count=total_count,
        free_shipping_threshold=FREE_SHIPPING_THRESHOLD
    )


@router.post("/add")
async def add_to_cart(
    body: AddToCartRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Add a piece to the shopping bag."""
    user_id = current_user["id"]
    item = await db.add_to_cart(
        user_id=user_id,
        product_id=body.product_id,
        size=body.selected_size,
        quantity=body.quantity
    )
    return {"success": True, "item": item}


@router.patch("/update")
async def update_cart_quantity(
    product_id: str = Query(...),
    selected_size: str = Query(...),
    quantity: int = Query(..., ge=0, le=50),
    current_user: dict = Depends(get_optional_current_user)
):
    """Update item quantity or remove when zero."""
    user_id = current_user["id"]
    success = await db.update_cart_quantity(user_id, product_id, selected_size, quantity)
    return {"success": success}


@router.delete("/remove")
async def remove_from_cart(
    product_id: str = Query(...),
    selected_size: str = Query(...),
    current_user: dict = Depends(get_optional_current_user)
):
    """Remove a specific piece from cart."""
    user_id = current_user["id"]
    success = await db.remove_from_cart(user_id, product_id, selected_size)
    return {"success": success}


@router.delete("/clear")
async def clear_cart(current_user: dict = Depends(get_optional_current_user)):
    """Empty cart after successful checkout."""
    user_id = current_user["id"]
    success = await db.clear_cart(user_id)
    return {"success": success}
