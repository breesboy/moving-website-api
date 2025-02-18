from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status, Request
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.bookings.service import BookingService
import stripe
from src.config import Config

from .schemas import InvoiceCreateModel, InvoiceRequestModel
from src.db.main import get_session
from .service import InvoiceService
from src.auth.dependencies import AccessTokenBearer, RoleChecker


access_token_bearer = AccessTokenBearer()
invoice_service = InvoiceService()
invoice_router = APIRouter()
booking_service = BookingService()

STRIPE_SECRET_KEY = Config.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = Config.STRIPE_WEBHOOK_SECRET
stripe.api_key = STRIPE_SECRET_KEY

admin_role_checker = RoleChecker(['admin'])


# @invoice_router.post("/create-invoice", status_code=status.HTTP_201_CREATED, response_model=InvoiceModel)
# async def create_invoice(invoice_data: InvoiceCreateModel, session: AsyncSession = Depends(get_session)) -> dict:
#         new_invoice = await invoice_service.create_invoice(invoice_data, session)
#         return new_invoice

@invoice_router.post("/create-invoice")
async def create_invoice(invoice_data: InvoiceRequestModel, session: AsyncSession = Depends(get_session)):

    booking_uid = invoice_data.booking_uid

    booking = await booking_service.get_booking(booking_uid,session)

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

    if not booking.email:
        raise HTTPException(status_code=400, detail="Client email is required for invoicing")

    # Check for valid invoice amount
    if invoice_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invoice amount must be greater than zero")

    # Step 1: Check if Customer Already Exists in Stripe
    existing_customers = stripe.Customer.list(email=booking.email).get("data", [])
    client_name = booking.firstName + " " + booking.lastName
    if existing_customers:
        customer_id = existing_customers[0]["id"]  # Use existing customer ID
    else:
        customer = stripe.Customer.create(
            email=booking.email,
            name=client_name
        )
        customer_id = customer.id

    # Step 2: Create a Stripe Invoice (Before Adding Items)
    stripe_invoice = stripe.Invoice.create(
        customer=customer_id,
        collection_method="send_invoice",
        days_until_due=1  # Invoice is due in 7 days
    )

    # Step 3: Create a Stripe Invoice Item (This must be linked to the same customer & invoice)
    stripe.InvoiceItem.create(
        customer=customer_id,
        invoice=stripe_invoice.id,  # Explicitly attach to the created invoice
        amount=int(invoice_data.amount * 100),  # Convert dollars to cents
        currency="cad",
        description=f"Invoice for Booking #{booking.uid}"
    )

    # Step 4: **Finalize the Invoice to Make It Payable**
    finalized_invoice = stripe.Invoice.finalize_invoice(stripe_invoice.id, auto_advance=True)

    # Step 5: **Force Immediate Invoice Send**
    try:
        stripe.Invoice.send_invoice(finalized_invoice.id)  # Ensures email is sent immediately
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=500, detail="Failed to send invoice immediately. Check Stripe dashboard.")

    booking = await booking_service.get_booking(booking_uid,session)
    await booking_service.quick_update_booking(booking, {"status": "invoiced"}, session)

    # Save Invoice Details to Database
    await invoice_service.create_invoice(session, booking_uid, stripe_invoice.id, invoice_data)

    return {
            "message": "Invoice created and sent",
            "invoice_id": finalized_invoice.id,
            "amount": invoice_data.amount,
            "status": "unpaid",
            "stripe_invoice_url": finalized_invoice.hosted_invoice_url
        }


@invoice_router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle "invoice.paid" event
    if event["type"] == "invoice.paid":
        invoice_data = event["data"]["object"]
        invoice_id = invoice_data["id"]
        
        # Find invoice in DB
        invoice = await invoice_service.get_invoice_by_id(invoice_id,session)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found in database")

        # Update invoice status
        paid_at_timestamp = invoice_data["status_transitions"]["paid_at"]
        paid_datetime = datetime.utcfromtimestamp(paid_at_timestamp)        
        invoice_status = "paid"
        await invoice_service.update_invoice(invoice, {"status": invoice_status}, session)
        await invoice_service.update_invoice(invoice, {"paid_at": paid_datetime}, session)

        # Update booking status to "confirmed"
        booking_uid = invoice.booking_uid
        booking = await booking_service.get_booking(booking_uid,session)
        await booking_service.quick_update_booking(booking, {"status": "confirmed"}, session)
        
    return {"status": "success"}
