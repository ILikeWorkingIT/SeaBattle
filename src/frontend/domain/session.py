from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import uuid4

from frontend.domain.board import Board
from frontend.domain.fleet import Fleet, Ship
from frontend.domain.types import (
    CellCoordinate,
    EndReason,
    Mark,
    SessionStatus,
    ShipStatus,
    ShotResult,
    Side,
)


IDLE_TTL = timedelta(minutes=30)


@dataclass(slots=True)
class Shot:
    seq: int
    shooter: Side
    coords: CellCoordinate
    result: ShotResult


@dataclass(slots=True)
class ShotOutcome:
    shot: Shot
    buffer: list[CellCoordinate]
    game_over: bool
    winner: Side | None
    end_reason: EndReason | None
    turn: Side


@dataclass(slots=True)
class Session:
    id: str
    player_board: Board
    backend_board: Board
    player_fleet: Fleet
    backend_fleet: Fleet
    status: SessionStatus = SessionStatus.ACTIVE
    turn: Side = Side.PLAYER
    winner: Side | None = None
    end_reason: EndReason | None = None
    ttl_anchor: datetime = field(default_factory=datetime.now)
    shots: list[Shot] = field(default_factory=list)
    target_ship_id: str | None = None

    @classmethod
    def create(
        cls,
        player_board: Board,
        backend_board: Board,
        player_fleet: Fleet,
        backend_fleet: Fleet,
    ) -> Session:
        return cls(
            id=str(uuid4()),
            player_board=player_board,
            backend_board=backend_board,
            player_fleet=player_fleet,
            backend_fleet=backend_fleet,
        )

    def remain_ttl(self, now: datetime | None = None) -> timedelta:
        now = now or datetime.now()
        left = IDLE_TTL - (now - self.ttl_anchor)
        return left if left.total_seconds() > 0 else timedelta(0)

    def board_for(self, owner: Side) -> Board:
        return self.player_board if owner is Side.PLAYER else self.backend_board

    def fleet_for(self, owner: Side) -> Fleet:
        return self.player_fleet if owner is Side.PLAYER else self.backend_fleet

    def opponent_of(self, side: Side) -> Side:
        return Side.BACKEND if side is Side.PLAYER else Side.PLAYER

    def apply_shot(self, shooter: Side, coords: CellCoordinate) -> ShotOutcome:
        if self.status is not SessionStatus.ACTIVE:
            raise IllegalShot("GAME_OVER")
        if self.turn is not shooter:
            raise IllegalShot("NOT_YOUR_TURN")
        target_board = self.board_for(self.opponent_of(shooter))
        target_fleet = self.fleet_for(self.opponent_of(shooter))
        cell = target_board.cell(coords.column, coords.row)
        if cell.mark is not Mark.UNCHECKED:
            raise IllegalShot("ALREADY_CHECKED")

        self.ttl_anchor = datetime.now()
        seq = len(self.shots) + 1
        buffer: list[CellCoordinate] = []

        if cell.occupancy_ship is None:
            target_board.apply_mark(coords, Mark.MISS)
            shot = Shot(seq, shooter, coords, ShotResult.MISS)
            self.shots.append(shot)
            self.turn = self.opponent_of(shooter)
            return ShotOutcome(shot, buffer, False, None, None, self.turn)

        ship = target_fleet.ship_by_id(cell.occupancy_ship)
        for deck in ship.decks:
            if deck.coords == coords:
                deck.destroyed = True
                break
        ship.refresh_status()

        if ship.status is ShipStatus.SUNK:
            result = ShotResult.SUNK
            for deck in ship.decks:
                target_board.apply_mark(deck.coords, Mark.SUNK)
            buffer = _mark_buffer(target_board, ship)
            if shooter is Side.BACKEND:
                self.target_ship_id = None
        else:
            result = ShotResult.HIT
            target_board.apply_mark(coords, Mark.HIT)
            if shooter is Side.BACKEND:
                self.target_ship_id = ship.id

        shot = Shot(seq, shooter, coords, result)
        self.shots.append(shot)
        game_over = target_fleet.all_sunk()
        winner = None
        end_reason = None
        if game_over:
            self.status = SessionStatus.GAME_OVER
            self.winner = shooter
            self.end_reason = EndReason.FLEET_LOST
            winner = shooter
            end_reason = EndReason.FLEET_LOST
        return ShotOutcome(shot, buffer, game_over, winner, end_reason, self.turn)

    def surrender(self) -> None:
        if self.status is not SessionStatus.ACTIVE:
            return
        self.status = SessionStatus.GAME_OVER
        self.winner = Side.BACKEND
        self.end_reason = EndReason.SURRENDER


class IllegalShot(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _neighbors(coords: CellCoordinate) -> list[CellCoordinate]:
    found: list[CellCoordinate] = []
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue
            col, row = coords.column + dc, coords.row + dr
            if 0 <= col <= 9 and 0 <= row <= 9:
                found.append(CellCoordinate(col, row))
    return found


def _mark_buffer(board: Board, ship: Ship) -> list[CellCoordinate]:
    ship_cells = {deck.coords.as_tuple() for deck in ship.decks}
    marked: list[CellCoordinate] = []
    seen: set[tuple[int, int]] = set()
    for deck in ship.decks:
        for neighbor in _neighbors(deck.coords):
            key = neighbor.as_tuple()
            if key in ship_cells or key in seen:
                continue
            seen.add(key)
            cell = board.cell(neighbor.column, neighbor.row)
            if cell.mark is Mark.UNCHECKED:
                board.apply_mark(neighbor, Mark.MISS)
                marked.append(neighbor)
    return marked
