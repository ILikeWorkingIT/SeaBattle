"""Serialize / deserialize Session for Redis JSON storage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.domain.session import (
    Board,
    Cell,
    Deck,
    Fleet,
    Occupancy,
    Session,
    Ship,
    Shot,
)
from backend.domain.types import (
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


def _coord(data: dict[str, Any]) -> CellCoordinate:
    return CellCoordinate(column=int(data["column"]), row=int(data["row"]))


def _cell(data: dict[str, Any]) -> Cell:
    occ = data["occupancy"]
    return Cell(
        coords=_coord(data["coords"]),
        occupancy=Occupancy(
            kind=OccupancyKind(occ["kind"]),
            ship=occ.get("ship"),
        ),
        mark=Mark(data["mark"]),
    )


def _ship(data: dict[str, Any]) -> Ship:
    return Ship(
        id=data["id"],
        type=ShipType(data["type"]),
        length=int(data["length"]),
        facing=Facing(data["facing"]),
        status=ShipStatus(data["status"]),
        decks=[
            Deck(coords=_coord(d["coords"]), destroyed=bool(d["destroyed"]))
            for d in data["decks"]
        ],
    )


def _board(data: dict[str, Any]) -> Board:
    return Board(
        owner=Side(data["owner"]),
        size=int(data["size"]),
        cells=[_cell(c) for c in data["cells"]],
    )


def _fleet(data: dict[str, Any]) -> Fleet:
    return Fleet(owner=Side(data["owner"]), ships=[_ship(s) for s in data["ships"]])


def session_to_dict(session: Session) -> dict[str, Any]:
    def cell_dict(cell: Cell) -> dict[str, Any]:
        occupancy: dict[str, Any] = {"kind": cell.occupancy.kind.value}
        if cell.occupancy.ship is not None:
            occupancy["ship"] = cell.occupancy.ship
        return {
            "coords": {
                "column": cell.coords.column,
                "row": cell.coords.row,
                "code": cell.coords.code,
            },
            "occupancy": occupancy,
            "mark": cell.mark.value,
        }

    def ship_dict(ship: Ship) -> dict[str, Any]:
        return {
            "id": ship.id,
            "type": ship.type.value,
            "length": ship.length,
            "facing": ship.facing.value,
            "status": ship.status.value,
            "decks": [
                {
                    "coords": {
                        "column": d.coords.column,
                        "row": d.coords.row,
                        "code": d.coords.code,
                    },
                    "destroyed": d.destroyed,
                }
                for d in ship.decks
            ],
        }

    def board_dict(board: Board) -> dict[str, Any]:
        return {
            "owner": board.owner.value,
            "size": board.size,
            "cells": [cell_dict(c) for c in board.cells],
        }

    def fleet_dict(fleet: Fleet) -> dict[str, Any]:
        return {
            "owner": fleet.owner.value,
            "ships": [ship_dict(s) for s in fleet.ships],
        }

    def shot_dict(shot: Shot) -> dict[str, Any]:
        return {
            "seq": shot.seq,
            "shooter": shot.shooter.value,
            "coords": {
                "column": shot.coords.column,
                "row": shot.coords.row,
                "code": shot.coords.code,
            },
            "result": shot.result.value,
        }

    return {
        "id": session.id,
        "mode": session.mode.value,
        "status": session.status.value,
        "turn": session.turn.value,
        "ttlAnchor": session.ttl_anchor.astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "idleTtlSeconds": session.idle_ttl_seconds,
        "connected": session.connected,
        "playerBoard": board_dict(session.player_board),
        "backendBoard": board_dict(session.backend_board),
        "playerFleet": fleet_dict(session.player_fleet),
        "backendFleet": fleet_dict(session.backend_fleet),
        "shots": [shot_dict(s) for s in session.shots],
        "winner": session.winner.value if session.winner else None,
        "endReason": session.end_reason,
    }


def session_from_dict(data: dict[str, Any]) -> Session:
    ttl_raw = data["ttlAnchor"]
    if isinstance(ttl_raw, str):
        ttl_anchor = datetime.fromisoformat(ttl_raw.replace("Z", "+00:00"))
    else:
        ttl_anchor = ttl_raw
    winner_raw = data.get("winner")
    shots_raw = data.get("shots") or []
    shots = [
        Shot(
            seq=int(item["seq"]),
            shooter=Side(item["shooter"]),
            coords=_coord(item["coords"]),
            result=ShotResult(item["result"]),
        )
        for item in shots_raw
    ]
    return Session(
        id=data["id"],
        mode=GameMode(data["mode"]),
        status=SessionStatus(data["status"]),
        turn=Side(data["turn"]),
        ttl_anchor=ttl_anchor,
        idle_ttl_seconds=int(data["idleTtlSeconds"]),
        connected=bool(data.get("connected", False)),
        player_board=_board(data["playerBoard"]),
        backend_board=_board(data["backendBoard"]),
        player_fleet=_fleet(data["playerFleet"]),
        backend_fleet=_fleet(data["backendFleet"]),
        shots=shots,
        winner=Side(winner_raw) if winner_raw else None,
        end_reason=data.get("endReason"),
    )
