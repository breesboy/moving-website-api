from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import CreateBooking,UpdateBooking,RescheduleBooking,UpdateBookingStatus,AddPayment
from sqlmodel import select,desc
from .models import Bookings
from datetime import datetime


class BookingService:
	async def create_new_booking(self,booking_data:CreateBooking, session: AsyncSession):
		bookings_data_dict = booking_data.model_dump()

		new_booking = Bookings(
			**bookings_data_dict
		)

		new_booking.moving_date = datetime.strptime(bookings_data_dict['moving_date'],"%Y-%m-%d %H:%M")
		new_booking.status = "Pending"

		session.add(new_booking)

		await session.commit()

		return new_booking

	async def get_all_bookings(self, session: AsyncSession):
		statement = select(Bookings).order_by(desc(Bookings.created_at))

		result = await session.exec(statement)

		result = result.all()

		return result


	async def get_user_bookings(self,user_uid : str, session: AsyncSession):
		statement = select(Bookings).where(Bookings.user_uid == user_uid)

		result = await session.exec(statement)

		result = result.all()
		
		return result



	async def get_booking(self,booking_uid : str, session: AsyncSession):
		statement = select(Bookings).where(Bookings.uid == booking_uid)

		result = await session.exec(statement)

		return result.first()


	async def update_booking(self, booking_uid : str, update_data : UpdateBooking, session: AsyncSession):
		booking_to_update = await self.get_booking(booking_uid,session)

		booking_update_dict = update_data.model_dump()

		for k, v in booking_update_dict.items():
			setattr(booking_to_update,k,v)


		await session.commit()

		return booking_to_update


	async def reschedule_booking(self, booking_uid : str, reschedule_data:RescheduleBooking, session: AsyncSession):
		booking_to_reschedule = await self.get_booking(booking_uid,session)

		booking_reschedule_dict = reschedule_data.model_dump()

		for k, v in booking_reschedule_dict.items():
			setattr(booking_to_reschedule,k,v)

		await session.commit()

		return booking_to_reschedule



	async def booking_status(self, booking_uid : str, booking_status_change_data:UpdateBookingStatus, session: AsyncSession):
		booking_status_change = await self.get_booking(booking_uid,session)


		if booking_status_change is None:
			return None


		booking_status_change_dict = booking_status_change_data.model_dump()

		for k, v in booking_status_change_dict.items():
			setattr(booking_status_change,k,v)

		await session.commit()

		return booking_status_change


	async def agreed_price(self, booking_uid : str, agreed_price_data:AddPayment, session: AsyncSession):
		booking_to_charge = await self.get_booking(booking_uid,session)

		booking_to_charge_dict = agreed_price_data.model_dump()

		for k, v in booking_to_charge_dict.items():
			setattr(booking_to_charge,k,v)

		await session.commit()

		return booking_to_charge



	async def cancel_booking(self, booking_uid : str, session: AsyncSession):
		booking_to_cancel = await self.get_booking(booking_uid,session)


		if booking_to_cancel is None:
			return None


		booking_cancel_dict = booking_to_cancel.model_dump()

		booking_cancel_dict['status'] = "cancelled"
		await session.commit()

		return booking_cancel_dict

	

	async def quick_update_booking(self, booking:Bookings, booking_data: dict, session: AsyncSession):
		
		for k, v in booking_data.items():
			setattr(booking, k, v)

		await session.commit()
		return booking



	# async def cancel_booking(self,booking_uid : str, session: AsyncSession):
	# 	booking_to_delete = await self.get_booking(booking_uid,session)

	# 	if booking_to_delete is None:
	# 		return None

	# 	await session.delete(booking_to_delete)

	# 	await session.commit()

	# 	return {}

