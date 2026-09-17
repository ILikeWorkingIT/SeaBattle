"""API DTOs aligned with requirements/openapi.yaml (camelCase)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.session import Board, Cell, Fleet, Session, Ship, Shot
from backend.domain.types import OccupancyKind, Side


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    messageRu: str


class StatisticsSnapshotOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    games: int = Field(ge=0)
    playerWins: int = Field(ge=0)
    backendWins: int = Field(ge=0)
    avgShots: float = Field(ge=0)


class CellCoordinateOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: int
    row: int
    code: str


class OccupancyOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    ship: str | None = None


class BoardCellPrivateOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coords: CellCoordinateOut
    occupancy: OccupancyOut
    mark: str


class BoardCellPublicOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coords: CellCoordinateOut
    mark: str


class PlayerBoardOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: Literal["Player"]
    size: Literal[10]
    cells: list[BoardCellPrivateOut]


class BackendBoardOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: Literal["Backend"]
    size: Literal[10]
    cells: list[BoardCellPublicOut]


class DeckOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coords: CellCoordinateOut
    destroyed: bool


class ShipOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    length: int
    facing: str
    status: str
    decks: list[DeckOut]


class FleetOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: Literal["Player", "Backend"]
    ships: list[ShipOut]


class ShotOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seq: int
    shooter: Literal["Player", "Backend"]
    coords: CellCoordinateOut
    result: Literal["MISS", "HIT", "SUNK"]


class SessionStateOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sessionId: str
    mode: Literal["PvE"]
    status: Literal["Active", "GameOver"]
    turn: Literal["Player", "Backend"]
    ttlAnchor: str
    idleTtlSeconds: Literal[1800]
    remainTtlSeconds: int = Field(ge=0)
    playerBoard: PlayerBoardOut
    backendBoard: BackendBoardOut
    playerFleet: FleetOut
    shots: list[ShotOut] = Field(default_factory=list)
    winner: Literal["Player", "Backend"] | None = None
    endReason: Literal["FleetLost", "Surrender"] | None = None


def _coords_out(column: int, row: int, code: str) -> CellCoordinateOut:
    return CellCoordinateOut(column=column, row=row, code=code)


def _ship_out(ship: Ship) -> ShipOut:
    return ShipOut(
        id=ship.id,
        type=ship.type.value,
        length=ship.length,
        facing=ship.facing.value,
        status=ship.status.value,
        decks=[
            DeckOut(
                coords=_coords_out(d.coords.column, d.coords.row, d.coords.code),
                destroyed=d.destroyed,
            )
            for d in ship.decks
        ],
    )


def _fleet_out(fleet: Fleet) -> FleetOut:
    return FleetOut(
        owner=fleet.owner.value,  # type: ignore[arg-type]
        ships=[_ship_out(s) for s in fleet.ships],
    )


def _shot_out(shot: Shot) -> ShotOut:
    return ShotOut(
        seq=shot.seq,
        shooter=shot.shooter.value,  # type: ignore[arg-type]
        coords=_coords_out(shot.coords.column, shot.coords.row, shot.coords.code),
        result=shot.result.value,  # type: ignore[arg-type]
    )


def _player_cell(cell: Cell) -> BoardCellPrivateOut:
    occupancy = OccupancyOut(kind=cell.occupancy.kind.value)
    if cell.occupancy.kind is OccupancyKind.DECK and cell.occupancy.ship:
        occupancy = OccupancyOut(kind="Deck", ship=cell.occupancy.ship)
    return BoardCellPrivateOut(
        coords=_coords_out(cell.coords.column, cell.coords.row, cell.coords.code),
        occupancy=occupancy,
        mark=cell.mark.value,
    )


def _backend_public_cell(cell: Cell) -> BoardCellPublicOut:
    """FT-015: omit occupancy so unrevealed decks stay hidden."""
    return BoardCellPublicOut(
        coords=_coords_out(cell.coords.column, cell.coords.row, cell.coords.code),
        mark=cell.mark.value,
    )


def _player_board(board: Board) -> PlayerBoardOut:
    assert board.owner is Side.PLAYER
    return PlayerBoardOut(
        owner="Player",
        size=10,
        cells=[_player_cell(c) for c in board.cells],
    )


def _backend_board_public(board: Board) -> BackendBoardOut:
    assert board.owner is Side.BACKEND
    return BackendBoardOut(
        owner="Backend",
        size=10,
        cells=[_backend_public_cell(c) for c in board.cells],
    )


def session_to_api(session: Session, *, now: datetime | None = None) -> SessionStateOut:
    instant = now or datetime.now(timezone.utc)
    ttl = session.ttl_anchor.astimezone(timezone.utc)
    ttl_text = ttl.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return SessionStateOut(
        sessionId=session.id,
        mode="PvE",
        status=session.status.value,  # type: ignore[arg-type]
        turn=session.turn.value,  # type: ignore[arg-type]
        ttlAnchor=ttl_text,
        idleTtlSeconds=1800,
        remainTtlSeconds=session.remain_ttl_seconds(instant),
        playerBoard=_player_board(session.player_board),
        backendBoard=_backend_board_public(session.backend_board),
        playerFleet=_fleet_out(session.player_fleet),
        shots=[_shot_out(s) for s in session.shots],
        winner=session.winner.value if session.winner else None,  # type: ignore[arg-type]
        endReason=session.end_reason,  # type: ignore[arg-type]
    )
