from __future__ import annotations

from dataclasses import dataclass, field

from frontend.domain.types import CellCoordinate, Mark, Side


@dataclass(slots=True)
class Cell:
    coords: CellCoordinate
    occupancy_ship: str | None = None
    mark: Mark = Mark.UNCHECKED


@dataclass(slots=True)
class Board:
    owner: Side
    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cells:
            self.cells = {
                (c, r): Cell(CellCoordinate(c, r)) for r in range(10) for c in range(10)
            }

    def cell(self, column: int, row: int) -> Cell:
        return self.cells[(column, row)]

    def mark_at(self, column: int, row: int) -> Mark:
        return self.cell(column, row).mark

    def set_ship(self, coords: CellCoordinate, ship_id: str) -> None:
        cell = self.cell(coords.column, coords.row)
        cell.occupancy_ship = ship_id

    def apply_mark(self, coords: CellCoordinate, mark: Mark) -> None:
        self.cell(coords.column, coords.row).mark = mark
