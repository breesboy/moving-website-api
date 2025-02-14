from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine


from src.config import Config


engine = AsyncEngine(
	create_engine(
	url=Config.DATABASE_URL,
	echo=True
))

async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
		



async def get_session() -> AsyncSession:
	Session = sessionmaker(
		bind=engine, class_=AsyncSession, expire_on_commit=False
	)

	async with Session() as session:
		yield session
