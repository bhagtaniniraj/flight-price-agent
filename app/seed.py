import logging
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Airport, Airline, Flight, Booking, PriceAlert
from app.services.data_generator import generate_all_data

logger = logging.getLogger(__name__)


async def seed_database(session: AsyncSession):
    # Check if flight data is stale (all flights in the past)
    result = await session.execute(select(func.max(Flight.departure_time)))
    max_dep = result.scalar()

    if max_dep is not None and max_dep < datetime.now():
        # All flights are in the past — purge and re-seed
        logger.info("Flight data is stale (max departure: %s). Purging and re-seeding...", max_dep)
        await session.execute(delete(Booking))
        await session.execute(delete(PriceAlert))
        await session.execute(delete(Flight))
        await session.execute(delete(Airline))
        await session.execute(delete(Airport))
        await session.commit()
    elif max_dep is None:
        logger.info("No flight data found. Seeding database...")
    else:
        logger.info("Flight data is current (max departure: %s). Checking for gaps...", max_dep)

    await generate_all_data(session)
