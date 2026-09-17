"""Async Redis connection helpers."""

from redis.asyncio import Redis


async def create_redis(redis_url: str) -> Redis:
    """Open a Redis client and verify connectivity with PING."""
    client: Redis = Redis.from_url(redis_url, decode_responses=True)
    await client.ping()
    return client


async def close_redis(client: Redis | None) -> None:
    if client is not None:
        await client.aclose()
