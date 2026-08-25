from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from frontend.domain.board import Board
from frontend.domain.fleet import Fleet, Ship
from frontend.domain.types import CellCoordinate, Mark, ShipStatus


class HeatmapMode(str, Enum):
    HUNT = "Hunt"
    TARGET = "Target"


class AimOutcome(str, Enum):
    PICKED = "Picked"
    EMPTY = "Empty"


@dataclass(frozen=True, slots=True)
class Aim:
    outcome: AimOutcome
    pick: CellCoordinate | None
    mode: HeatmapMode
    target_ship: str | None = None


def aim(board: Board, fleet: Fleet, preferred_target: str | None = None) -> Aim:
    wounded = fleet.wounded()
    if wounded:
        ship = _pick_wounded(wounded, preferred_target)
        return _target_mode(board, ship)
    return _hunt_mode(board, fleet.remaining_lengths())


def _pick_wounded(wounded: list[Ship], preferred: str | None) -> Ship:
    if preferred:
        for ship in wounded:
            if ship.id == preferred:
                return ship
    return wounded[0]


def _hunt_mode(board: Board, lengths: list[int]) -> Aim:
    weights = [[0] * 10 for _ in range(10)]
    for length in lengths:
        _accumulate(board, weights, length, horizontal=True)
        _accumulate(board, weights, length, horizontal=False)
    pick = _argmax(weights)
    if pick is None:
        return Aim(AimOutcome.EMPTY, None, HeatmapMode.HUNT)
    return Aim(AimOutcome.PICKED, pick, HeatmapMode.HUNT)


def _accumulate(board: Board, weights: list[list[int]], length: int, horizontal: bool) -> None:
    if horizontal:
        for row in range(10):
            for col in range(11 - length):
                cells = [(col + i, row) for i in range(length)]
                if _free(board, cells):
                    for c, r in cells:
                        weights[r][c] += 1
        return
    for col in range(10):
        for row in range(11 - length):
            cells = [(col, row + i) for i in range(length)]
            if _free(board, cells):
                for c, r in cells:
                    weights[r][c] += 1


def _free(board: Board, cells: list[tuple[int, int]]) -> bool:
    return all(board.mark_at(c, r) is Mark.UNCHECKED for c, r in cells)


def _target_mode(board: Board, ship: Ship) -> Aim:
    hits = [deck.coords for deck in ship.decks if deck.destroyed]
    candidates: list[CellCoordinate] = []
    if len(hits) == 1:
        origin = hits[0]
        for dc, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            col, row = origin.column + dc, origin.row + dr
            if 0 <= col <= 9 and 0 <= row <= 9 and board.mark_at(col, row) is Mark.UNCHECKED:
                candidates.append(CellCoordinate(col, row))
    else:
        columns = {item.column for item in hits}
        rows = {item.row for item in hits}
        if len(rows) == 1:
            row = hits[0].row
            left = min(item.column for item in hits) - 1
            right = max(item.column for item in hits) + 1
            if left >= 0 and board.mark_at(left, row) is Mark.UNCHECKED:
                candidates.append(CellCoordinate(left, row))
            if right <= 9 and board.mark_at(right, row) is Mark.UNCHECKED:
                candidates.append(CellCoordinate(right, row))
        elif len(columns) == 1:
            col = hits[0].column
            up = min(item.row for item in hits) - 1
            down = max(item.row for item in hits) + 1
            if up >= 0 and board.mark_at(col, up) is Mark.UNCHECKED:
                candidates.append(CellCoordinate(col, up))
            if down <= 9 and board.mark_at(col, down) is Mark.UNCHECKED:
                candidates.append(CellCoordinate(col, down))
    if not candidates:
        return Aim(AimOutcome.EMPTY, None, HeatmapMode.TARGET, ship.id)
    pick = candidates[0]
    return Aim(AimOutcome.PICKED, pick, HeatmapMode.TARGET, ship.id)


def _argmax(weights: list[list[int]]) -> CellCoordinate | None:
    best = 0
    leaders: list[CellCoordinate] = []
    for row in range(10):
        for col in range(10):
            value = weights[row][col]
            if value <= 0:
                continue
            if value > best:
                best = value
                leaders = [CellCoordinate(col, row)]
            elif value == best:
                leaders.append(CellCoordinate(col, row))
    if not leaders:
        return None
    return random.choice(leaders)
