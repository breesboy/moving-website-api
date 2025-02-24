from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import CreateBooking,UpdateBooking,RescheduleBooking,UpdateBookingStatus,AddPayment
from sqlmodel import select,desc
from sqlalchemy import func,cast,Numeric,extract
from .models import Bookings
from datetime import datetime

from src.auth.services import UserService

user_service = UserService()


class BookingService:
	async def create_new_booking(self,booking_data:CreateBooking, session: AsyncSession):
		bookings_data_dict = booking_data.model_dump()

		new_booking = Bookings(
			**bookings_data_dict
		)

		new_booking.moving_date = datetime.strptime(bookings_data_dict['moving_date'],"%Y-%m-%d %H:%M")
		new_booking.status = "Pending"

		if new_booking.user_uid is None:
			user = await user_service.get_user_by_email(new_booking.email,session)
			if user:
				new_booking.user_uid = user.uid


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

		booking_to_reschedule.moving_date = datetime.strptime(booking_reschedule_dict['moving_date'],"%Y-%m-%d %H:%M")

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

	async def link_booking_to_user(self, user_uid:UUID,user_email:str, session: AsyncSession):
		statement = select(Bookings).where(Bookings.email == user_email)

		result = await session.exec(statement)
		bookings = result.all()  

		if bookings:
			for booking in bookings:
				booking.user_uid = user_uid

			await session.commit()
		return bookings




	async def get_sum_or_count(session: AsyncSession, column, filter_status=None, past_7_days=None, prev_7_days=None):
		"""
		General function to get total sum or count, plus 7-day growth if needed.

		:param session: Async database session
		:param column: Column to aggregate (e.g., func.count() or func.sum(Bookings.price))
		:param filter_status: Optional booking status filter (e.g., "completed")
		:param past_7_days: Timestamp for last 7 days (optional)
		:param prev_7_days: Timestamp for prior 7-day period (optional)
		"""
		filters = []
		prev_filters = []

		if filter_status:
			filters.append(Bookings.status == filter_status)
			prev_filters.append(Bookings.status == filter_status)

		statement = select(column).where(*filters)
		result = await session.exec(statement)
		total_value = result.first() or 0 		
		if past_7_days and prev_7_days:

			statement = select(column).where(Bookings.created_at >= past_7_days, *filters)
			result = await session.exec(statement)
			current_value = result.first() or 0	

			statement = select(column).where(
                Bookings.created_at >= prev_7_days, 
                Bookings.created_at < past_7_days, 
                *prev_filters
            )
			result = await session.exec(statement)
			previous_value = result.first() or 0			

			growth = 100 if previous_value == 0 and current_value > 0 else (
                ((current_value - previous_value) / previous_value) * 100 if previous_value > 0 else 0
            )

			return {"total_value": round(total_value, 2),"previous_7_days": round(previous_value,2), "last_7_days": round(current_value, 2), "growth": round(growth, 2)}
        
		return {"total_value": round(total_value, 2)}


	async def get_new_booking_count(self,now, past_7_days, prev_7_days, session: AsyncSession):
		return await BookingService.get_sum_or_count(session, func.count(Bookings.uid), past_7_days=past_7_days, prev_7_days=prev_7_days)


	async def get_total_revenue(self, now, past_7_days, prev_7_days, session: AsyncSession):
		return await BookingService.get_sum_or_count(session, func.sum(cast(Bookings.agreedPrice, Numeric)), filter_status="confirmed", past_7_days=past_7_days, prev_7_days=prev_7_days)
	
	
	async def get_total_pending_bookings_count(self, now, past_7_days, prev_7_days, session: AsyncSession):
		return await BookingService.get_sum_or_count(session, func.count(Bookings.uid), filter_status="invoiced", past_7_days=past_7_days, prev_7_days=prev_7_days)



	async def get_monthly_booking_counts(self,session: AsyncSession):

		current_year = datetime.utcnow().year

		statement = (
			select(
				extract('month', Bookings.created_at).label('month'),
				func.count().label('count')
			)
			.where(func.extract('year', Bookings.created_at) == current_year)
			.group_by('month')
			.order_by('month')
		)

		result = await session.exec(statement)
		data = result.all()

		bookings_per_month = {int(row.month): row.count for row in data}

		monthly_stats = [{"month": month, "count": bookings_per_month.get(month, 0)} for month in range(1, 13)]

		return {"data": monthly_stats}



	async def get_monthly_revenue(self,session: AsyncSession):
		""" Fetches the total revenue for each month of the current year """
		current_year = datetime.utcnow().year

		statement = (
			select(
				extract('month', Bookings.created_at).label('month'),
				func.sum(cast(Bookings.agreedPrice, Numeric)).label('revenue')
			)
			.where(
				func.extract('year', Bookings.created_at) == current_year,
				Bookings.status == "confirmed"  # Only consider completed bookings
			)
			.group_by('month')
			.order_by('month')
		)

		result = await session.exec(statement)
		data = result.all()

		revenue_per_month = {int(row.month): row.revenue for row in data}

		monthly_revenue_stats = [{"month": month, "revenue": revenue_per_month.get(month, 0)} for month in range(1, 13)]

		return {"data": monthly_revenue_stats}


	async def get_customer_bookings(self,customer_id: int, session: AsyncSession):
		""" Fetches the number of bookings for each month for a specific customer """
		current_year = datetime.utcnow().year

		statement = (
			select(
				extract('month', Bookings.created_at).label('month'),
				func.count().label('total_bookings')
			)
			.where(
				func.extract('year', Bookings.created_at) == current_year,
				Bookings.user_uid == customer_id  # Filter bookings by customer ID
			)
			.group_by('month')
			.order_by('month')
		)

		result = await session.exec(statement)
		data = result.all()

		# Convert to dictionary format {1: count, 2: count, ..., 12: count}
		bookings_per_month = {int(row.month): row.total_bookings for row in data}

		# Ensure all 12 months are represented
		customer_booking_stats = [{"month": month, "bookings": bookings_per_month.get(month, 0)} for month in range(1, 13)]

		return {"data": customer_booking_stats}


	async def get_new_customers(self,first_day: int, session: AsyncSession):
		# Query unique customers who made bookings this month
		statement = select(Bookings.email).where(Bookings.created_at >= first_day).distinct()
		results = await session.exec(statement)
		results = results.all()
		
		return {"new_customers": len(results)}


	async def get_avg_daily_bookings(self, first_day:datetime , days_so_far:int, session:AsyncSession):
	# Count total bookings in the current month
		stmt = select(func.count()).where(Bookings.created_at >= first_day)
		result = await session.exec(stmt)
		total_bookings = result.first()  # Handle case where no bookings exist


		total_bookings = total_bookings if total_bookings else 0

		avg_daily_bookings = total_bookings / days_so_far if days_so_far > 0 else 0

		return {"avg_daily_bookings": round(avg_daily_bookings, 2)
		  		# "total":total_bookings,
				# "days":days_so_far
		  }

	# async def get_new_booking_count(self,now,past_7_days,prev_7_days,session: AsyncSession):
		
	# 	statement = select(func.count()).where(Bookings.created_at >= past_7_days)
	# 	result = await session.exec(statement)
	# 	current_bookings = result.first() or 0

	# 	statement = select(func.count()).where(
	# 		(Bookings.created_at >= prev_7_days) & (Bookings.created_at < past_7_days)
	# 	)
	# 	result = await session.exec(statement)
	# 	previous_bookings = result.first() or 0

	# 	if previous_bookings == 0:
	# 		growth = 100 if current_bookings > 0 else 0
	# 	else:
	# 		growth = ((current_bookings - previous_bookings) / previous_bookings) * 100
	# 	return {
	# 		"new_bookings": current_bookings,
	# 		"growth": round(growth, 2)
	# 	}
	


