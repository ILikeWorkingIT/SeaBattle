from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from frontend.domain.types import EndReason, Side


@dataclass(slots=True)
class Record:
    id: str
    session_id: str
    winner: Side
    shots: int
    end_reason: EndReason


@dataclass(slots=True)
class Snapshot:
    games: int
    player_wins: int
    backend_wins: int
    avg_shots: float
    records: list[Record] = field(default_factory=list)


def seed_ledger() -> list[Record]:
    samples = (
        (Side.PLAYER, 41, EndReason.FLEET_LOST),
        (Side.BACKEND, 36, EndReason.FLEET_LOST),
        (Side.PLAYER, 52, EndReason.FLEET_LOST),
        (Side.BACKEND, 18, EndReason.SURRENDER),
        (Side.BACKEND, 44, EndReason.FLEET_LOST),
        (Side.PLAYER, 39, EndReason.FLEET_LOST),
        (Side.PLAYER, 47, EndReason.FLEET_LOST),
        (Side.BACKEND, 55, EndReason.FLEET_LOST),
        (Side.PLAYER, 33, EndReason.FLEET_LOST),
        (Side.BACKEND, 29, EndReason.SURRENDER),
        (Side.BACKEND, 48, EndReason.FLEET_LOST),
        (Side.PLAYER, 61, EndReason.FLEET_LOST),
        (Side.PLAYER, 28, EndReason.FLEET_LOST),
        (Side.BACKEND, 42, EndReason.FLEET_LOST),
        (Side.PLAYER, 50, EndReason.FLEET_LOST),
        (Side.BACKEND, 37, EndReason.FLEET_LOST),
        (Side.PLAYER, 45, EndReason.FLEET_LOST),
        (Side.BACKEND, 22, EndReason.SURRENDER),
        (Side.BACKEND, 58, EndReason.FLEET_LOST),
        (Side.PLAYER, 34, EndReason.FLEET_LOST),
        (Side.PLAYER, 40, EndReason.FLEET_LOST),
        (Side.BACKEND, 31, EndReason.FLEET_LOST),
        (Side.PLAYER, 56, EndReason.FLEET_LOST),
        (Side.BACKEND, 43, EndReason.FLEET_LOST),
    )
    records: list[Record] = []
    for winner, shots, reason in samples:
        records.append(
            Record(
                id=str(uuid4()),
                session_id=str(uuid4()),
                winner=winner,
                shots=shots,
                end_reason=reason,
            )
        )
    return records


def snapshot_from(records: list[Record]) -> Snapshot:
    games = len(records)
    player_wins = sum(1 for item in records if item.winner is Side.PLAYER)
    backend_wins = sum(1 for item in records if item.winner is Side.BACKEND)
    avg = (sum(item.shots for item in records) / games) if games else 0.0
    return Snapshot(games, player_wins, backend_wins, avg, list(records))
