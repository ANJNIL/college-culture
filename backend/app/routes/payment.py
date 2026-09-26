from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    CreatePaymentOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse
)
from app.security.auth import get_optional_current_user
from app.security.rate_limiter import limiter
from app.services.products import product_service
from app.services.payment import payment_service
from app.database.supabase import db
from app.config import settings

router = APIRouter(prefix="/api/payment", tags=["Payments"])


@router.post("/create-order", response_model=CreatePaymentOrderResponse)
@limiter.limit("20/minute")
async def create_payment_order(
    request: Request,
    body: CreatePaymentOrderRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """
    CRITICAL SECURITY IMPLEMENTATION:
    1. Calculate order total strictly from database product prices.
    2. Generate Razorpay order on backend via Razorpay SDK with RAZORPAY_KEY_SECRET.
    3. Persist order record in database with razorpay_order_id.
    4. Return Razorpay order ID and public RAZORPAY_KEY_ID (never secret).
    """
    # 1. Price verification
    subtotal, shipping_amount, grand_total, validated_items = (
        await product_service.calculate_and_validate_order_totals(body.items)
    )

    # 2. Razorpay Order Generation
    receipt_id = f"rcpt_{current_user['id'][:8]}_{len(validated_items)}"
    razorpay_order = payment_service.create_order(
        amount_in_inr=grand_total,
        receipt=receipt_id,
        notes={
            "user_id": current_user["id"],
            "items_count": str(len(validated_items)),
            "platform": "college  culture Luxury Accessories"
        }
    )

    razorpay_order_id = razorpay_order["id"]

    # 3. Create database order
    order = await db.create_order(
        user_id=current_user["id"],
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        grand_total=grand_total,
        shipping_address=body.shipping_address.model_dump(),
        items=validated_items,
        payment_method="razorpay",
        razorpay_order_id=razorpay_order_id
    )

    # 4. Safe response (public key only)
    return CreatePaymentOrderResponse(
        order_id=order.id,
        razorpay_order_id=razorpay_order_id,
        amount_in_paise=razorpay_order["amount"],
        amount_in_inr=grand_total,
        currency="INR",
        razorpay_key_id=settings.RAZORPAY_KEY_ID
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
@limiter.limit("20/minute")
async def verify_payment(
    request: Request,
    body: VerifyPaymentRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """
    Verify HMAC SHA256 payment signature using RAZORPAY_KEY_SECRET on backend.
    Updates order status and confirms order upon signature match.
    """
    is_valid = payment_service.verify_payment_signature(
        razorpay_order_id=body.razorpay_order_id,
        razorpay_payment_id=body.razorpay_payment_id,
        razorpay_signature=body.razorpay_signature
    )

    if not is_valid:
        await db.update_order_payment(
            order_id=body.order_id,
            razorpay_payment_id=body.razorpay_payment_id,
            payment_status="failed",
            status="pending"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: Invalid transaction signature."
        )

    # Mark order as paid and confirmed
    await db.update_order_payment(
        order_id=body.order_id,
        razorpay_payment_id=body.razorpay_payment_id,
        payment_status="paid",
        status="confirmed"
    )

    # Empty user cart after verified payment
    await db.clear_cart(current_user["id"])

    return VerifyPaymentResponse(
        success=True,
        message="Payment successfully verified. Your order is confirmed.",
        order_id=body.order_id,
        status="confirmed"
    )
