"""Use-case tests for PlayBackendTurns (UC-003)."""

from __future__ import annotations

import random
from datetime import datetime, timezone

import pytest

from backend.application.errors import SessionNotFoundError, SessionPersistError
from backend.application.play_backend_turns import PlayBackendTurns
from backend.domain.session import (
    Board,
    Cell,
    Deck,
    Fleet,
    Occupancy,
    Ship,
    empty_board,
    new_session,
)
from backend.domain.types import (
    BOARD_SIZE,
    CellCoordinate,
    Facing,
    Mark,
    OccupancyKind,
    SessionStatus,
    ShipStatus,
    ShipType,
    ShotResult,
    Side,
)
from tests.conftest import FakeSessionStore


def _set_mark(board: Board, column: int, row: int, mark: Mark) -> None:
    index = row * BOARD_SIZE + column
    old = board.cells[index]
    board.cells[index] = Cell(
        coords=old.coords, occupancy=old.occupancy, mark=mark
    )


def _put(store: FakeSessionStore, session) -> str:
    store.by_id[session.id] = session
    return session.id


@pytest.mark.asyncio
async def test_should_apply_backend_shot_when_turn_is_backend() -> None:
    """FT-027: Hunt picks a cell and records a backend shot."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    boat = Ship(
        id="p01",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=0, row=0))],
    )
    player_board.cells[0] = Cell(
        coords=CellCoordinate(column=0, row=0),
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=boat.id),
    )
    session = new_session(
        "a" * 32,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store, random.Random(0)).execute(session_id)
    assert result.applications
    assert result.applications[0].shot.shooter is Side.BACKEND
    assert not result.aborted


@pytest.mark.asyncio
async def test_should_stop_chain_when_backend_misses() -> None:
    """After MISS the turn is Player; no extra backend shots."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if row == 0 and column == 0:
                continue
            _set_mark(player_board, column, row, Mark.MISS)
    boat = Ship(
        id="p-alive",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=9, row=9))],
    )
    session = new_session(
        "c" * 32,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store, random.Random(0)).execute(session_id)
    assert len(result.applications) == 1
    assert result.applications[0].shot.result is ShotResult.MISS
    assert result.applications[0].shot.coords == CellCoordinate(column=0, row=0)
    assert store.by_id[session_id].turn is Side.PLAYER
    assert not result.game_over


@pytest.mark.asyncio
async def test_should_continue_when_backend_hits() -> None:
    """HIT/SUNK without GAME_OVER repeats UC-003 until MISS or end."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    ship = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0)),
            Deck(coords=CellCoordinate(column=1, row=0)),
        ],
    )
    for deck in ship.decks:
        index = deck.coords.row * BOARD_SIZE + deck.coords.column
        player_board.cells[index] = Cell(
            coords=deck.coords,
            occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship.id),
        )
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if row == 0 and column in (0, 1, 2):
                continue
            _set_mark(player_board, column, row, Mark.MISS)
    session = new_session(
        "d" * 32,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[ship]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store, random.Random(0)).execute(session_id)
    kinds = [item.shot.result for item in result.applications]
    assert kinds[0] in (ShotResult.HIT, ShotResult.SUNK)
    assert len(result.applications) >= 2


@pytest.mark.asyncio
async def test_should_abort_when_heatmap_empty_and_fleet_alive() -> None:
    """FT-075 / FT-076: empty heatmap does not shoot; caller deletes the slot."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if (column + row) % 2 == 0:
                continue
            _set_mark(player_board, column, row, Mark.MISS)
    destroyer = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0)),
            Deck(coords=CellCoordinate(column=0, row=1)),
        ],
    )
    session = new_session(
        "e" * 32,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[destroyer]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store).execute(session_id)
    assert result.aborted
    assert result.applications == ()
    assert store.by_id[session_id].shots == []
    assert store.by_id[session_id].status is SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_should_raise_when_session_missing_on_backend_turn() -> None:
    """UC-003: unknown session id does not create a turn."""
    store = FakeSessionStore()
    with pytest.raises(SessionNotFoundError):
        await PlayBackendTurns(store).execute("a" * 32)


@pytest.mark.asyncio
async def test_should_set_game_over_without_shot_when_heatmap_empty_and_fleet_sunk() -> None:
    """FT-052 / FT-065: empty heatmap with destroyed player fleet → GAME_OVER, no shot."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    boat = _sunk_only_boat()
    session = new_session(
        "f" * 32,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store).execute(session_id)
    assert result.game_over
    assert not result.aborted
    assert result.applications == ()
    stored = store.by_id[session_id]
    assert stored.status is SessionStatus.GAME_OVER
    assert stored.winner is Side.BACKEND
    assert stored.shots == []


@pytest.mark.asyncio
async def test_should_recompute_aim_when_backend_continues_after_hit() -> None:
    """FT-028: each chained shot recalculates aim; the second cell differs."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    ship = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0)),
            Deck(coords=CellCoordinate(column=1, row=0)),
        ],
    )
    for deck in ship.decks:
        index = deck.coords.row * BOARD_SIZE + deck.coords.column
        player_board.cells[index] = Cell(
            coords=deck.coords,
            occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship.id),
        )
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if row == 0 and column in (0, 1, 2):
                continue
            _set_mark(player_board, column, row, Mark.MISS)
    session = new_session(
        "d0" + "e" * 30,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[ship]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store, random.Random(0)).execute(session_id)
    assert len(result.applications) >= 2
    first, second = result.applications[0], result.applications[1]
    assert first.shot.result in (ShotResult.HIT, ShotResult.SUNK)
    assert first.shot.coords != second.shot.coords


@pytest.mark.asyncio
async def test_should_leave_peer_session_when_backend_plays() -> None:
    """FT-003 / UC-003 5.5: a Backend turn in session A does not mutate session B."""
    store = FakeSessionStore()
    player_board_a = empty_board(Side.PLAYER)
    player_board_b = empty_board(Side.PLAYER)
    boat_a = Ship(
        id="p-a",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=9, row=9))],
    )
    boat_b = Ship(
        id="p-b",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=9, row=9))],
    )
    session_a = new_session(
        "a" * 32,
        player_board_a,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat_a]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session_a.turn = Side.BACKEND
    session_b = new_session(
        "b" * 32,
        player_board_b,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat_b]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session_b.turn = Side.BACKEND
    _put(store, session_a)
    _put(store, session_b)
    await PlayBackendTurns(store, random.Random(0)).execute(session_a.id)
    assert store.by_id[session_a.id].shots
    peer = store.by_id[session_b.id]
    assert peer.shots == []
    assert peer.turn is Side.BACKEND
    assert peer.player_board.cell_at(0, 0).mark is Mark.UNCHECKED


def _place_deck(board: Board, coords: CellCoordinate, ship_id: str) -> None:
    index = coords.row * BOARD_SIZE + coords.column
    old = board.cells[index]
    board.cells[index] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship_id),
        mark=old.mark,
    )


@pytest.mark.asyncio
async def test_should_shoot_unchecked_between_hits_when_battleship_has_gaps() -> None:
    """FT-058 / FT-033 / UC-003 5.1: Target axis with skipped decks still fires; no abort/silence."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    decks = (
        CellCoordinate(column=2, row=4),
        CellCoordinate(column=3, row=4),
        CellCoordinate(column=4, row=4),
        CellCoordinate(column=5, row=4),
    )
    battleship = Ship(
        id="p-bb",
        type=ShipType.BATTLESHIP,
        length=4,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=decks[0], destroyed=True),
            Deck(coords=decks[1], destroyed=False),
            Deck(coords=decks[2], destroyed=False),
            Deck(coords=decks[3], destroyed=True),
        ],
    )
    for coords in decks:
        _place_deck(player_board, coords, battleship.id)
    _set_mark(player_board, 2, 4, Mark.HIT)
    _set_mark(player_board, 5, 4, Mark.HIT)
    _set_mark(player_board, 1, 4, Mark.MISS)
    _set_mark(player_board, 6, 4, Mark.MISS)
    session = new_session(
        "g0" + "a" * 30,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[battleship]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    result = await PlayBackendTurns(store, random.Random(0)).execute(session_id)
    gaps = {
        CellCoordinate(column=3, row=4),
        CellCoordinate(column=4, row=4),
    }
    assert not result.aborted
    assert result.applications
    first = result.applications[0]
    assert first.shot.shooter is Side.BACKEND
    assert first.shot.coords in gaps
    assert first.shot.result is ShotResult.HIT


@pytest.mark.asyncio
async def test_should_raise_persist_error_when_save_fails_after_backend_shot() -> None:
    """UC-003 E2 analogue: persist failure after a legal Backend shot."""
    store = FakeSessionStore()
    player_board = empty_board(Side.PLAYER)
    boat = Ship(
        id="p-live",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=0, row=0))],
    )
    session = new_session(
        "c0" + "d" * 30,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    session_id = _put(store, session)
    store.fail_persist = True
    with pytest.raises(SessionPersistError):
        await PlayBackendTurns(store, random.Random(0)).execute(session_id)


def _sunk_only_boat() -> Ship:
    coords = CellCoordinate(column=0, row=0)
    return Ship(
        id="p-sunk",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.SUNK,
        decks=[Deck(coords=coords, destroyed=True)],
    )
