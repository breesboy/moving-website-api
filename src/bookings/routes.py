from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timedelta

from src.auth.models import User
from src.bookings.schemas import Bookings, UpdateBooking,CreateBooking,UpdateBookingStatus,RescheduleBooking,AddPayment
from src.db.main import get_session
from .service import BookingService
from src.auth.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.mail import mail, create_message



booking_router = APIRouter()
booking_service = BookingService()
access_token_bearer = AccessTokenBearer()

user_role_checker = RoleChecker(['admin','user'])
admin_role_checker = RoleChecker(['admin'])



@booking_router.post("/new_booking", status_code=status.HTTP_201_CREATED, response_model=Bookings)
async def create_new_booking(booking_data: CreateBooking, session:AsyncSession = Depends(get_session)) -> dict:
	new_booking = await booking_service.create_new_booking(booking_data,session)

	email = new_booking.email
	names = new_booking.firstName + " " + booking_data.lastName
	booking_uid = new_booking.uid
	link = ""
	message = create_message(
        recipients=[email],
        subject="Booking Confirmation",
        template_name="verify-email.html",
        context={"names": names, "booking_uid": booking_uid, "link" : link},
    )
	await mail.send_message(message, template_name="booking-email.html")

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


# @booking_router.patch("/add_payment/{booking_uid}", response_model=Bookings)
# async def add_agreed_price(booking_uid:str, agreed_price_data: AddPayment, session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)) -> dict:
# 	agreed_price = await booking_service.agreed_price(booking_uid,agreed_price_data,session)

# 	if agreed_price is None:
# 		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

# 	else:
# 		return agreed_price




@booking_router.patch("/cancel_booking/{booking_uid}")
async def cancel_or_reject_booking(booking_uid:str, user: User = Depends(get_current_user), session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(user_role_checker)) -> dict:
	
	role = user.role
	user_uid = user.uid

	booking = await booking_service.get_booking(booking_uid,session)

	if booking is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	if role == "admin" and booking.status == "Pending":
		reject_booking = await booking_service.cancel_booking(booking_uid,"rejected",session)

		email = booking.email
		names = booking.firstName + " " + booking.lastName
		booking_uid = booking.uid
		link = ""
		message = create_message(
			recipients=[email],
			subject="Booking rejected",
			template_name="cancel_reject.html",
			context={"names": names, "booking_uid": booking_uid,"status":"rejected", "link" : link},
		)
		await mail.send_message(message, template_name="cancel_reject.html")

		return reject_booking

	elif user_uid == booking.user_uid and booking.status == "Pending":
		cancel_booking = await booking_service.cancel_booking(booking_uid,"cancelled",session)

		email = booking.email
		names = booking.firstName + " " + booking.lastName
		booking_uid = booking.uid
		link = ""
		message = create_message(
			recipients=[email],
			subject="Booking cancelled",
			template_name="cancel_reject.html",
			context={"names": names, "booking_uid": booking_uid,"status":"cancelled", "link" : link},
		)
		await mail.send_message(message, template_name="cancel_reject.html")
				
		return cancel_booking
		

	raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking is already comfirmed")

@booking_router.delete("/delete_booking/{booking_uid}")
async def delete_booking(booking_uid:str, user: User = Depends(get_current_user), session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(user_role_checker)) -> dict:
	
	user_uid = user.uid

	booking = await booking_service.get_booking(booking_uid,session)

	if booking is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

	if user_uid == booking.user_uid and booking.status == "Pending":
		await booking_service.delete_booking(booking_uid,session)

		return {"message": "Booking deleted"}
	
	else:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail= "Booking is under review.")

		

@booking_router.get("/dashboard/new-bookings")
async def get_new_bookings(session:AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
	now = datetime.utcnow()
	past_7_days = now - timedelta(days=7)
	prev_7_days = past_7_days - timedelta(days=7)
	return await booking_service.get_new_booking_count(now, past_7_days, prev_7_days, session)


@booking_router.get("/dashboard/total-revenue")
async def get_total_revenue(session: AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
    now = datetime.utcnow()
    past_7_days = now - timedelta(days=7)
    prev_7_days = past_7_days - timedelta(days=7)
    return await booking_service.get_total_revenue(now, past_7_days, prev_7_days, session)


@booking_router.get("/dashboard/pending-bookings")
async def get_total_pending_bookings(session: AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
    now = datetime.utcnow()
    past_7_days = now - timedelta(days=7)
    prev_7_days = past_7_days - timedelta(days=7)
    return await booking_service.get_total_pending_bookings_count(now, past_7_days, prev_7_days, session)


@booking_router.get("/dashboard/booking-statistics") 
async def get_admin_booking_statistics(session: AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker))-> dict:
    return await booking_service.get_monthly_booking_counts(session)


@booking_router.get("/dashboard/revenue-statistics")
async def get_admin_revenue_statistics(session: AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
    return await booking_service.get_monthly_revenue(session)


@booking_router.get("/dashboard/customer-bookings")
async def get_customer_booking_statistics(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    return await booking_service.get_customer_bookings(user.uid, session)


@booking_router.get("/dashboard/new-customers")
async def get_new_customers(session: AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
    
	today = datetime.today()
	first_day = today.replace(day=1)

	return await booking_service.get_new_customers(first_day,session)
    

@booking_router.get("/dashboard/avg-daily-bookings")
async def get_avg_daily_bookings(session: AsyncSession = Depends(get_session),token_details : dict =Depends(access_token_bearer),_:bool = Depends(admin_role_checker)):
	today = datetime.today()
	first_day = today.replace(day=1)
	days_so_far = today.day  

	return await booking_service.get_avg_daily_bookings(first_day,days_so_far,session)