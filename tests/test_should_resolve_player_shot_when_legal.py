"""Domain tests for player shot resolution (UC-002)."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from backend.domain.placement import generate_placement_pair
from backend.domain.session import (
    Board,
    Cell,
    Deck,
    Fleet,
    Occupancy,
    Session,
    Ship,
    empty_board,
    new_session,
)
from backend.domain.shot import ShotRejectedError, apply_player_shot
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


def _session_from_placement() -> Session:
    pair = generate_placement_pair(deadline_monotonic=time.monotonic() + 2.0)
    return new_session(
        "a" * 32,
        pair.player_board,
        pair.backend_board,
        pair.player_fleet,
        pair.backend_fleet,
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )


def _first_empty(board: Board) -> CellCoordinate:
    for cell in board.cells:
        if cell.occupancy.kind is OccupancyKind.EMPTY:
            return cell.coords
    raise AssertionError("no empty cell")


def _first_deck(board: Board) -> CellCoordinate:
    for cell in board.cells:
        if cell.occupancy.kind is OccupancyKind.DECK:
            return cell.coords
    raise AssertionError("no deck cell")


def test_should_mark_miss_and_pass_turn_when_empty_cell() -> None:
    session = _session_from_placement()
    coords = _first_empty(session.backend_board)
    outcome = apply_player_shot(session, coords.column, coords.row)
    assert outcome.shot.result is ShotResult.MISS
    assert session.turn is Side.BACKEND
    assert session.backend_board.cell_at(coords.column, coords.row).mark is Mark.MISS
    assert len(session.shots) == 1


def test_should_mark_hit_and_keep_turn_when_deck_survives() -> None:
    session = _session_from_placement()
    multi = next(
        ship for ship in session.backend_fleet.ships if ship.length >= 2
    )
    coords = multi.decks[0].coords
    outcome = apply_player_shot(session, coords.column, coords.row)
    assert outcome.shot.result is ShotResult.HIT
    assert session.turn is Side.PLAYER
    assert multi.status is ShipStatus.WOUNDED
    assert session.backend_board.cell_at(coords.column, coords.row).mark is Mark.HIT


def test_should_mark_sunk_and_perimeter_miss_when_last_deck() -> None:
    session = _session_from_placement()
    boat = next(ship for ship in session.backend_fleet.ships if ship.length == 1)
    coords = boat.decks[0].coords
    outcome = apply_player_shot(session, coords.column, coords.row)
    assert outcome.shot.result is ShotResult.SUNK
    assert boat.status is ShipStatus.SUNK
    assert session.backend_board.cell_at(coords.column, coords.row).mark is Mark.SUNK
    perimeter_marks = [
        cell for cell in outcome.affected_cells if cell.mark is Mark.MISS
    ]
    assert perimeter_marks
    assert session.turn is Side.PLAYER
    assert not outcome.game_over


def test_should_reject_when_cell_already_checked() -> None:
    session = _session_from_placement()
    coords = _first_empty(session.backend_board)
    apply_player_shot(session, coords.column, coords.row)
    session.turn = Side.PLAYER
    with pytest.raises(ShotRejectedError) as exc:
        apply_player_shot(session, coords.column, coords.row)
    assert exc.value.code == "SHOT_CELL_CHECKED"


def test_should_reject_when_not_player_turn() -> None:
    session = _session_from_placement()
    session.turn = Side.BACKEND
    coords = _first_empty(session.backend_board)
    with pytest.raises(ShotRejectedError) as exc:
        apply_player_shot(session, coords.column, coords.row)
    assert exc.value.code == "SHOT_NOT_YOUR_TURN"


def test_should_set_game_over_when_last_ship_sunk() -> None:
    """FT-071 / A0005: last SUNK of backend fleet also yields GAME_OVER; last deck is SUNK."""
    board = empty_board(Side.BACKEND)
    coords = CellCoordinate(column=0, row=0)
    ship = Ship(
        id="b01",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords, destroyed=False)],
    )
    index = coords.row * BOARD_SIZE + coords.column
    board.cells[index] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship.id),
        mark=Mark.UNCHECKED,
    )
    # Nine already-sunk placeholder ships so fleet size stays 10.
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
        "b" * 32,
        empty_board(Side.PLAYER),
        board,
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[ship, *sunk]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    outcome = apply_player_shot(session, 0, 0)
    assert outcome.shot.result is ShotResult.SUNK
    assert outcome.game_over is True
    assert session.backend_board.cell_at(0, 0).mark is Mark.SUNK
    assert session.status is SessionStatus.GAME_OVER
    assert session.winner is Side.PLAYER
    assert session.end_reason == "FleetLost"


def test_should_reject_when_coordinates_out_of_board() -> None:
    """FT-045: column/row outside [0..9] without mutating state."""
    session = _session_from_placement()
    shots_before = list(session.shots)
    with pytest.raises(ShotRejectedError) as exc:
        apply_player_shot(session, 10, 0)
    assert exc.value.code == "SHOT_OUT_OF_BOUNDS"
    assert session.shots == shots_before
    assert session.turn is Side.PLAYER


def test_should_reject_when_match_already_over() -> None:
    """FT-047: no shot after GAME_OVER."""
    session = _session_from_placement()
    session.status = SessionStatus.GAME_OVER
    coords = _first_empty(session.backend_board)
    with pytest.raises(ShotRejectedError) as exc:
        apply_player_shot(session, coords.column, coords.row)
    assert exc.value.code == "SHOT_GAME_OVER"
    assert session.shots == []


def test_should_reject_second_shot_when_turn_already_passed() -> None:
    """FT-051: extra shot of the same side after an accepted MISS is refused."""
    session = _session_from_placement()
    first = _first_empty(session.backend_board)
    apply_player_shot(session, first.column, first.row)
    other = next(
        c.coords
        for c in session.backend_board.cells
        if c.occupancy.kind is OccupancyKind.EMPTY
        and c.coords != first
        and c.mark is Mark.UNCHECKED
    )
    with pytest.raises(ShotRejectedError) as exc:
        apply_player_shot(session, other.column, other.row)
    assert exc.value.code == "SHOT_NOT_YOUR_TURN"
    assert len(session.shots) == 1


def test_should_shift_ttl_anchor_when_shot_accepted() -> None:
    """FT-005 / A0158: idle TTL shifts only on create and accepted shot."""
    session = _session_from_placement()
    original = session.ttl_anchor
    later = datetime(2026, 9, 16, 12, 30, tzinfo=timezone.utc)
    coords = _first_empty(session.backend_board)
    apply_player_shot(session, coords.column, coords.row, now=later)
    assert session.ttl_anchor == later
    assert session.ttl_anchor != original


def test_should_keep_ttl_anchor_when_shot_rejected() -> None:
    """FT-005 / A0158: a refused shot does not move the idle TTL anchor."""
    session = _session_from_placement()
    original = session.ttl_anchor
    session.turn = Side.BACKEND
    with pytest.raises(ShotRejectedError):
        apply_player_shot(session, 0, 0)
    assert session.ttl_anchor == original
    assert session.shots == []


def test_should_accept_when_corner_cell_unchecked() -> None:
    """UC-002 5.6: corner 00 is a legal target while still Unchecked."""
    session = _session_from_placement()
    outcome = apply_player_shot(session, 0, 0)
    assert outcome.shot.coords.column == 0
    assert outcome.shot.coords.row == 0
    assert outcome.shot.coords.code == "00"
    assert session.backend_board.cell_at(0, 0).mark is not Mark.UNCHECKED
    assert len(session.shots) == 1
