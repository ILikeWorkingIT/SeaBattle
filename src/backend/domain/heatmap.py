"""HeatmapBot: Hunt / Target aim for the backend turn (UC-003)."""

from __future__ import annotations

import random
from dataclasses import dataclass

from backend.domain.session import Board, Session, Ship
from backend.domain.types import (
    BOARD_SIZE,
    AimOutcome,
    CellCoordinate,
    Facing,
    HeatmapMode,
    Mark,
    SessionStatus,
    ShipStatus,
    Side,
    TargetAreaKind,
)


@dataclass(frozen=True, slots=True)
class Aim:
    outcome: AimOutcome
    pick: CellCoordinate | None = None
    target_ship: str | None = None
    mode: HeatmapMode | None = None
    area_kind: TargetAreaKind | None = None


def remaining_lengths(session: Session) -> tuple[int, ...]:
    return tuple(
        ship.length
        for ship in session.player_fleet.ships
        if ship.status is not ShipStatus.SUNK
    )


def wounded_ships(session: Session) -> tuple[Ship, ...]:
    return tuple(
        ship
        for ship in session.player_fleet.ships
        if ship.status is ShipStatus.WOUNDED
    )


def _blocked(board: Board, column: int, row: int) -> bool:
    return board.cell_at(column, row).mark is not Mark.UNCHECKED


def _segment(
    start: CellCoordinate, length: int, facing: Facing
) -> list[CellCoordinate] | None:
    cells: list[CellCoordinate] = []
    for i in range(length):
        column = start.column + (i if facing is Facing.HORIZONTAL else 0)
        row = start.row + (i if facing is Facing.VERTICAL else 0)
        if not (0 <= column < BOARD_SIZE and 0 <= row < BOARD_SIZE):
            return None
        cells.append(CellCoordinate(column=column, row=row))
    return cells


def hunt_weights(board: Board, lengths: tuple[int, ...]) -> list[list[int]]:
    weights = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for length in lengths:
        for facing in (Facing.HORIZONTAL, Facing.VERTICAL):
            for row in range(BOARD_SIZE):
                for column in range(BOARD_SIZE):
                    if length == 1 and facing is Facing.VERTICAL:
                        continue
                    start = CellCoordinate(column=column, row=row)
                    segment = _segment(start, length, facing)
                    if segment is None:
                        continue
                    if any(_blocked(board, cell.column, cell.row) for cell in segment):
                        continue
                    for cell in segment:
                        weights[cell.row][cell.column] += 1
    return weights


def _hit_coords(ship: Ship) -> list[CellCoordinate]:
    return [deck.coords for deck in ship.decks if deck.destroyed]


def _unchecked(board: Board, column: int, row: int) -> bool:
    if not (0 <= column < BOARD_SIZE and 0 <= row < BOARD_SIZE):
        return False
    return board.cell_at(column, row).mark is Mark.UNCHECKED


def _walk_axis(
    board: Board, column: int, row: int, d_col: int, d_row: int
) -> list[CellCoordinate]:
    """Collect UNCHECKED cells outward until the board edge, MISS, HIT, or SUNK."""
    found: list[CellCoordinate] = []
    cursor_c, cursor_r = column + d_col, row + d_row
    while 0 <= cursor_c < BOARD_SIZE and 0 <= cursor_r < BOARD_SIZE:
        mark = board.cell_at(cursor_c, cursor_r).mark
        if mark is Mark.UNCHECKED:
            found.append(CellCoordinate(column=cursor_c, row=cursor_r))
            cursor_c += d_col
            cursor_r += d_row
            continue
        break
    return found


def _span_unchecked(
    board: Board, column: int, row: int, d_col: int, d_row: int, steps: int
) -> list[CellCoordinate]:
    """UNCHECKED cells on the open segment between HITs (HIT must not abort the scan)."""
    found: list[CellCoordinate] = []
    cursor_c, cursor_r = column + d_col, row + d_row
    for _ in range(steps):
        if _unchecked(board, cursor_c, cursor_r):
            found.append(CellCoordinate(column=cursor_c, row=cursor_r))
        cursor_c += d_col
        cursor_r += d_row
    return found


def target_area(
    board: Board, ship: Ship
) -> tuple[TargetAreaKind, tuple[CellCoordinate, ...]]:
    hits = _hit_coords(ship)
    if not hits:
        return TargetAreaKind.CROSS, ()
    if len(hits) == 1:
        cell = hits[0]
        neighbours: list[CellCoordinate] = []
        for d_col, d_row in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            column, row = cell.column + d_col, cell.row + d_row
            if _unchecked(board, column, row):
                neighbours.append(CellCoordinate(column=column, row=row))
        return TargetAreaKind.CROSS, tuple(neighbours)

    rows = {hit.row for hit in hits}
    cols = {hit.column for hit in hits}
    cells: list[CellCoordinate] = []
    if len(rows) == 1:
        row = hits[0].row
        min_c = min(hit.column for hit in hits)
        max_c = max(hit.column for hit in hits)
        cells.extend(_walk_axis(board, min_c, row, -1, 0))
        cells.extend(_walk_axis(board, max_c, row, 1, 0))
        cells.extend(_span_unchecked(board, min_c, row, 1, 0, max_c - min_c - 1))
        return TargetAreaKind.AXIS, tuple(cells)
    if len(cols) == 1:
        column = hits[0].column
        min_r = min(hit.row for hit in hits)
        max_r = max(hit.row for hit in hits)
        cells.extend(_walk_axis(board, column, min_r, 0, -1))
        cells.extend(_walk_axis(board, column, max_r, 0, 1))
        cells.extend(_span_unchecked(board, column, min_r, 0, 1, max_r - min_r - 1))
        return TargetAreaKind.AXIS, tuple(cells)
    return TargetAreaKind.AXIS, ()


def _leaders(weights: list[list[int]]) -> list[tuple[CellCoordinate, int]]:
    found: list[tuple[CellCoordinate, int]] = []
    best = 0
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            weight = weights[row][column]
            if weight <= 0:
                continue
            coords = CellCoordinate(column=column, row=row)
            if weight > best:
                best = weight
                found = [(coords, weight)]
            elif weight == best:
                found.append((coords, weight))
    return found


def compute_aim(
    session: Session, rng: random.Random | None = None
) -> Aim:
    """
    Recalculate Hunt/Target weights and pick a cell (FT-028…034, FT-058, FT-064).

    Heatmap is not stored on the session and must not be sent to the player (FT-050).
    """
    if session.status is not SessionStatus.ACTIVE or session.turn is not Side.BACKEND:
        return Aim(outcome=AimOutcome.EMPTY)

    picker = rng or random.Random()
    wounded = wounded_ships(session)
    board = session.player_board

    if wounded:
        ship = wounded[0]
        kind, area = target_area(board, ship)
        weights = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        for cell in area:
            weights[cell.row][cell.column] = 1
        leaders = _leaders(weights)
        if not leaders:
            return Aim(
                outcome=AimOutcome.EMPTY,
                target_ship=ship.id,
                mode=HeatmapMode.TARGET,
                area_kind=kind,
            )
        pick, _ = picker.choice(leaders)
        return Aim(
            outcome=AimOutcome.PICKED,
            pick=pick,
            target_ship=ship.id,
            mode=HeatmapMode.TARGET,
            area_kind=kind,
        )

    lengths = remaining_lengths(session)
    if not lengths:
        return Aim(outcome=AimOutcome.EMPTY, mode=HeatmapMode.HUNT)

    weights = hunt_weights(board, lengths)
    leaders = _leaders(weights)
    if not leaders:
        return Aim(outcome=AimOutcome.EMPTY, mode=HeatmapMode.HUNT)
    pick, _ = picker.choice(leaders)
    return Aim(
        outcome=AimOutcome.PICKED,
        pick=pick,
        mode=HeatmapMode.HUNT,
    )
