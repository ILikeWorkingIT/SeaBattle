"""UC-005: ApplySurrender commits GAME_OVER with Backend win (include UC-004)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.apply_shot import ApplyPlayerShot
from backend.application.apply_surrender import ApplySurrender
from backend.application.errors import SessionNotFoundError
from backend.domain.session import Fleet, Shot, empty_board, new_session
from backend.domain.shot import ShotRejectedError
from backend.domain.surrender import SurrenderRejectedError, apply_surrender
from backend.domain.types import (
    CellCoordinate,
    EndReason,
    SessionStatus,
    ShotResult,
    Side,
)
from tests.conftest import FakeLedgerStore, FakeSessionStore


def _active_session(
    store: FakeSessionStore,
    *,
    session_id: str = "aa" + "s" * 30,
    turn: Side = Side.PLAYER,
    shots: int = 0,
) -> str:
    session = new_session(
        session_id,
        empty_board(Side.PLAYER),
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = turn
    session.shots = [
        Shot(
            seq=index,
            shooter=Side.PLAYER,
            coords=CellCoordinate(column=0, row=0),
            result=ShotResult.MISS,
        )
        for index in range(1, shots + 1)
    ]
    store.by_id[session.id] = session
    return session.id


def test_should_mark_backend_win_when_surrender_applied() -> None:
    """FT-077 / FT-026: Surrender → GAME_OVER, winner Backend, endReason Surrender."""
    store = FakeSessionStore()
    session_id = _active_session(store)
    session = store.by_id[session_id]
    apply_surrender(session)
    assert session.status is SessionStatus.GAME_OVER
    assert session.winner is Side.BACKEND
    assert session.end_reason == EndReason.SURRENDER.value


def test_should_allow_surrender_when_backend_turn() -> None:
    """A0092 / A0100: surrender is legal while Backend holds the turn."""
    store = FakeSessionStore()
    session_id = _active_session(store, turn=Side.BACKEND)
    apply_surrender(store.by_id[session_id])
    assert store.by_id[session_id].status is SessionStatus.GAME_OVER
    assert store.by_id[session_id].winner is Side.BACKEND


def test_should_reject_surrender_when_match_already_over() -> None:
    """FT-077: second surrender is not a new outcome."""
    store = FakeSessionStore()
    session_id = _active_session(store)
    session = store.by_id[session_id]
    apply_surrender(session)
    with pytest.raises(SurrenderRejectedError) as caught:
        apply_surrender(session)
    assert caught.value.code == "SHOT_GAME_OVER"
    assert session.end_reason == EndReason.SURRENDER.value


@pytest.mark.asyncio
async def test_should_commit_ledger_when_surrender_has_zero_shots() -> None:
    """UC-005 5.6: zero-shot surrender still writes one Record (shots=0)."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _active_session(store, shots=0)
    result = await ApplySurrender(store, ledger).execute(session_id)
    assert result.session.status is SessionStatus.GAME_OVER
    assert len(ledger.records) == 1
    assert ledger.records[0].winner is Side.BACKEND
    assert ledger.records[0].end_reason is EndReason.SURRENDER
    assert ledger.records[0].shots == 0
    assert ledger.counters["games"] == 1
    assert ledger.counters["backendWins"] == 1
    assert session_id in store.released
    assert session_id in store.by_id


@pytest.mark.asyncio
async def test_should_not_double_count_when_surrender_repeated() -> None:
    """FT-077: GAME_OVER already present → no second Ledger row."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _active_session(store)
    await ApplySurrender(store, ledger).execute(session_id)
    with pytest.raises(SurrenderRejectedError):
        await ApplySurrender(store, ledger).execute(session_id)
    assert len(ledger.records) == 1
    assert ledger.counters["games"] == 1


@pytest.mark.asyncio
async def test_should_raise_when_session_missing_on_surrender() -> None:
    """UC-005 5.4: unknown session is refused without a Ledger row."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    with pytest.raises(SessionNotFoundError):
        await ApplySurrender(store, ledger).execute("ff" + "0" * 30)
    assert ledger.records == []


@pytest.mark.asyncio
async def test_should_reject_shot_when_surrender_already_committed() -> None:
    """FT-077: if surrender is the first accepted mutation, the shot is refused."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _active_session(store)
    await ApplySurrender(store, ledger).execute(session_id)
    with pytest.raises(ShotRejectedError) as caught:
        await ApplyPlayerShot(store, ledger).execute(session_id, 0, 0)
    assert caught.value.code == "SHOT_GAME_OVER"
    assert len(ledger.records) == 1
    assert ledger.records[0].end_reason is EndReason.SURRENDER
    assert ledger.counters["games"] == 1


@pytest.mark.asyncio
async def test_should_apply_surrender_when_shot_already_accepted() -> None:
    """FT-077: if the shot is accepted first, surrender still yields one GAME_OVER."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _active_session(store)
    await ApplyPlayerShot(store, ledger).execute(session_id, 0, 0)
    result = await ApplySurrender(store, ledger).execute(session_id)
    assert result.session.status is SessionStatus.GAME_OVER
    assert result.session.winner is Side.BACKEND
    assert result.session.turn is Side.BACKEND
    assert len(ledger.records) == 1
    assert ledger.records[0].end_reason is EndReason.SURRENDER
    assert ledger.records[0].shots == 1
    assert ledger.counters["games"] == 1
