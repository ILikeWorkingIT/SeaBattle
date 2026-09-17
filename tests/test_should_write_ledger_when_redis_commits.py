"""RedisLedgerStore write path (UC-004). No live Redis."""

from __future__ import annotations

import json

import pytest
from redis.exceptions import RedisError

from backend.application.errors import LedgerWriteError
from backend.domain.ledger import record_from_outcome
from backend.domain.types import EndReason, Side
from backend.infrastructure.redis_ledger_store import (
    COUNTERS_KEY,
    RECORDED_KEY,
    RECORDS_KEY,
    RedisLedgerStore,
)


class FakeRedis:
    """Minimal async Redis for ledger Lua (eval) and key reads."""

    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.hashes: dict[str, dict[str, int]] = {}
        self.sets: dict[str, set[str]] = {}
        self.fail = False

    async def eval(self, script: str, numkeys: int, *keys_and_args: str) -> int:
        del script
        if self.fail:
            raise RedisError("unavailable")
        keys = keys_and_args[:numkeys]
        args = keys_and_args[numkeys:]
        records_key, counters_key, recorded_key = keys
        session_id, payload, winner_field, shots_raw = args
        recorded = self.sets.setdefault(recorded_key, set())
        if session_id in recorded:
            return 0
        recorded.add(session_id)
        self.lists.setdefault(records_key, []).insert(0, payload)
        counters = self.hashes.setdefault(
            counters_key,
            {"games": 0, "playerWins": 0, "backendWins": 0, "shotsSum": 0},
        )
        counters["games"] = int(counters.get("games", 0)) + 1
        counters[winner_field] = int(counters.get(winner_field, 0)) + 1
        counters["shotsSum"] = int(counters.get("shotsSum", 0)) + int(shots_raw)
        return 1

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        del start, end
        return list(self.lists.get(key, []))

    async def hgetall(self, key: str) -> dict[str, str]:
        raw = self.hashes.get(key, {})
        return {name: str(value) for name, value in raw.items()}


@pytest.mark.asyncio
async def test_should_write_record_once_when_redis_commits() -> None:
    """A0088 / A0129: LPUSH + HASH increment; second commit is a no-op."""
    redis = FakeRedis()
    store = RedisLedgerStore(redis)
    record = record_from_outcome(
        session_id="e" * 32,
        winner=Side.PLAYER,
        shots=12,
        end_reason=EndReason.FLEET_LOST,
    )
    first = await store.record_outcome(record)
    second = await store.record_outcome(record)
    assert first is True
    assert second is False
    assert len(redis.lists[RECORDS_KEY]) == 1
    row = json.loads(redis.lists[RECORDS_KEY][0])
    assert row["sessionId"] == "e" * 32
    assert row["winner"] == "Player"
    assert row["endReason"] == "FleetLost"
    assert row["shots"] == 12
    assert redis.hashes[COUNTERS_KEY]["games"] == 1
    assert redis.hashes[COUNTERS_KEY]["playerWins"] == 1
    assert redis.hashes[COUNTERS_KEY]["shotsSum"] == 12
    assert "e" * 32 in redis.sets[RECORDED_KEY]
    snap = await store.load_snapshot()
    assert snap.games == 1
    assert snap.player_wins == 1
    assert snap.avg_shots == 12.0


@pytest.mark.asyncio
async def test_should_raise_ledger_write_when_redis_errors() -> None:
    redis = FakeRedis()
    redis.fail = True
    record = record_from_outcome(
        session_id="f" * 32,
        winner=Side.BACKEND,
        shots=0,
        end_reason=EndReason.FLEET_LOST,
    )
    with pytest.raises(LedgerWriteError):
        await RedisLedgerStore(redis).record_outcome(record)


@pytest.mark.asyncio
async def test_should_increment_backend_wins_when_redis_commits() -> None:
    """FT-040 / A0129: Backend winner bumps backendWins HASH, not playerWins."""
    redis = FakeRedis()
    store = RedisLedgerStore(redis)
    record = record_from_outcome(
        session_id="a" * 32,
        winner=Side.BACKEND,
        shots=5,
        end_reason=EndReason.FLEET_LOST,
    )
    wrote = await store.record_outcome(record)
    assert wrote is True
    assert redis.hashes[COUNTERS_KEY]["games"] == 1
    assert redis.hashes[COUNTERS_KEY]["backendWins"] == 1
    assert redis.hashes[COUNTERS_KEY]["playerWins"] == 0
    assert redis.hashes[COUNTERS_KEY]["shotsSum"] == 5
