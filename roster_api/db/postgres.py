from typing import Optional

import asyncpg
from roster_api import settings

POSTGRES_POOL: Optional[asyncpg.Pool] = None


async def setup_postgres():
    global POSTGRES_POOL
    if POSTGRES_POOL is None:
        POSTGRES_POOL = await asyncpg.create_pool(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
        )


async def teardown_postgres():
    global POSTGRES_POOL
    if POSTGRES_POOL is not None:
        await POSTGRES_POOL.close()
        POSTGRES_POOL = None


async def get_postgres_connection():
    if POSTGRES_POOL is None:
        await setup_postgres()
    async with POSTGRES_POOL.acquire() as conn:
        yield conn
