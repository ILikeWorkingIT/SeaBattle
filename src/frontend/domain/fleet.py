from __future__ import annotations

import random
from dataclasses import dataclass, field

from frontend.domain.board import Board
from frontend.domain.types import (
    FLEET_SPEC,
    SHIP_LENGTH,
    CellCoordinate,
    Facing,
    ShipStatus,
    ShipType,
    Side,
)


@dataclass(slots=True)
class Deck:
    coords: CellCoordinate
    destroyed: bool = False


@dataclass(slots=True)
class Ship:
    id: str
    type: ShipType
    length: int
    facing: Facing
    decks: list[Deck]
    status: ShipStatus = ShipStatus.INTACT

    def refresh_status(self) -> None:
        hit = sum(1 for deck in self.decks if deck.destroyed)
        if hit == 0:
            self.status = ShipStatus.INTACT
        elif hit < self.length:
            self.status = ShipStatus.WOUNDED
        else:
            self.status = ShipStatus.SUNK


@dataclass(slots=True)
class Fleet:
    owner: Side
    ships: list[Ship] = field(default_factory=list)

    def ship_by_id(self, ship_id: str) -> Ship:
        for ship in self.ships:
            if ship.id == ship_id:
                return ship
        raise KeyError(ship_id)

    def remaining_lengths(self) -> list[int]:
        return [ship.length for ship in self.ships if ship.status is not ShipStatus.SUNK]

    def all_sunk(self) -> bool:
        return all(ship.status is ShipStatus.SUNK for ship in self.ships)

    def wounded(self) -> list[Ship]:
        return [ship for ship in self.ships if ship.status is ShipStatus.WOUNDED]


def _chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _touches_occupied(occupied: set[tuple[int, int]], coords: list[tuple[int, int]]) -> bool:
    for cell in coords:
        for existing in occupied:
            if _chebyshev(cell, existing) <= 1:
                return True
    return False


def generate_fleet(owner: Side, rng: random.Random | None = None) -> tuple[Fleet, Board]:
    rng = rng or random.Random()
    for _attempt in range(80):
        occupied: set[tuple[int, int]] = set()
        ships: list[Ship] = []
        board = Board(owner=owner)
        ok = True
        for index, ship_type in enumerate(FLEET_SPEC, start=1):
            length = SHIP_LENGTH[ship_type]
            placed: list[tuple[int, int]] | None = None
            facing = Facing.HORIZONTAL
            for _try in range(400):
                facing = rng.choice((Facing.HORIZONTAL, Facing.VERTICAL))
                if facing is Facing.HORIZONTAL:
                    col = rng.randint(0, 10 - length)
                    row = rng.randint(0, 9)
                    coords = [(col + i, row) for i in range(length)]
                else:
                    col = rng.randint(0, 9)
                    row = rng.randint(0, 10 - length)
                    coords = [(col, row + i) for i in range(length)]
                if any(not (0 <= c <= 9 and 0 <= r <= 9) for c, r in coords):
                    continue
                if _touches_occupied(occupied, coords):
                    continue
                placed = coords
                break
            if placed is None:
                ok = False
                break
            occupied.update(placed)
            ship_id = f"{owner.value[0]}{index:02d}"
            decks = [Deck(CellCoordinate(c, r)) for c, r in placed]
            ships.append(Ship(ship_id, ship_type, length, facing, decks))
            for c, r in placed:
                board.set_ship(CellCoordinate(c, r), ship_id)
        if ok and len(ships) == 10:
            return Fleet(owner=owner, ships=ships), board
    raise RuntimeError("Could not generate a valid fleet placement")
