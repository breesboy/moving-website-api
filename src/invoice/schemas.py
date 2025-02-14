import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel

class InvoiceRequestModel(BaseModel):
    booking_uid: uuid.UUID
    amount: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": 99.99,
                "booking_uid": "123e4567-e89b-12d3-a456-426614174001"
            }
        }
    }

class InvoiceCreateModel(BaseModel):
    booking_uid: uuid.UUID
    stripe_invoice_id: str
    amount: float
    status: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "booking_uid": "123e4567-e89b-12d3-a456-426614174001",
                "stripe_invoice_id": "in_1234567890",
                "amount": 99.99,
                "status": "pending"
            }
        }
    }

class InvoiceModel(BaseModel):
    uid: uuid.UUID
    booking_uid: uuid.UUID
    stripe_invoice_id: str
    amount: float
    status: str
    issued_at: datetime
    paid_at: datetime | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "booking_uid": "123e4567-e89b-12d3-a456-426614174001",
                "stripe_invoice_id": "in_1234567890",
                "amount": 99.99,
                "status": "pending",
                "issued_at": "2023-01-01T00:00:00Z",
                "paid_at": None
            }
        }
    }

