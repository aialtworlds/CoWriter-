import asyncpg
import os

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.environ['DATABASE_URL'], min_size=1, max_size=10, statement_cache_size=0
        )
    return _pool


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError('DB pool not initialized')
    return _pool
