"""Apply an accepted shot to the opponent board (UC-002 / UC-003)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.domain.session import Board, Cell, Deck, Session, Ship, Shot
from backend.domain.types import (
    BOARD_SIZE,
    CellCoordinate,
    EndReason,
    Mark,
    OccupancyKind,
    SessionStatus,
    ShipStatus,
    ShotResult,
    Side,
)


class ShotRejectedError(Exception):
    """Shot refused without mutating session state."""

    def __init__(self, code: str, message: str, message_ru: str) -> None:
        super().__init__(code)
        self.code = code
        self.message = message
        self.message_ru = message_ru


@dataclass(frozen=True, slots=True)
class AffectedCell:
    coords: CellCoordinate
    mark: Mark


@dataclass(frozen=True, slots=True)
class ShotApplication:
    shot: Shot
    affected_cells: tuple[AffectedCell, ...]
    turn: Side
    remain_ttl_seconds: int
    game_over: bool


def _set_cell_mark(board: Board, coords: CellCoordinate, mark: Mark) -> Cell:
    index = coords.row * board.size + coords.column
    old = board.cells[index]
    new_cell = Cell(coords=old.coords, occupancy=old.occupancy, mark=mark)
    board.cells[index] = new_cell
    return new_cell


def _perimeter(coords_list: list[CellCoordinate]) -> list[CellCoordinate]:
    occupied = set(coords_list)
    buffer: set[CellCoordinate] = set()
    for cell in coords_list:
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                column = cell.column + dc
                row = cell.row + dr
                if not (0 <= column < BOARD_SIZE and 0 <= row < BOARD_SIZE):
                    continue
                neighbour = CellCoordinate(column=column, row=row)
                if neighbour not in occupied:
                    buffer.add(neighbour)
    return sorted(buffer, key=lambda c: (c.row, c.column))


def _find_ship(fleet_ships: list[Ship], ship_id: str) -> Ship:
    for ship in fleet_ships:
        if ship.id == ship_id:
            return ship
    raise RuntimeError(f"ship {ship_id} missing from fleet")


def _update_ship_after_hit(ship: Ship, hit_coords: CellCoordinate) -> ShotResult:
    new_decks: list[Deck] = []
    for deck in ship.decks:
        if deck.coords == hit_coords:
            new_decks.append(Deck(coords=deck.coords, destroyed=True))
        else:
            new_decks.append(deck)
    ship.decks = new_decks
    destroyed = sum(1 for d in ship.decks if d.destroyed)
    if destroyed == ship.length:
        ship.status = ShipStatus.SUNK
        return ShotResult.SUNK
    ship.status = ShipStatus.WOUNDED
    return ShotResult.HIT


def _fleet_destroyed(ships: list[Ship]) -> bool:
    return all(ship.status is ShipStatus.SUNK for ship in ships)


def apply_player_shot(
    session: Session,
    column: int,
    row: int,
    *,
    now: datetime | None = None,
) -> ShotApplication:
    """Mutate ``session`` with an accepted player shot on the backend board."""
    return _apply_side_shot(session, Side.PLAYER, column, row, now=now)


def apply_backend_shot(
    session: Session,
    column: int,
    row: int,
    *,
    now: datetime | None = None,
) -> ShotApplication:
    """Mutate ``session`` with an accepted backend shot on the player board."""
    return _apply_side_shot(session, Side.BACKEND, column, row, now=now)


def _apply_side_shot(
    session: Session,
    shooter: Side,
    column: int,
    row: int,
    *,
    now: datetime | None = None,
) -> ShotApplication:
    """
    Apply a legal shot for ``shooter``.

    Raises ``ShotRejectedError`` without changes when the shot is illegal.
    """
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)

    if session.status is SessionStatus.GAME_OVER:
        raise ShotRejectedError(
            "SHOT_GAME_OVER",
            "The match is already over.",
            "Партия уже завершена.",
        )
    if session.turn is not shooter:
        raise ShotRejectedError(
            "SHOT_NOT_YOUR_TURN",
            "It is not your turn.",
            "Сейчас не ваш ход.",
        )
    if not (0 <= column < BOARD_SIZE and 0 <= row < BOARD_SIZE):
        raise ShotRejectedError(
            "SHOT_OUT_OF_BOUNDS",
            "Shot coordinates are outside the board.",
            "Координаты выстрела вне поля.",
        )

    coords = CellCoordinate(column=column, row=row)
    if shooter is Side.PLAYER:
        target = session.backend_board
        fleet_ships = session.backend_fleet.ships
        miss_turn = Side.BACKEND
        hit_turn = Side.PLAYER
    else:
        target = session.player_board
        fleet_ships = session.player_fleet.ships
        miss_turn = Side.PLAYER
        hit_turn = Side.BACKEND

    cell = target.cell_at(column, row)
    if cell.mark is not Mark.UNCHECKED:
        raise ShotRejectedError(
            "SHOT_CELL_CHECKED",
            "This cell was already checked.",
            "Эта клетка уже проверена.",
        )

    affected: list[AffectedCell] = []
    if cell.occupancy.kind is OccupancyKind.EMPTY:
        _set_cell_mark(target, coords, Mark.MISS)
        result = ShotResult.MISS
        affected.append(AffectedCell(coords=coords, mark=Mark.MISS))
        session.turn = miss_turn
    else:
        assert cell.occupancy.ship is not None
        ship = _find_ship(fleet_ships, cell.occupancy.ship)
        result = _update_ship_after_hit(ship, coords)
        if result is ShotResult.HIT:
            _set_cell_mark(target, coords, Mark.HIT)
            affected.append(AffectedCell(coords=coords, mark=Mark.HIT))
        else:
            _set_cell_mark(target, coords, Mark.SUNK)
            affected.append(AffectedCell(coords=coords, mark=Mark.SUNK))
            for buffer_coords in _perimeter([d.coords for d in ship.decks]):
                buffer_cell = target.cell_at(buffer_coords.column, buffer_coords.row)
                if buffer_cell.mark is Mark.UNCHECKED:
                    _set_cell_mark(target, buffer_coords, Mark.MISS)
                    affected.append(
                        AffectedCell(coords=buffer_coords, mark=Mark.MISS)
                    )
        session.turn = hit_turn

    seq = len(session.shots) + 1
    shot = Shot(seq=seq, shooter=shooter, coords=coords, result=result)
    session.shots.append(shot)
    session.ttl_anchor = instant

    game_over = False
    if result is ShotResult.SUNK and _fleet_destroyed(fleet_ships):
        session.status = SessionStatus.GAME_OVER
        session.winner = shooter
        session.end_reason = EndReason.FLEET_LOST.value
        game_over = True

    return ShotApplication(
        shot=shot,
        affected_cells=tuple(affected),
        turn=session.turn,
        remain_ttl_seconds=session.remain_ttl_seconds(instant),
        game_over=game_over,
    )
