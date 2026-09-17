from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal

from frontend.client.config import CREATE_SESSION_TIMEOUT_SECONDS, api_base_url
from frontend.client.fleet_status import placeholder_backend_fleet
from frontend.domain.types import (
    EndReason,
    Mark,
    ShipStatus,
    ShipType,
    ShotResult,
    Side,
)
from frontend.i18n import STRINGS
from frontend.mock.static_scene import BattleScene, GameOverView, ShipView, ShotView
from frontend.ui.cell_view import CellView

# OpenAPI examples (A0157): used only when the body has no message fields.
_CANON_MESSAGES: dict[str, tuple[str, str]] = {
    "SESSION_LIMIT_REACHED": (STRINGS["en"]["err_no_slot"], STRINGS["ru"]["err_no_slot"]),
    "SESSION_START_FAILED": (STRINGS["en"]["err_start_failed"], STRINGS["ru"]["err_start_failed"]),
    "VALIDATION_ERROR": (STRINGS["en"]["err_validation"], STRINGS["ru"]["err_validation"]),
    "INTERNAL_ERROR": (STRINGS["en"]["err_internal"], STRINGS["ru"]["err_internal"]),
}

_MARK: dict[str, Mark] = {
    "Unchecked": Mark.UNCHECKED,
    "MISS": Mark.MISS,
    "HIT": Mark.HIT,
    "SUNK": Mark.SUNK,
}
_SHIP_TYPE: dict[str, ShipType] = {
    "Battleship": ShipType.BATTLESHIP,
    "Cruiser": ShipType.CRUISER,
    "Destroyer": ShipType.DESTROYER,
    "Boat": ShipType.BOAT,
}
_SHIP_STATUS: dict[str, ShipStatus] = {
    "Intact": ShipStatus.INTACT,
    "Wounded": ShipStatus.WOUNDED,
    "Sunk": ShipStatus.SUNK,
}
_SIDE: dict[str, Side] = {"Player": Side.PLAYER, "Backend": Side.BACKEND}
_SHOT: dict[str, ShotResult] = {"MISS": ShotResult.MISS, "HIT": ShotResult.HIT, "SUNK": ShotResult.SUNK}


@dataclass(frozen=True, slots=True)
class StartSessionOutcome:
    kind: Literal["success", "timeout", "unreachable", "http"]
    scene: BattleScene | None = None
    http_status: int | None = None
    code: str | None = None
    message: str = ""
    message_ru: str = ""

    def text_for(self, russian: bool) -> str:
        chosen = self.message_ru if russian else self.message
        if chosen:
            return chosen
        if self.kind in {"timeout", "unreachable"}:
            table = STRINGS["ru" if russian else "en"]
            return table["err_timeout"]
        pair = _CANON_MESSAGES.get(self.code or "")
        if pair is not None:
            return pair[1] if russian else pair[0]
        fallback = _CANON_MESSAGES["SESSION_START_FAILED"]
        return fallback[1] if russian else fallback[0]


def create_session(base_url: str | None = None, timeout: float | None = None) -> StartSessionOutcome:
    url = f"{(base_url or api_base_url()).rstrip('/')}/sessions"
    wait = CREATE_SESSION_TIMEOUT_SECONDS if timeout is None else timeout
    request = urllib.request.Request(
        url,
        data=None,
        method="POST",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=wait) as response:
            raw = response.read().decode("utf-8")
            status = int(response.status)
            payload = _parse_json_object(raw)
            if status == 201 and payload is not None:
                try:
                    scene = session_state_to_scene(payload)
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    return _from_error_payload(201, {"code": "SESSION_START_FAILED"})
                return StartSessionOutcome(
                    kind="success",
                    scene=scene,
                    http_status=201,
                )
            return _from_error_payload(status, payload)
    except TimeoutError:
        return StartSessionOutcome(kind="timeout")
    except socket.timeout:
        return StartSessionOutcome(kind="timeout")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return _from_error_payload(int(exc.code), _parse_json_object(raw))
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, TimeoutError | socket.timeout):
            return StartSessionOutcome(kind="timeout")
        return StartSessionOutcome(kind="unreachable")
    except json.JSONDecodeError:
        return _from_error_payload(0, {"code": "SESSION_START_FAILED"})
    except OSError:
        return StartSessionOutcome(kind="unreachable")


def session_state_to_scene(payload: dict[str, object]) -> BattleScene:
    player_board = payload["playerBoard"]
    backend_board = payload["backendBoard"]
    if not isinstance(player_board, dict) or not isinstance(backend_board, dict):
        raise TypeError("boards must be objects")
    fleet = payload["playerFleet"]
    if not isinstance(fleet, dict):
        raise TypeError("playerFleet must be an object")
    shots_raw = payload["shots"]
    if not isinstance(shots_raw, list):
        raise TypeError("shots must be an array")
    shots = _map_shots(shots_raw)
    remain = payload["remainTtlSeconds"]
    if not isinstance(remain, int) or isinstance(remain, bool) or remain < 0:
        raise TypeError("remainTtlSeconds must be a non-negative int")
    session_id = str(payload["sessionId"])
    if not session_id:
        raise ValueError("sessionId required")
    turn = str(payload["turn"])
    if turn not in {"Player", "Backend"}:
        raise ValueError("turn must be Player or Backend")
    return BattleScene(
        session_id=session_id,
        player_turn=turn == "Player",
        ttl_seconds=int(remain),
        player_cells=_map_player_board(player_board),
        backend_cells=_map_backend_board(backend_board),
        player_ships=_map_player_fleet(fleet),
        backend_ships=placeholder_backend_fleet(),
        shots=shots,
        game_over=GameOverView(
            player_won=False,
            end_reason=EndReason.SURRENDER,
            shot_count=len(shots),
        ),
        last_shot_seq=max((item.seq for item in shots), default=0),
        match_over=str(payload.get("status", "Active")) == "GameOver",
    )


def _from_error_payload(status: int, payload: dict[str, object] | None) -> StartSessionOutcome:
    code: str | None = None
    message = ""
    message_ru = ""
    if payload is not None:
        raw_code = payload.get("code")
        if isinstance(raw_code, str):
            code = raw_code
        raw_en = payload.get("message")
        raw_ru = payload.get("messageRu")
        if isinstance(raw_en, str):
            message = raw_en
        if isinstance(raw_ru, str):
            message_ru = raw_ru
    if code is None:
        if status == 409:
            code = "SESSION_LIMIT_REACHED"
        elif status == 503:
            code = "SESSION_START_FAILED"
    if not message and not message_ru and code in _CANON_MESSAGES:
        message, message_ru = _CANON_MESSAGES[code]
    return StartSessionOutcome(
        kind="http",
        http_status=status,
        code=code,
        message=message,
        message_ru=message_ru,
    )


def _parse_json_object(raw: str) -> dict[str, object] | None:
    if not raw.strip():
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        return None
    return data


def _empty_grid() -> list[list[CellView]]:
    return [[CellView(Mark.UNCHECKED) for _ in range(10)] for _ in range(10)]


def _map_player_board(board: dict[str, object]) -> list[list[CellView]]:
    grid = _empty_grid()
    cells = board.get("cells") or []
    if not isinstance(cells, list):
        return grid
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        column, row = _coords(cell)
        occupancy = cell.get("occupancy")
        has_ship = isinstance(occupancy, dict) and occupancy.get("kind") == "Deck"
        grid[row][column] = CellView(_mark(cell.get("mark")), has_ship)
    return grid


def _map_backend_board(board: dict[str, object]) -> list[list[CellView]]:
    grid = _empty_grid()
    cells = board.get("cells") or []
    if not isinstance(cells, list):
        return grid
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        column, row = _coords(cell)
        grid[row][column] = CellView(_mark(cell.get("mark")), has_ship=False)
    return grid


def _map_player_fleet(fleet: dict[str, object]) -> list[ShipView]:
    ships_raw = fleet.get("ships") or []
    if not isinstance(ships_raw, list):
        return []
    views: list[ShipView] = []
    for ship in ships_raw:
        if not isinstance(ship, dict):
            continue
        type_name = str(ship.get("type", ""))
        status_name = str(ship.get("status", ""))
        ship_type = _SHIP_TYPE.get(type_name)
        status = _SHIP_STATUS.get(status_name)
        if ship_type is None or status is None:
            continue
        decks_raw = ship.get("decks") or []
        hits: list[bool] = []
        coords: list[tuple[int, int]] = []
        if isinstance(decks_raw, list):
            for item in decks_raw:
                if not isinstance(item, dict):
                    continue
                hits.append(bool(item.get("destroyed")))
                raw_coords = item.get("coords")
                if isinstance(raw_coords, dict):
                    coords.append((int(raw_coords["column"]), int(raw_coords["row"])))
        views.append(
            ShipView(
                ship_type,
                status,
                tuple(hits),
                hide_intact_bars=False,
                deck_coords=tuple(coords),
            )
        )
    return views


def _map_shots(items: list[object]) -> list[ShotView]:
    shots: list[ShotView] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        shooter = _SIDE.get(str(item.get("shooter", "")))
        result = _SHOT.get(str(item.get("result", "")))
        coords = item.get("coords")
        if shooter is None or result is None or not isinstance(coords, dict):
            continue
        shots.append(
            ShotView(
                seq=int(item.get("seq", len(shots) + 1)),
                shooter=shooter,
                column=int(coords["column"]),
                row=int(coords["row"]),
                result=result,
            )
        )
    return shots


def _coords(cell: dict[str, object]) -> tuple[int, int]:
    coords = cell.get("coords")
    if not isinstance(coords, dict):
        raise TypeError("cell.coords required")
    column = int(coords["column"])
    row = int(coords["row"])
    if not (0 <= column <= 9 and 0 <= row <= 9):
        raise ValueError("cell out of range")
    return column, row


def _mark(raw: object) -> Mark:
    if isinstance(raw, str) and raw in _MARK:
        return _MARK[raw]
    return Mark.UNCHECKED
