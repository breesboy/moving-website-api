from pydantic import BaseModel
import uuid
from datetime import datetime,date
from typing import Optional, List



class Bookings(BaseModel):
	uid : uuid.UUID
	firstName : str
	lastName : str
	email : str
	phoneNumber : str
	pickup_address : Optional[str] = None
	dropoff_address : Optional[str] = None
	location : Optional[str] = None
	moving_date: datetime
	service : str
	sub_services: Optional[List[str]]	= None
	description : str
	status : str
	agreedPrice: str
	user_uid : Optional[uuid.UUID]
	created_at : datetime
	updated_at : datetime


class CreateBooking(BaseModel):
	firstName : str
	lastName : str
	email : str
	phoneNumber : str
	pickup_address : Optional[str] = None
	dropoff_address : Optional[str] = None
	location : Optional[str] = None
	moving_date: str
	service : str
	sub_services: Optional[List[str]]	= None
	description : str


class UpdateBooking(BaseModel):
	firstName : str
	lastName : str
	phoneNumber : str
	pickup_address : Optional[str] = None
	dropoff_address : Optional[str] = None
	location : Optional[str] = None
	moving_date: date
	description : str
	service : str


class RescheduleBooking(BaseModel):
	moving_date: date


class UpdateBookingStatus(BaseModel):
	status: str

class AddPayment(BaseModel):
	agreedPrice: str
