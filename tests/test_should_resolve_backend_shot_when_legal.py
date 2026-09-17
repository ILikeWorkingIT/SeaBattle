"""Domain tests for backend shots on the player board (UC-003)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.domain.session import (
    Cell,
    Deck,
    Fleet,
    Occupancy,
    Ship,
    empty_board,
    new_session,
)
from backend.domain.shot import ShotRejectedError, apply_backend_shot
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


def _backend_turn_session(
    player_board,
    player_fleet,
):
    session = new_session(
        "b" * 32,
        player_board,
        empty_board(Side.BACKEND),
        player_fleet,
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    return session


def test_should_mark_miss_and_pass_turn_when_backend_misses() -> None:
    """FT-027 / FT-018 analogue: MISS on the player board returns the turn."""
    board = empty_board(Side.PLAYER)
    fleet = Fleet(owner=Side.PLAYER, ships=[])
    session = _backend_turn_session(board, fleet)
    outcome = apply_backend_shot(session, 0, 0)
    assert outcome.shot.shooter is Side.BACKEND
    assert outcome.shot.result is ShotResult.MISS
    assert session.turn is Side.PLAYER
    assert session.player_board.cell_at(0, 0).mark is Mark.MISS


def test_should_keep_turn_when_backend_hits() -> None:
    """UC-003 step 5: HIT keeps the backend turn."""
    board = empty_board(Side.PLAYER)
    coords = CellCoordinate(column=2, row=2)
    ship = Ship(
        id="p01",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=coords),
            Deck(coords=CellCoordinate(column=3, row=2)),
        ],
    )
    index = coords.row * BOARD_SIZE + coords.column
    board.cells[index] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship.id),
    )
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[ship]))
    outcome = apply_backend_shot(session, 2, 2)
    assert outcome.shot.result is ShotResult.HIT
    assert session.turn is Side.BACKEND
    assert ship.status is ShipStatus.WOUNDED
    assert not outcome.game_over


def test_should_keep_turn_and_mark_perimeter_when_backend_sinks() -> None:
    """FT-021 on the player board; turn stays with Backend unless GAME_OVER."""
    board = empty_board(Side.PLAYER)
    coords = CellCoordinate(column=0, row=0)
    boat = Ship(
        id="p-boat",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords)],
    )
    other = Ship(
        id="p-alive",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=9, row=9))],
    )
    board.cells[0] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=boat.id),
    )
    session = _backend_turn_session(
        board, Fleet(owner=Side.PLAYER, ships=[boat, other])
    )
    outcome = apply_backend_shot(session, 0, 0)
    assert outcome.shot.result is ShotResult.SUNK
    assert boat.status is ShipStatus.SUNK
    assert session.turn is Side.BACKEND
    assert session.player_board.cell_at(1, 0).mark is Mark.MISS
    assert not outcome.game_over


def test_should_set_game_over_when_backend_sinks_last_ship() -> None:
    """FT-025 for Backend win: last player ship SUNK. Ledger is UC-004."""
    board = empty_board(Side.PLAYER)
    coords = CellCoordinate(column=4, row=4)
    boat = Ship(
        id="p-last",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords)],
    )
    index = coords.row * BOARD_SIZE + coords.column
    board.cells[index] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=boat.id),
    )
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[boat]))
    outcome = apply_backend_shot(session, 4, 4)
    assert outcome.game_over
    assert session.winner is Side.BACKEND
    assert session.end_reason == "FleetLost"


def test_should_reject_when_backend_shoots_on_player_turn() -> None:
    """UC-003 5.4 / FT-046: Backend shot is refused when the turn is Player."""
    board = empty_board(Side.PLAYER)
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[]))
    session.turn = Side.PLAYER
    with pytest.raises(ShotRejectedError) as caught:
        apply_backend_shot(session, 0, 0)
    assert caught.value.code == "SHOT_NOT_YOUR_TURN"
    assert session.shots == []
    assert session.player_board.cell_at(0, 0).mark is Mark.UNCHECKED


def test_should_reject_when_backend_cell_already_checked() -> None:
    """FT-044 on the player board: Backend cannot re-check a cell."""
    board = empty_board(Side.PLAYER)
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[]))
    apply_backend_shot(session, 0, 0)
    session.turn = Side.BACKEND
    with pytest.raises(ShotRejectedError) as caught:
        apply_backend_shot(session, 0, 0)
    assert caught.value.code == "SHOT_CELL_CHECKED"
    assert len(session.shots) == 1


def test_should_reject_when_backend_shoots_after_game_over() -> None:
    """FT-047: Backend shot after GAME_OVER does not mutate the board."""
    board = empty_board(Side.PLAYER)
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[]))
    session.status = SessionStatus.GAME_OVER
    with pytest.raises(ShotRejectedError) as caught:
        apply_backend_shot(session, 0, 0)
    assert caught.value.code == "SHOT_GAME_OVER"
    assert session.shots == []


def test_should_shift_ttl_anchor_when_backend_shot_accepted() -> None:
    """FT-005 / A0158: accepted Backend shot moves the idle TTL anchor."""
    board = empty_board(Side.PLAYER)
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[]))
    started = session.ttl_anchor
    later = started + timedelta(seconds=30)
    apply_backend_shot(session, 0, 0, now=later)
    assert session.ttl_anchor == later


def test_should_keep_ttl_anchor_when_backend_shot_rejected() -> None:
    """FT-005: rejected Backend shot does not move idle TTL."""
    board = empty_board(Side.PLAYER)
    session = _backend_turn_session(board, Fleet(owner=Side.PLAYER, ships=[]))
    started = session.ttl_anchor
    session.turn = Side.PLAYER
    with pytest.raises(ShotRejectedError):
        apply_backend_shot(session, 0, 0, now=started + timedelta(seconds=30))
    assert session.ttl_anchor == started
