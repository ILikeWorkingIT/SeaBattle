"""Redis-backed session store and active-session registry (FT-004, FT-005)."""

from __future__ import annotations

import json

from redis.asyncio import Redis

from backend.domain.session import Session
from backend.domain.types import IDLE_TTL_SECONDS, SLOT_LIMIT
from backend.infrastructure.session_codec import session_from_dict, session_to_dict

REGISTRY_KEY = "seabattle:registry:slots"
SESSION_KEY_PREFIX = "seabattle:session:"

# Claim a slot only if cardinality < limit, then store the session JSON with TTL.
_SAVE_NEW_LUA = """
local registry = KEYS[1]
local session_key = KEYS[2]
local session_id = ARGV[1]
local payload = ARGV[2]
local ttl = tonumber(ARGV[3])
local limit = tonumber(ARGV[4])
if redis.call('SCARD', registry) >= limit then
  return 0
end
if redis.call('SISMEMBER', registry, session_id) == 1 then
  return 0
end
redis.call('SADD', registry, session_id)
redis.call('SET', session_key, payload, 'EX', ttl)
return 1
"""


class RedisSessionStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _session_key(self, session_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}{session_id}"

    async def _prune_stale_slots(self) -> None:
        """Drop registry members whose session key expired (FT-053 / FT-004)."""
        members = await self._redis.smembers(REGISTRY_KEY)
        if not members:
            return
        stale: list[str] = []
        for session_id in members:
            exists = await self._redis.exists(self._session_key(session_id))
            if not exists:
                stale.append(session_id)
        if stale:
            await self._redis.srem(REGISTRY_KEY, *stale)

    async def active_count(self) -> int:
        await self._prune_stale_slots()
        return int(await self._redis.scard(REGISTRY_KEY))

    async def save_new(self, session: Session) -> bool:
        await self._prune_stale_slots()
        payload = json.dumps(session_to_dict(session), ensure_ascii=False)
        result = await self._redis.eval(
            _SAVE_NEW_LUA,
            2,
            REGISTRY_KEY,
            self._session_key(session.id),
            session.id,
            payload,
            str(session.idle_ttl_seconds or IDLE_TTL_SECONDS),
            str(SLOT_LIMIT),
        )
        return int(result) == 1

    async def get(self, session_id: str) -> Session | None:
        raw = await self._redis.get(self._session_key(session_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return session_from_dict(json.loads(raw))

    async def save(self, session: Session, *, refresh_idle: bool = False) -> None:
        payload = json.dumps(session_to_dict(session), ensure_ascii=False)
        if refresh_idle:
            ttl = session.idle_ttl_seconds or IDLE_TTL_SECONDS
        else:
            ttl = max(1, session.remain_ttl_seconds())
        await self._redis.set(self._session_key(session.id), payload, ex=ttl)

    async def release_slot(self, session_id: str) -> None:
        await self._redis.srem(REGISTRY_KEY, session_id)

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._session_key(session_id))
        await self._redis.srem(REGISTRY_KEY, session_id)
