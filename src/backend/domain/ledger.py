"""Ledger aggregate: completed-game records and derived statistics snapshot."""

from __future__ import annotations

from dataclasses import dataclass

from backend.domain.types import EndReason, Side


class InconsistentLedgerError(ValueError):
    """Snapshot would violate UC-007 E1 (e.g. wins exceed games)."""


@dataclass(frozen=True, slots=True)
class Record:
    """One GAME_OVER row (FT-056). Written by UC-004, not by GET /statistics."""

    id: str
    session_id: str
    winner: Side
    shots: int
    end_reason: EndReason

    def __post_init__(self) -> None:
        if not self.id or not self.session_id:
            raise InconsistentLedgerError("record identity is required")
        if self.shots < 0:
            raise InconsistentLedgerError("shots must be >= 0")
        if self.winner not in (Side.PLAYER, Side.BACKEND):
            raise InconsistentLedgerError("winner must be Player or Backend")
        if self.end_reason not in (EndReason.FLEET_LOST, EndReason.SURRENDER):
            raise InconsistentLedgerError("endReason must be FleetLost or Surrender")


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Derived counters for GET /statistics (A0159)."""

    games: int
    player_wins: int
    backend_wins: int
    avg_shots: float

    def __post_init__(self) -> None:
        if self.games < 0 or self.player_wins < 0 or self.backend_wins < 0:
            raise InconsistentLedgerError("counters must be >= 0")
        if self.avg_shots < 0:
            raise InconsistentLedgerError("avgShots must be >= 0")
        if self.player_wins + self.backend_wins != self.games:
            raise InconsistentLedgerError("playerWins + backendWins must equal games")
        if self.games == 0 and self.avg_shots != 0:
            raise InconsistentLedgerError("avgShots must be 0 when games is 0")


@dataclass(frozen=True, slots=True)
class Ledger:
    """Single-server journal (A0015). Empty records → all zeros (UC-007 5.6)."""

    id: str = "backend"
    records: tuple[Record, ...] = ()

    def snapshot(self) -> Snapshot:
        return snapshot_from_records(self.records)


def snapshot_from_records(records: tuple[Record, ...]) -> Snapshot:
    games = len(records)
    if games == 0:
        return Snapshot(games=0, player_wins=0, backend_wins=0, avg_shots=0.0)
    player_wins = sum(1 for row in records if row.winner is Side.PLAYER)
    backend_wins = sum(1 for row in records if row.winner is Side.BACKEND)
    shots_sum = sum(row.shots for row in records)
    return Snapshot(
        games=games,
        player_wins=player_wins,
        backend_wins=backend_wins,
        avg_shots=shots_sum / games,
    )


def record_from_outcome(
    *,
    session_id: str,
    winner: Side,
    shots: int,
    end_reason: EndReason,
) -> Record:
    """One Ledger row for one GAME_OVER (sessionId unique, A0129)."""
    return Record(
        id=session_id,
        session_id=session_id,
        winner=winner,
        shots=shots,
        end_reason=end_reason,
    )


def snapshot_from_counters(
    *,
    games: int,
    player_wins: int,
    backend_wins: int,
    shots_sum: int,
) -> Snapshot:
    """Projection used when Redis HASH is the read model (empty or after UC-004)."""
    if games == 0:
        if player_wins != 0 or backend_wins != 0 or shots_sum != 0:
            raise InconsistentLedgerError("zero games requires zero totals")
        return Snapshot(games=0, player_wins=0, backend_wins=0, avg_shots=0.0)
    if shots_sum < 0:
        raise InconsistentLedgerError("shotsSum must be >= 0")
    return Snapshot(
        games=games,
        player_wins=player_wins,
        backend_wins=backend_wins,
        avg_shots=shots_sum / games,
    )
