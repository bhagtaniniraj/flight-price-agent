import logging
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Booking
from app.schemas import CheckoutRequest, CheckoutResponse, PaymentStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


def _get_stripe():
    """Return the stripe module, or raise a helpful error if not configured."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Payment gateway not configured. Set STRIPE_SECRET_KEY in your .env file.",
        )
    try:
        import stripe as _stripe
        _stripe.api_key = STRIPE_SECRET_KEY
        return _stripe
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="stripe package not installed. Run: pip install stripe",
        ) from exc


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout Session for a booking."""
    result = await db.execute(select(Booking).where(Booking.id == body.booking_id))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    stripe = _get_stripe()

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Flight Booking #{booking.booking_reference}",
                        },
                        "unit_amount": int(booking.total_price * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={"booking_id": str(booking.id)},
        )
    except Exception as exc:
        logger.error("Stripe session creation failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {exc}") from exc

    booking.stripe_session_id = session.id
    await db.commit()

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    stripe = _get_stripe()

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError as exc:
            logger.warning("Invalid Stripe webhook signature: %s", exc)
            raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc
    else:
        event = json.loads(payload)

    if event.get("type") == "checkout.session.completed":
        session_obj = event["data"]["object"]
        booking_id = int(session_obj.get("metadata", {}).get("booking_id", 0))
        if booking_id:
            result = await db.execute(select(Booking).where(Booking.id == booking_id))
            booking = result.scalars().first()
            if booking:
                booking.payment_status = "paid"
                await db.commit()
                logger.info("Payment confirmed for booking %s", booking_id)

    return {"received": True}


@router.get("/status/{booking_id}", response_model=PaymentStatusResponse)
async def get_payment_status(booking_id: int, db: AsyncSession = Depends(get_db)):
    """Get the payment status for a booking."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return PaymentStatusResponse(
        booking_id=booking.id,
        status=booking.payment_status,
        amount=booking.total_price,
    )
