from typing import Dict, Any, Optional
import razorpay
from fastapi import HTTPException, status
from app.config import settings


class RazorpayPaymentService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self._client: Optional[razorpay.Client] = None

    @property
    def client(self) -> razorpay.Client:
        if not self._client:
            if not self.key_id or not self.key_secret:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Razorpay payment gateway credentials are not configured on the server."
                )
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    def create_order(
        self,
        amount_in_inr: int,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new payment order with Razorpay.
        amount_in_inr is converted to paise (1 INR = 100 paise).
        """
        amount_in_paise = amount_in_inr * 100
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {"brand": "LIHAS Luxury Accessories"},
            "payment_capture": 1
        }
        try:
            order = self.client.order.create(data=data)
            return order
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to initialize payment order with payment gateway."
            )

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify the cryptographic signature returned after checkout.
        Authenticates that the payment actually succeeded on Razorpay.
        """
        try:
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            }
            # verify_payment_signature returns None on success or raises SignatureVerificationError
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception:
            return False


payment_service = RazorpayPaymentService()
