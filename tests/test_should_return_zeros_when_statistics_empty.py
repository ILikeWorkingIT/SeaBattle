"""Domain snapshot derivation for UC-007 (FT-038…FT-041, A0088)."""

from __future__ import annotations

import pytest

from backend.domain.ledger import (
    InconsistentLedgerError,
    Record,
    snapshot_from_counters,
    snapshot_from_records,
)
from backend.domain.types import EndReason, Side


def test_should_return_zero_snapshot_when_no_records() -> None:
    snap = snapshot_from_records(())
    assert snap.games == 0
    assert snap.player_wins == 0
    assert snap.backend_wins == 0
    assert snap.avg_shots == 0


def test_should_average_shots_when_records_exist() -> None:
    records = (
        Record("r1", "s1", Side.PLAYER, 40, EndReason.FLEET_LOST),
        Record("r2", "s2", Side.BACKEND, 60, EndReason.SURRENDER),
        Record("r3", "s3", Side.PLAYER, 42, EndReason.FLEET_LOST),
    )
    snap = snapshot_from_records(records)
    assert snap.games == 3
    assert snap.player_wins == 2
    assert snap.backend_wins == 1
    assert snap.avg_shots == pytest.approx(142 / 3)


def test_should_reject_when_counter_wins_exceed_games() -> None:
    with pytest.raises(InconsistentLedgerError):
        snapshot_from_counters(
            games=1, player_wins=1, backend_wins=1, shots_sum=10
        )


def test_should_reject_when_zero_games_have_nonzero_totals() -> None:
    """UC-007 E1: empty ledger cannot carry leftover HASH totals."""
    with pytest.raises(InconsistentLedgerError):
        snapshot_from_counters(
            games=0, player_wins=0, backend_wins=0, shots_sum=10
        )


def test_should_average_zero_when_surrender_has_no_shots() -> None:
    """FT-041 / A0105: Record.shots may be 0 (surrender); mean is 0."""
    records = (
        Record("r1", "s1", Side.BACKEND, 0, EndReason.SURRENDER),
    )
    snap = snapshot_from_records(records)
    assert snap.games == 1
    assert snap.player_wins == 0
    assert snap.backend_wins == 1
    assert snap.avg_shots == 0.0
