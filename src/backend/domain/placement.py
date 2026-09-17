"""Pseudo-random fleet placement (FT-010…FT-013)."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from backend.domain.session import Board, Cell, Deck, Fleet, Occupancy, Ship, empty_board
from backend.domain.types import (
    BOARD_SIZE,
    FLEET_BLUEPRINT,
    SHIP_LENGTH,
    CellCoordinate,
    Facing,
    Mark,
    OccupancyKind,
    ShipStatus,
    ShipType,
    Side,
)


class PlacementTimeoutError(Exception):
    """No valid placement found within the start window (NFT-015 / FT-010)."""


@dataclass(frozen=True, slots=True)
class PlacementPair:
    player_board: Board
    backend_board: Board
    player_fleet: Fleet
    backend_fleet: Fleet


def _chebyshev(a: CellCoordinate, b: CellCoordinate) -> int:
    return max(abs(a.column - b.column), abs(a.row - b.row))


def _segment(
    start: CellCoordinate,
    length: int,
    facing: Facing,
) -> list[CellCoordinate] | None:
    cells: list[CellCoordinate] = []
    for i in range(length):
        column = start.column + (i if facing is Facing.HORIZONTAL else 0)
        row = start.row + (i if facing is Facing.VERTICAL else 0)
        if not (0 <= column < BOARD_SIZE and 0 <= row < BOARD_SIZE):
            return None
        cells.append(CellCoordinate(column=column, row=row))
    return cells


def _fits(candidate: list[CellCoordinate], occupied: set[CellCoordinate]) -> bool:
    for cell in candidate:
        for other in occupied:
            if _chebyshev(cell, other) < 2:
                return False
    return True


def _place_one_fleet(
    owner: Side,
    rng: random.Random,
    ship_id_prefix: str,
) -> tuple[Board, Fleet]:
    occupied: set[CellCoordinate] = set()
    ships: list[Ship] = []
    for index, ship_type in enumerate(FLEET_BLUEPRINT, start=1):
        length = SHIP_LENGTH[ship_type]
        placed = False
        for _ in range(500):
            facing = Facing.HORIZONTAL if rng.random() < 0.5 else Facing.VERTICAL
            start = CellCoordinate(
                column=rng.randrange(BOARD_SIZE),
                row=rng.randrange(BOARD_SIZE),
            )
            segment = _segment(start, length, facing)
            if segment is None or not _fits(segment, occupied):
                continue
            ship_id = f"{ship_id_prefix}{index:02d}"
            decks = [Deck(coords=c, destroyed=False) for c in segment]
            ships.append(
                Ship(
                    id=ship_id,
                    type=ship_type,
                    length=length,
                    facing=facing,
                    status=ShipStatus.INTACT,
                    decks=decks,
                )
            )
            occupied.update(segment)
            placed = True
            break
        if not placed:
            raise RuntimeError("failed to place ship in attempt")
    board = empty_board(owner)
    occupancy_map = {
        deck.coords: Occupancy(kind=OccupancyKind.DECK, ship=ship.id)
        for ship in ships
        for deck in ship.decks
    }
    cells: list[Cell] = []
    for cell in board.cells:
        occupancy = occupancy_map.get(
            cell.coords,
            Occupancy(kind=OccupancyKind.EMPTY),
        )
        cells.append(
            Cell(coords=cell.coords, occupancy=occupancy, mark=Mark.UNCHECKED)
        )
    return Board(owner=owner, size=BOARD_SIZE, cells=cells), Fleet(owner=owner, ships=ships)


def generate_placement_pair(
    *,
    deadline_monotonic: float,
    rng: random.Random | None = None,
) -> PlacementPair:
    """Generate two independent valid fleets before ``deadline_monotonic``."""
    generator = rng or random.Random()
    while time.monotonic() < deadline_monotonic:
        try:
            player_board, player_fleet = _place_one_fleet(
                Side.PLAYER, generator, "p"
            )
            backend_board, backend_fleet = _place_one_fleet(
                Side.BACKEND, generator, "b"
            )
        except RuntimeError:
            continue
        return PlacementPair(
            player_board=player_board,
            backend_board=backend_board,
            player_fleet=player_fleet,
            backend_fleet=backend_fleet,
        )
    raise PlacementTimeoutError()


def assert_fleet_valid(fleet: Fleet) -> None:
    """Raise AssertionError if composition or spacing rules fail."""
    assert len(fleet.ships) == 10
    assert sum(ship.length for ship in fleet.ships) == 20
    counts: dict[ShipType, int] = {t: 0 for t in ShipType}
    for ship in fleet.ships:
        assert ship.length == SHIP_LENGTH[ship.type]
        assert len(ship.decks) == ship.length
        counts[ship.type] += 1
        cols = {d.coords.column for d in ship.decks}
        rows = {d.coords.row for d in ship.decks}
        if ship.facing is Facing.HORIZONTAL:
            assert len(rows) == 1 and len(cols) == ship.length
        else:
            assert len(cols) == 1 and len(rows) == ship.length
    assert counts[ShipType.BATTLESHIP] == 1
    assert counts[ShipType.CRUISER] == 2
    assert counts[ShipType.DESTROYER] == 3
    assert counts[ShipType.BOAT] == 4
    all_decks = [d.coords for ship in fleet.ships for d in ship.decks]
    assert len(all_decks) == len(set(all_decks))
    for i, a in enumerate(all_decks):
        for b in all_decks[i + 1 :]:
            same_ship = any(
                a in [d.coords for d in ship.decks]
                and b in [d.coords for d in ship.decks]
                for ship in fleet.ships
            )
            if same_ship:
                continue
            assert _chebyshev(a, b) >= 2
