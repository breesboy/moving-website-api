from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import InvoiceCreateModel, InvoiceModel, InvoiceRequestModel
from sqlmodel import UUID, select,desc
from .models import Invoice
from datetime import datetime


class InvoiceService:
    # async def create_invoice(self, invoice_data: InvoiceCreateModel, session: AsyncSession):
    #     invoice_dict = invoice_data.model_dump()
                
    #     new_invoice = Invoice(**invoice_dict)
    #     session.add(new_invoice)
    #     await session.commit()
                
    #     return new_invoice
            
    async def get_invoices(self, session: AsyncSession):
        query = select(Invoice).order_by(desc(Invoice.created_at))
        result = await session.execute(query)
        invoices = result.scalars().all()
        return invoices
            
    async def get_invoice_by_id(self, invoice_id: str, session: AsyncSession):
        query = select(Invoice).where(Invoice.id == invoice_id)
        result = await session.execute(query)
        invoice = result.scalar_one_or_none()
        return invoice
    

    from src.invoice.models import Invoice 
    from sqlalchemy.ext.asyncio import AsyncSession

    async def create_invoice(self,session: AsyncSession, booking_uid: UUID, stripe_invoice_id: str, invoice_data:InvoiceRequestModel):
        new_invoice = Invoice(
            booking_uid=booking_uid,
            stripe_invoice_id=stripe_invoice_id,
            amount=invoice_data.amount,
            status="unpaid"
        )

        session.add(new_invoice)

        await session.commit()

        # Return a response
        return {"message": "Invoice created and sent to client"}
    
    
    async def update_invoice(self, invoice:Invoice, invoice_data: dict, session: AsyncSession):
		
        for k, v in invoice_data.items():
            setattr(invoice, k, v)

        await session.commit()
        return invoice
