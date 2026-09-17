"""Map shotResolved HIT/SUNK onto fleet rows. No shooting rules — only API cells."""

from __future__ import annotations

from frontend.domain.types import (
    FLEET_SPEC,
    SHIP_LENGTH,
    Mark,
    ShipStatus,
    ShipType,
    ShotResult,
    Side,
)
from frontend.mock.static_scene import BattleScene, ShipView
from frontend.ui.cell_view import CellView

_TYPE_BY_LENGTH: dict[int, ShipType] = {length: kind for kind, length in SHIP_LENGTH.items()}


def placeholder_backend_fleet() -> list[ShipView]:
    """FT-009 composition with hidden intact decks (FT-015)."""
    return [
        ShipView(
            kind,
            ShipStatus.INTACT,
            tuple(False for _ in range(SHIP_LENGTH[kind])),
            hide_intact_bars=True,
        )
        for kind in FLEET_SPEC
    ]


def apply_shot_to_fleets(
    scene: BattleScene,
    shooter: Side,
    result: ShotResult,
    column: int,
    row: int,
    _affected: object,
) -> None:
    if result not in {ShotResult.HIT, ShotResult.SUNK}:
        return
    if shooter is Side.BACKEND:
        _apply_player_fleet(scene.player_ships, column, row, result)
        return
    if shooter is Side.PLAYER:
        _apply_backend_fleet(scene, column, row, result)


def _apply_player_fleet(
    ships: list[ShipView],
    column: int,
    row: int,
    result: ShotResult,
) -> None:
    index = _index_with_coord(ships, column, row)
    if index is None:
        return
    ship = ships[index]
    if result is ShotResult.SUNK:
        ships[index] = ShipView(
            ship.type,
            ShipStatus.SUNK,
            tuple(True for _ in ship.decks_hit),
            hide_intact_bars=False,
            deck_coords=ship.deck_coords,
            type_known=True,
        )
        return
    hits = list(ship.decks_hit)
    for i, (col, r) in enumerate(ship.deck_coords):
        if i < len(hits) and col == column and r == row:
            hits[i] = True
            break
    status = ShipStatus.SUNK if hits and all(hits) else ShipStatus.WOUNDED
    ships[index] = ShipView(
        ship.type,
        status,
        tuple(hits),
        hide_intact_bars=False,
        deck_coords=ship.deck_coords,
        type_known=True,
    )


def _apply_backend_fleet(
    scene: BattleScene,
    _column: int,
    _row: int,
    _result: ShotResult,
) -> None:
    scene.backend_ships = _backend_fleet_from_board(scene.backend_cells)


def _backend_fleet_from_board(grid: list[list[CellView]]) -> list[ShipView]:
    """Ten slots: typed intact/sunk in FLEET_SPEC order; unnamed HIT clusters take end slots."""
    sunk_kinds: list[ShipType] = []
    wounded: list[ShipView] = []
    for cells in _hit_sunk_groups(grid):
        if any(grid[row][column].mark is Mark.SUNK for column, row in cells):
            kind = _TYPE_BY_LENGTH[len(cells)]
            sunk_kinds.append(kind)
        else:
            wounded.append(
                ShipView(
                    ShipType.BOAT,
                    ShipStatus.WOUNDED,
                    tuple(True for _ in cells),
                    hide_intact_bars=True,
                    type_known=False,
                )
            )
    remaining = list(FLEET_SPEC)
    for kind in sunk_kinds:
        remaining.remove(kind)
    intact_kinds = remaining[: -len(wounded)] if wounded else remaining
    sunk_left = list(sunk_kinds)
    intact_left = list(intact_kinds)
    typed: list[ShipView] = []
    for kind in FLEET_SPEC:
        if kind in sunk_left:
            sunk_left.remove(kind)
            typed.append(
                ShipView(
                    kind,
                    ShipStatus.SUNK,
                    tuple(True for _ in range(SHIP_LENGTH[kind])),
                    hide_intact_bars=False,
                    type_known=True,
                )
            )
        elif kind in intact_left:
            intact_left.remove(kind)
            typed.append(
                ShipView(
                    kind,
                    ShipStatus.INTACT,
                    tuple(False for _ in range(SHIP_LENGTH[kind])),
                    hide_intact_bars=True,
                    type_known=True,
                )
            )
    return typed + wounded


def _hit_sunk_groups(grid: list[list[CellView]]) -> list[list[tuple[int, int]]]:
    seen: set[tuple[int, int]] = set()
    groups: list[list[tuple[int, int]]] = []
    for row in range(10):
        for column in range(10):
            origin = (column, row)
            if origin in seen or not _is_hit_or_sunk(grid, column, row):
                continue
            stack = [origin]
            seen.add(origin)
            cells: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    nxt = (nx, ny)
                    if nxt not in seen and _is_hit_or_sunk(grid, nx, ny):
                        seen.add(nxt)
                        stack.append(nxt)
            groups.append(cells)
    return groups


def _index_with_coord(ships: list[ShipView], column: int, row: int) -> int | None:
    for index, ship in enumerate(ships):
        if (column, row) in ship.deck_coords:
            return index
    return None


def _is_hit_or_sunk(grid: list[list[CellView]], column: int, row: int) -> bool:
    if not (0 <= column <= 9 and 0 <= row <= 9):
        return False
    return grid[row][column].mark in {Mark.HIT, Mark.SUNK}
