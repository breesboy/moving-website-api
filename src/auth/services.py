from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .schemas import UserCreateModel
from .models import User
from .utils import generate_passwd_hash

class UserService:
	async def get_user_by_email(self, email : str, session : AsyncSession):
		statement = select(User).where(User.email == email)

		result = await session.exec(statement)

		user = result.first()

		return user
	
	async def get_user_by_username(self, username : str, session : AsyncSession):
		statement = select(User).where(User.username == username)

		result = await session.exec(statement)

		user = result.first()

		return user

	async def email_exists(self, email : str, session : AsyncSession):
		user = await self.get_user_by_email(email, session)

		return True if user is not None else False
	
	async def username_exists(self, username : str, session : AsyncSession):
		user = await self.get_user_by_username(username, session)

		return True if user is not None else False
	

	async def create_user_Account(self, user_data: UserCreateModel, session: AsyncSession):
		user_data_dict = user_data.model_dump()

		new_user = User(
			**user_data_dict
		)

		new_user.password_hash = generate_passwd_hash(user_data_dict['password'])
		new_user.role = 'user'

		session.add(new_user)

		await session.commit()

		return new_user


	async def get_all_users(self, session : AsyncSession):
			statement = select(User)

			result = await session.exec(statement)

			return result.all()
	

	async def update_user(self, user:User, user_data: dict, session: AsyncSession):
		
		for k, v in user_data.items():
			setattr(user, k, v)

		await session.commit()
		return user