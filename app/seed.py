from sqlalchemy.ext.asyncio import AsyncSession
from app.services.data_generator import generate_all_data


async def seed_database(session: AsyncSession):
    await generate_all_data(session)
