"""UC-004: CommitGameOver writes Ledger once and frees the FT-004 slot."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.apply_shot import ApplyPlayerShot
from backend.application.commit_game_over import CommitGameOver
from backend.application.errors import SessionPersistError
from backend.application.play_backend_turns import PlayBackendTurns
from backend.domain.session import Cell, Deck, Fleet, Occupancy, Ship, Shot, empty_board, new_session
from backend.domain.types import (
    BOARD_SIZE,
    CellCoordinate,
    EndReason,
    Facing,
    Mark,
    OccupancyKind,
    SessionStatus,
    ShipStatus,
    ShipType,
    ShotResult,
    Side,
)
from tests.conftest import FakeLedgerStore, FakeSessionStore


def _session_player_win(store: FakeSessionStore, *, shots: int) -> str:
    session_id = "aa" + "b" * 30
    session = new_session(
        session_id,
        empty_board(Side.PLAYER),
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.status = SessionStatus.GAME_OVER
    session.winner = Side.PLAYER
    session.end_reason = EndReason.FLEET_LOST.value
    session.shots = [
        Shot(
            seq=index,
            shooter=Side.PLAYER,
            coords=CellCoordinate(column=0, row=0),
            result=ShotResult.SUNK,
        )
        for index in range(1, shots + 1)
    ]
    store.by_id[session.id] = session
    return session.id


@pytest.mark.asyncio
async def test_should_append_ledger_and_release_slot_when_game_over() -> None:
    """A0128 / A0129: one Record, slot free while JSON still present."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _session_player_win(store, shots=3)
    session = store.by_id[session_id]
    await CommitGameOver(store, ledger).execute(session)
    assert len(ledger.records) == 1
    assert ledger.records[0].session_id == session_id
    assert ledger.records[0].shots == 3
    assert ledger.records[0].winner is Side.PLAYER
    assert ledger.records[0].end_reason is EndReason.FLEET_LOST
    assert ledger.counters["games"] == 1
    assert ledger.counters["playerWins"] == 1
    assert session_id in store.released
    assert session_id in store.by_id
    assert await store.active_count() == 0


@pytest.mark.asyncio
async def test_should_not_double_count_when_commit_retried() -> None:
    """A0129: retry must not create a second GAME_OVER row."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _session_player_win(store, shots=1)
    session = store.by_id[session_id]
    await CommitGameOver(store, ledger).execute(session)
    await CommitGameOver(store, ledger).execute(session)
    assert len(ledger.records) == 1
    assert ledger.counters["games"] == 1
    assert ledger.counters["shotsSum"] == 1


@pytest.mark.asyncio
async def test_should_retry_write_without_second_row_when_ledger_fails_once() -> None:
    """UC-004 E1: failed HASH/LIST write is retried; one Record after success."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    ledger.fail_write_remaining = 1
    session_id = _session_player_win(store, shots=4)
    session = store.by_id[session_id]
    await CommitGameOver(store, ledger).execute(session)
    assert len(ledger.records) == 1
    assert ledger.counters["games"] == 1


@pytest.mark.asyncio
async def test_should_raise_persist_when_ledger_write_exhausted() -> None:
    """UC-004 E1: three LedgerWriteError attempts become SessionPersistError; no Record."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    ledger.fail_write_remaining = 3
    session_id = _session_player_win(store, shots=1)
    session = store.by_id[session_id]
    with pytest.raises(SessionPersistError):
        await CommitGameOver(store, ledger).execute(session)
    assert ledger.records == []


@pytest.mark.asyncio
async def test_should_record_ledger_when_heatmap_empty_and_fleet_sunk() -> None:
    """FT-052: empty heatmap + destroyed player fleet writes FleetLost, no abort."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    boat = Ship(
        id="p-sunk",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.SUNK,
        decks=[Deck(coords=CellCoordinate(column=0, row=0), destroyed=True)],
    )
    session = new_session(
        "cc" + "d" * 30,
        empty_board(Side.PLAYER),
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    store.by_id[session.id] = session
    result = await PlayBackendTurns(store, ledger=ledger).execute(session.id)
    assert result.game_over
    assert not result.aborted
    assert result.applications == ()
    assert len(ledger.records) == 1
    assert ledger.records[0].winner is Side.BACKEND
    assert ledger.records[0].end_reason is EndReason.FLEET_LOST
    assert session.id in store.released


@pytest.mark.asyncio
async def test_should_count_backend_win_when_commit_game_over() -> None:
    """FT-040 / UC-004 5.6: Backend winner increments backendWins; games +1."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = "bb" + "c" * 30
    session = new_session(
        session_id,
        empty_board(Side.PLAYER),
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.status = SessionStatus.GAME_OVER
    session.winner = Side.BACKEND
    session.end_reason = EndReason.FLEET_LOST.value
    store.by_id[session.id] = session
    await CommitGameOver(store, ledger).execute(session)
    assert ledger.counters["games"] == 1
    assert ledger.counters["backendWins"] == 1
    assert ledger.counters["playerWins"] == 0
    assert ledger.records[0].winner is Side.BACKEND


@pytest.mark.asyncio
async def test_should_set_avg_shots_when_first_game_commits() -> None:
    """UC-004 5.6 / FT-041: first Record sets average equal to that party's shots."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session_id = _session_player_win(store, shots=7)
    session = store.by_id[session_id]
    await CommitGameOver(store, ledger).execute(session)
    snap = await ledger.load_snapshot()
    assert snap.games == 1
    assert snap.avg_shots == 7.0
    assert snap.player_wins == 1


@pytest.mark.asyncio
async def test_should_reject_commit_when_status_is_active() -> None:
    """A0027 / FT-056: no Ledger row without GAME_OVER."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    session = new_session(
        "99" + "a" * 30,
        empty_board(Side.PLAYER),
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    store.by_id[session.id] = session
    with pytest.raises(SessionPersistError):
        await CommitGameOver(store, ledger).execute(session)
    assert ledger.records == []
    assert ledger.counters["games"] == 0
    assert session.id not in store.released


@pytest.mark.asyncio
async def test_should_commit_ledger_when_player_sinks_last_ship() -> None:
    """A0128 / FT-071: ApplyPlayerShot writes one Record and frees the slot; JSON remains."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    coords = CellCoordinate(column=0, row=0)
    board = empty_board(Side.BACKEND)
    ship = Ship(
        id="b01",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords, destroyed=False)],
    )
    board.cells[coords.row * BOARD_SIZE + coords.column] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship.id),
    )
    sunk = [
        Ship(
            id=f"b{i:02d}",
            type=ShipType.BOAT,
            length=1,
            facing=Facing.HORIZONTAL,
            status=ShipStatus.SUNK,
            decks=[
                Deck(
                    coords=CellCoordinate(column=i % 10, row=9),
                    destroyed=True,
                )
            ],
        )
        for i in range(2, 11)
    ]
    session = new_session(
        "ee" + "f" * 30,
        empty_board(Side.PLAYER),
        board,
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[ship, *sunk]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    store.by_id[session.id] = session
    result = await ApplyPlayerShot(store, ledger).execute(session.id, 0, 0)
    assert result.application.game_over
    assert result.application.shot.result is ShotResult.SUNK
    assert len(ledger.records) == 1
    assert ledger.records[0].winner is Side.PLAYER
    assert session.id in store.released
    assert session.id in store.by_id
    assert await store.active_count() == 0


@pytest.mark.asyncio
async def test_should_commit_ledger_when_backend_sinks_last_ship() -> None:
    """FT-025 / FT-040: PlayBackendTurns last player deck writes Backend win (not FT-052)."""
    store = FakeSessionStore()
    ledger = FakeLedgerStore()
    coords = CellCoordinate(column=0, row=0)
    player_board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if row == 0 and column == 0:
                continue
            index = row * BOARD_SIZE + column
            old = player_board.cells[index]
            player_board.cells[index] = Cell(
                coords=old.coords,
                occupancy=old.occupancy,
                mark=Mark.MISS,
            )
    boat = Ship(
        id="p-last",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords)],
    )
    player_board.cells[0] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=boat.id),
    )
    session = new_session(
        "12" + "ab" * 15,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    store.by_id[session.id] = session
    result = await PlayBackendTurns(store, ledger=ledger).execute(session.id)
    assert result.game_over
    assert not result.aborted
    assert len(result.applications) == 1
    assert result.applications[0].shot.result is ShotResult.SUNK
    assert len(ledger.records) == 1
    assert ledger.records[0].winner is Side.BACKEND
    assert ledger.counters["backendWins"] == 1
    assert session.id in store.released
