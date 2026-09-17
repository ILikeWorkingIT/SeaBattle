"""Board, fleet and session aggregate fragments for UC-001."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.domain.types import (
    BOARD_SIZE,
    IDLE_TTL_SECONDS,
    CellCoordinate,
    Facing,
    GameMode,
    Mark,
    OccupancyKind,
    SessionStatus,
    ShipStatus,
    ShipType,
    ShotResult,
    Side,
)


@dataclass(frozen=True, slots=True)
class Occupancy:
    kind: OccupancyKind
    ship: str | None = None


@dataclass(frozen=True, slots=True)
class Cell:
    coords: CellCoordinate
    occupancy: Occupancy
    mark: Mark = Mark.UNCHECKED


@dataclass(frozen=True, slots=True)
class Deck:
    coords: CellCoordinate
    destroyed: bool = False


@dataclass(slots=True)
class Ship:
    id: str
    type: ShipType
    length: int
    facing: Facing
    status: ShipStatus
    decks: list[Deck]


@dataclass(slots=True)
class Fleet:
    owner: Side
    ships: list[Ship]


@dataclass(frozen=True, slots=True)
class Shot:
    """Accepted shot only (FT-002); rejections do not create records."""

    seq: int
    shooter: Side
    coords: CellCoordinate
    result: ShotResult


@dataclass(slots=True)
class Board:
    owner: Side
    size: int
    cells: list[Cell]

    def cell_at(self, column: int, row: int) -> Cell:
        return self.cells[row * self.size + column]


@dataclass(slots=True)
class Session:
    """Operational match state stored on the backend (FT-002)."""

    id: str
    mode: GameMode
    status: SessionStatus
    turn: Side
    ttl_anchor: datetime
    idle_ttl_seconds: int
    connected: bool
    player_board: Board
    backend_board: Board
    player_fleet: Fleet
    backend_fleet: Fleet
    shots: list[Shot] = field(default_factory=list)
    winner: Side | None = None
    end_reason: str | None = None

    def remain_ttl_seconds(self, now: datetime | None = None) -> int:
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        anchor = self.ttl_anchor
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=timezone.utc)
        elapsed = (instant - anchor).total_seconds()
        remain = int(self.idle_ttl_seconds - elapsed)
        return max(0, remain)


def empty_board(owner: Side) -> Board:
    cells = [
        Cell(
            coords=CellCoordinate(column=c, row=r),
            occupancy=Occupancy(kind=OccupancyKind.EMPTY),
            mark=Mark.UNCHECKED,
        )
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
    ]
    return Board(owner=owner, size=BOARD_SIZE, cells=cells)


def new_session(
    session_id: str,
    player_board: Board,
    backend_board: Board,
    player_fleet: Fleet,
    backend_fleet: Fleet,
    *,
    ttl_anchor: datetime | None = None,
) -> Session:
    return Session(
        id=session_id,
        mode=GameMode.PVE,
        status=SessionStatus.ACTIVE,
        turn=Side.PLAYER,
        ttl_anchor=ttl_anchor or datetime.now(timezone.utc),
        idle_ttl_seconds=IDLE_TTL_SECONDS,
        connected=False,
        player_board=player_board,
        backend_board=backend_board,
        player_fleet=player_fleet,
        backend_fleet=backend_fleet,
        shots=[],
    )
