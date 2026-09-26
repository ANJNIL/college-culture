from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.orders import CreateOrderRequest, OrderListResponse
from app.security.auth import get_optional_current_user, get_current_user
from app.database.supabase import db
from app.services.products import product_service
from app.models.domain import Order

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("/create", response_model=Order)
async def create_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """
    Create a new customer order.
    Calculates order totals strictly on backend with database product prices.
    """
    subtotal, shipping_amount, grand_total, validated_items = (
        await product_service.calculate_and_validate_order_totals(body.items)
    )

    order = await db.create_order(
        user_id=current_user["id"],
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        grand_total=grand_total,
        shipping_address=body.shipping_address.model_dump(),
        items=validated_items,
        payment_method=body.payment_method,
    )

    # Clear user cart upon creating order
    await db.clear_cart(current_user["id"])
    return order


@router.get("", response_model=OrderListResponse)
async def list_orders(current_user: dict = Depends(get_optional_current_user)):
    """Retrieve orders for the current user."""
    orders = await db.get_orders_for_user(current_user["id"])
    return OrderListResponse(orders=orders, total=len(orders))


@router.get("/{order_id}", response_model=Order)
async def get_order_details(
    order_id: str,
    current_user: dict = Depends(get_optional_current_user)
):
    """Retrieve details for a specific order with authorization check."""
    order = await db.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' was not found."
        )

    # Authorization: Customer can only view their own order
    if order.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this order."
        )

    return order
