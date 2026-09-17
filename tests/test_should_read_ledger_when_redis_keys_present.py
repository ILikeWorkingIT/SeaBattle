"""RedisLedgerStore read path (UC-007). No live Redis."""

from __future__ import annotations

import json

import pytest
from redis.exceptions import RedisError

from backend.application.errors import LedgerReadError
from backend.domain.ledger import InconsistentLedgerError
from backend.infrastructure.redis_ledger_store import (
    COUNTERS_KEY,
    RECORDS_KEY,
    RedisLedgerStore,
)


class FakeRedis:
    """Minimal async Redis surface for ledger GET (lrange / hgetall)."""

    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.hashes: dict[str, dict[str, str]] = {}
        self.fail = False

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        del start, end
        if self.fail:
            raise RedisError("unavailable")
        return list(self.lists.get(key, []))

    async def hgetall(self, key: str) -> dict[str, str]:
        if self.fail:
            raise RedisError("unavailable")
        return dict(self.hashes.get(key, {}))


def _record_json(
    *,
    record_id: str,
    winner: str,
    shots: int,
    end_reason: str = "FleetLost",
) -> str:
    return json.dumps(
        {
            "id": record_id,
            "sessionId": "a" * 32,
            "winner": winner,
            "shots": shots,
            "endReason": end_reason,
        }
    )


@pytest.mark.asyncio
async def test_should_read_hash_when_records_list_empty() -> None:
    """S-02 HASH read model when LIST is empty (OpenAPI populated)."""
    redis = FakeRedis()
    redis.hashes[COUNTERS_KEY] = {
        "games": "10",
        "playerWins": "6",
        "backendWins": "4",
        "shotsSum": "473",
    }
    snap = await RedisLedgerStore(redis).load_snapshot()
    assert snap.games == 10
    assert snap.player_wins == 6
    assert snap.backend_wins == 4
    assert snap.avg_shots == 47.3


@pytest.mark.asyncio
async def test_should_prefer_list_records_when_hash_differs() -> None:
    """FT-038…FT-041 / A0088: LIST records are the snapshot source when present."""
    redis = FakeRedis()
    redis.lists[RECORDS_KEY] = [
        _record_json(record_id="r1", winner="Player", shots=40),
        _record_json(record_id="r2", winner="Backend", shots=54),
    ]
    redis.hashes[COUNTERS_KEY] = {
        "games": "99",
        "playerWins": "99",
        "backendWins": "0",
        "shotsSum": "1",
    }
    snap = await RedisLedgerStore(redis).load_snapshot()
    assert snap.games == 2
    assert snap.player_wins == 1
    assert snap.backend_wins == 1
    assert snap.avg_shots == 47.0


@pytest.mark.asyncio
async def test_should_raise_inconsistent_when_record_json_corrupt() -> None:
    """UC-007 E1: corrupt LIST row is not a silent snapshot."""
    redis = FakeRedis()
    redis.lists[RECORDS_KEY] = ["{"]
    with pytest.raises(InconsistentLedgerError):
        await RedisLedgerStore(redis).load_snapshot()


@pytest.mark.asyncio
async def test_should_raise_ledger_read_when_redis_errors() -> None:
    """UC-007 E1: RedisError becomes LedgerReadError."""
    redis = FakeRedis()
    redis.fail = True
    with pytest.raises(LedgerReadError):
        await RedisLedgerStore(redis).load_snapshot()
