"""Redis ledger: HASH counters + LIST of records (FT-038…FT-041, A0088).

GET /statistics is read-only. UC-004 appends LIST and increments HASH once per sessionId.
"""

from __future__ import annotations

import json

from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.application.errors import LedgerReadError, LedgerWriteError
from backend.domain.ledger import (
    InconsistentLedgerError,
    Ledger,
    Record,
    Snapshot,
    snapshot_from_counters,
    snapshot_from_records,
)
from backend.domain.types import EndReason, Side

COUNTERS_KEY = "seabattle:ledger:counters"
RECORDS_KEY = "seabattle:ledger:records"
RECORDED_KEY = "seabattle:ledger:sessions"

# Append one record and bump HASH only if sessionId is new (A0129).
_RECORD_OUTCOME_LUA = """
local records = KEYS[1]
local counters = KEYS[2]
local recorded = KEYS[3]
local session_id = ARGV[1]
local payload = ARGV[2]
local winner_field = ARGV[3]
local shots = tonumber(ARGV[4])
if redis.call('SISMEMBER', recorded, session_id) == 1 then
  return 0
end
redis.call('SADD', recorded, session_id)
redis.call('LPUSH', records, payload)
redis.call('HINCRBY', counters, 'games', 1)
redis.call('HINCRBY', counters, winner_field, 1)
redis.call('HINCRBY', counters, 'shotsSum', shots)
return 1
"""


def record_from_dict(payload: dict[str, object]) -> Record:
    winner_raw = str(payload["winner"])
    reason_raw = str(payload["endReason"])
    return Record(
        id=str(payload["id"]),
        session_id=str(payload["sessionId"]),
        winner=Side(winner_raw),
        shots=int(payload["shots"]),
        end_reason=EndReason(reason_raw),
    )


def record_to_dict(record: Record) -> dict[str, object]:
    return {
        "id": record.id,
        "sessionId": record.session_id,
        "winner": record.winner.value,
        "shots": record.shots,
        "endReason": record.end_reason.value,
    }


class RedisLedgerStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def ensure(self) -> None:
        """Create zero counters if missing so S-05 can HINCRBY without a stub."""
        await self._redis.hsetnx(COUNTERS_KEY, "games", 0)
        await self._redis.hsetnx(COUNTERS_KEY, "playerWins", 0)
        await self._redis.hsetnx(COUNTERS_KEY, "backendWins", 0)
        await self._redis.hsetnx(COUNTERS_KEY, "shotsSum", 0)

    async def load(self) -> Ledger:
        try:
            raw_rows = await self._redis.lrange(RECORDS_KEY, 0, -1)
        except RedisError as exc:
            raise LedgerReadError() from exc
        records: list[Record] = []
        for raw in raw_rows:
            text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            try:
                records.append(record_from_dict(json.loads(text)))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise InconsistentLedgerError("corrupt ledger record") from exc
        return Ledger(records=tuple(records))

    async def load_snapshot(self) -> Snapshot:
        ledger = await self.load()
        if ledger.records:
            return snapshot_from_records(ledger.records)
        try:
            raw = await self._redis.hgetall(COUNTERS_KEY)
        except RedisError as exc:
            raise LedgerReadError() from exc
        if not raw:
            return snapshot_from_counters(
                games=0, player_wins=0, backend_wins=0, shots_sum=0
            )
        fields = {
            (k.decode("utf-8") if isinstance(k, bytes) else k): (
                v.decode("utf-8") if isinstance(v, bytes) else v
            )
            for k, v in raw.items()
        }
        try:
            return snapshot_from_counters(
                games=int(fields.get("games", 0)),
                player_wins=int(fields.get("playerWins", 0)),
                backend_wins=int(fields.get("backendWins", 0)),
                shots_sum=int(fields.get("shotsSum", 0)),
            )
        except (TypeError, ValueError) as exc:
            raise InconsistentLedgerError("corrupt ledger counters") from exc

    async def record_outcome(self, record: Record) -> bool:
        winner_field = (
            "playerWins" if record.winner is Side.PLAYER else "backendWins"
        )
        payload = json.dumps(record_to_dict(record), ensure_ascii=False)
        try:
            result = await self._redis.eval(
                _RECORD_OUTCOME_LUA,
                3,
                RECORDS_KEY,
                COUNTERS_KEY,
                RECORDED_KEY,
                record.session_id,
                payload,
                winner_field,
                str(record.shots),
            )
        except RedisError as exc:
            raise LedgerWriteError() from exc
        return int(result) == 1
