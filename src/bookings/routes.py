from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.bookings.schemas import Bookings, UpdateBooking,CreateBooking,UpdateBookingStatus,RescheduleBooking,AddPayment
from src.db.main import get_session
from .service import BookingService
from src.auth.dependencies import AccessTokenBearer, RoleChecker


booking_router = APIRouter()
booking_service = BookingService()
access_token_bearer = AccessTokenBearer()

user_role_checker = RoleChecker(['admin','user'])
admin_role_checker = RoleChecker(['admin'])



@booking_router.post("/new_booking", status_code=status.HTTP_201_CREATED, response_model=Bookings)
async def create_new_booking(booking_data: CreateBooking, session:AsyncSession = Depends(get_session),) -> dict:
	new_booking = await booking_service.create_new_booking(booking_data,session)

	return new_booking


@booking_router.get("/get_all_bookings", response_model = List[Bookings])
async def get_all_bookings(session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
	bookings = await booking_service.get_all_bookings(session)

	return bookings


@booking_router.get("/get_booking/{booking_uid}", response_model = Bookings)
async def get_booking(booking_uid:str, session:AsyncSession = Depends(get_session)):
	booking = await booking_service.get_booking(booking_uid,session)

	if booking is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	else:
		return booking

@booking_router.get("/get_user_bookings/{user_uid}", response_model = List[Bookings])
async def get_user_bookings(user_uid:str, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(user_role_checker)):
	bookings = await booking_service.get_user_bookings(user_uid,session)

	if bookings is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Bookings not found")

	else:
		return bookings


@booking_router.patch("/update_booking/{booking_uid}", response_model=Bookings)
async def update_booking(booking_uid:str, update_booking_data: UpdateBooking, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(user_role_checker)) -> dict:
	update_booking = await booking_service.update_booking(booking_uid,update_booking_data,session)

	if update_booking is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	else:
		return update_booking



@booking_router.patch("/reschedule_booking/{booking_uid}", response_model=Bookings)
async def reschedule_booking(booking_uid:str, reschedule_booking_data: RescheduleBooking, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(user_role_checker)) -> dict:
	reschedule_booking = await booking_service.reschedule_booking(booking_uid,reschedule_booking_data,session)

	if reschedule_booking is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	else:
		return reschedule_booking

@booking_router.patch("/booking_status/{booking_uid}", response_model=Bookings)
async def update_booking_status(booking_uid:str, booking_status_data: UpdateBookingStatus, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)) -> dict:
	booking_status = await booking_service.booking_status(booking_uid,booking_status_data,session)

	if booking_status is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	else:
		return booking_status


@booking_router.patch("/add_payment/{booking_uid}", response_model=Bookings)
async def add_agreed_price(booking_uid:str, agreed_price_data: AddPayment, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)) -> dict:
	agreed_price = await booking_service.agreed_price(booking_uid,agreed_price_data,session)

	if agreed_price is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	else:
		return agreed_price




@booking_router.patch("/cancel_booking/{booking_uid}", response_model=Bookings)
async def cancel_booking(booking_uid:str, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(user_role_checker)) -> dict:
	cancel_booking = await booking_service.cancel_booking(booking_uid,session)

	if cancel_booking is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	else:
		return cancel_booking




# @booking_router.put("/", status_code=status.HTTP_204_NO_CONTENT)
# async def shit_bookingsssss(booking_uid:str, session:AsyncSession = Depends(get_session)):
# 	cancel_booking = await booking_service.cancel_booking(booking_uid,session)

# 	if cancel_booking is None:
# 		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")


# 	else:
# 		return {}

