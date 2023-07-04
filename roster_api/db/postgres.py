import logging
from typing import Optional

import asyncpg
from roster_api import constants, settings

POSTGRES_POOL: Optional[asyncpg.pool.Pool] = None

logger = logging.getLogger(constants.LOGGER_NAME)


async def get_postgres_pool() -> asyncpg.pool.Pool:
    global POSTGRES_POOL
    if POSTGRES_POOL is not None:
        return POSTGRES_POOL

    POSTGRES_POOL = await asyncpg.create_pool(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
    )
    return POSTGRES_POOL
