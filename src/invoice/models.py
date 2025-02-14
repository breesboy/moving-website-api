from sqlmodel import SQLModel,Field,Column
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
import uuid


class Invoice(SQLModel, table=True):
	__tablename__ = "invoices"

	uid : uuid.UUID = Field(
		sa_column= Column(
			pg.UUID,
			nullable=False,
			primary_key=True,
			default=uuid.uuid4
		)
	)
	booking_uid : uuid.UUID = Field(foreign_key="bookings.uid",nullable=False)
	stripe_invoice_id : str
	amount : float
	status: str
	issued_at : datetime = Field(default_factory=datetime.now)
	paid_at : datetime = Field(default=None, nullable=True)


	def __repr__(self):
		return f"<Invoice of {self.booking_uid} for {self.amount}>"