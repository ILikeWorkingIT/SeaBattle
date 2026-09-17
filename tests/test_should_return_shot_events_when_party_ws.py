"""API tests for UC-002: REST shot reject and party WebSocket."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.domain.placement import generate_placement_pair
from backend.domain.session import (
    Board,
    Cell,
    Deck,
    Fleet,
    Occupancy,
    Ship,
    empty_board,
    new_session,
)
from backend.domain.types import (
    BOARD_SIZE,
    CellCoordinate,
    Facing,
    Mark,
    OccupancyKind,
    SessionStatus,
    ShipStatus,
    ShipType,
    Side,
)
from tests.conftest import FakeLedgerStore, FakeSessionStore


def _seed_session(store: FakeSessionStore) -> str:
    pair = generate_placement_pair(deadline_monotonic=time.monotonic() + 2.0)
    session = new_session(
        "c" * 32,
        pair.player_board,
        pair.backend_board,
        pair.player_fleet,
        pair.backend_fleet,
        ttl_anchor=datetime.now(timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def _first_empty_coords(store: FakeSessionStore, session_id: str) -> tuple[int, int]:
    session = store.by_id[session_id]
    for cell in session.backend_board.cells:
        if cell.occupancy.kind is OccupancyKind.EMPTY:
            return cell.coords.column, cell.coords.row
    raise AssertionError("no empty cell")


def _first_multi_deck_coords(store: FakeSessionStore, session_id: str) -> tuple[int, int]:
    session = store.by_id[session_id]
    ship = next(s for s in session.backend_fleet.ships if s.length >= 2)
    coords = ship.decks[0].coords
    return coords.column, coords.row


def _first_boat_coords(store: FakeSessionStore, session_id: str) -> tuple[int, int]:
    session = store.by_id[session_id]
    ship = next(s for s in session.backend_fleet.ships if s.length == 1)
    coords = ship.decks[0].coords
    return coords.column, coords.row


def test_should_return_400_shot_wrong_channel_when_post_shots(
    api_client: TestClient,
) -> None:
    """FT-055: REST shots always refuse without mutating state."""
    response = api_client.post(
        f"/sessions/{'d' * 32}/shots",
        json={"type": "shot", "column": 0, "row": 0},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "SHOT_WRONG_CHANNEL"


def test_should_send_snapshot_then_shot_resolved_when_ws_miss(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    session_id = _seed_session(fake_store)
    column, row = _first_empty_coords(fake_store, session_id)

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        snapshot = ws.receive_json()
        assert snapshot["type"] == "sessionSnapshot"
        assert snapshot["session"]["sessionId"] == session_id
        assert "backendFleet" not in snapshot["session"]
        assert "heatmap" not in snapshot["session"]

        ws.send_json({"type": "shot", "column": column, "row": row})
        player_shot = ws.receive_json()
        assert player_shot["type"] == "shotResolved"
        assert player_shot["result"] == "MISS"
        assert player_shot["shooter"] == "Player"
        assert player_shot["turn"] == "Backend"
        assert player_shot["seq"] == 1

        follow = ws.receive_json()
        assert follow["type"] in ("shotResolved", "sessionAborted", "gameOver")
        if follow["type"] == "shotResolved":
            assert follow["shooter"] == "Backend"
            assert follow["seq"] == 2
            assert "heatmap" not in follow
            assert "mode" not in follow
            assert "targetShip" not in follow
            assert follow["result"] in ("MISS", "HIT", "SUNK")

    session = fake_store.by_id.get(session_id)
    if session is not None:
        assert any(shot.shooter is Side.BACKEND for shot in session.shots)


def test_should_send_shot_resolved_when_ws_hit(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """UC-002 / FT-019 / FT-023: HIT keeps Player turn; OpenAPI shotResolved."""
    session_id = _seed_session(fake_store)
    column, row = _first_multi_deck_coords(fake_store, session_id)

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": column, "row": row})
        resolved = ws.receive_json()

    assert resolved["type"] == "shotResolved"
    assert resolved["result"] == "HIT"
    assert resolved["shooter"] == "Player"
    assert resolved["turn"] == "Player"
    assert resolved["seq"] == 1
    assert resolved["coords"]["column"] == column
    assert resolved["coords"]["row"] == row
    assert resolved["coords"]["code"] == f"{column}{row}"
    marks = {cell["mark"] for cell in resolved["affectedCells"]}
    assert marks == {"HIT"}
    session = fake_store.by_id[session_id]
    assert session.turn is Side.PLAYER
    assert session.shots[0].result.value == "HIT"


def test_should_send_shot_resolved_when_ws_sunk(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """UC-002 / FT-020 / FT-021 / FT-024: SUNK frame with perimeter MISS, not GAME_OVER."""
    session_id = _seed_session(fake_store)
    column, row = _first_boat_coords(fake_store, session_id)

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": column, "row": row})
        resolved = ws.receive_json()

    assert resolved["type"] == "shotResolved"
    assert resolved["result"] == "SUNK"
    assert resolved["turn"] == "Player"
    marks = [cell["mark"] for cell in resolved["affectedCells"]]
    assert "SUNK" in marks
    assert "MISS" in marks
    session = fake_store.by_id[session_id]
    assert session_id in fake_store.by_id
    assert session.turn is Side.PLAYER
    assert session.shots[0].result.value == "SUNK"


def test_should_send_error_when_ws_cell_already_checked(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-044: repeat shot on the same cell is refused on the party channel."""
    session_id = _seed_session(fake_store)
    column, row = _first_multi_deck_coords(fake_store, session_id)

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": column, "row": row})
        first = ws.receive_json()
        assert first["type"] == "shotResolved"
        assert first["result"] == "HIT"
        ws.send_json({"type": "shot", "column": column, "row": row})
        error = ws.receive_json()

    assert error["type"] == "error"
    assert error["code"] == "SHOT_CELL_CHECKED"
    assert len(fake_store.by_id[session_id].shots) == 1


def test_should_send_invalid_payload_error_when_shot_coords_wrong_type(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-070: non-integer column/row does not change state."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": "0", "row": 0})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "SHOT_INVALID_PAYLOAD"
    assert fake_store.by_id[session_id].shots == []


def test_should_send_error_when_shot_not_your_turn(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    session_id = _seed_session(fake_store)
    column, row = _first_empty_coords(fake_store, session_id)
    fake_store.by_id[session_id].turn = Side.BACKEND

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": column, "row": row})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "SHOT_NOT_YOUR_TURN"


def test_should_reject_ws_when_session_unknown(api_client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{'e' * 32}/ws") as ws:
            ws.receive_json()


def test_should_leave_session_unchanged_when_post_shots(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-055 / A0001: REST shot does not mutate even if the session exists."""
    session_id = _seed_session(fake_store)
    response = api_client.post(
        f"/sessions/{session_id}/shots",
        json={"type": "shot", "column": 0, "row": 0},
    )
    assert response.status_code == 400
    session = fake_store.by_id[session_id]
    assert session.shots == []
    assert session.turn is Side.PLAYER


def test_should_send_invalid_payload_error_when_shot_missing_coords(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-070: shot without integer column/row does not change state."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot"})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "SHOT_INVALID_PAYLOAD"
    assert fake_store.by_id[session_id].shots == []


def test_should_reject_second_ws_when_party_already_connected(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-068: a second live frontend on the same session is refused."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as first:
        assert first.receive_json()["type"] == "sessionSnapshot"
        with pytest.raises(WebSocketDisconnect):
            with api_client.websocket_connect(f"/sessions/{session_id}/ws") as second:
                second.receive_json()


def _seed_last_backend_ship(store: FakeSessionStore) -> str:
    coords = CellCoordinate(column=0, row=0)
    board = empty_board(Side.BACKEND)
    ship = Ship(
        id="b01",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords, destroyed=False)],
    )
    board.cells[coords.row * BOARD_SIZE + coords.column] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship.id),
        mark=Mark.UNCHECKED,
    )
    sunk = [
        Ship(
            id=f"b{i:02d}",
            type=ShipType.BOAT,
            length=1,
            facing=Facing.HORIZONTAL,
            status=ShipStatus.SUNK,
            decks=[
                Deck(
                    coords=CellCoordinate(column=i % 10, row=9),
                    destroyed=True,
                )
            ],
        )
        for i in range(2, 11)
    ]
    session = new_session(
        "f" * 32,
        empty_board(Side.PLAYER),
        board,
        Fleet(owner=Side.PLAYER, ships=[]),
        Fleet(owner=Side.BACKEND, ships=[ship, *sunk]),
        ttl_anchor=datetime.now(timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def test_should_send_game_over_and_delete_when_last_ship_sunk(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-071 / A0005: shotResolved then separate gameOver; session deleted."""
    session_id = _seed_last_backend_ship(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 0, "row": 0})
        resolved = ws.receive_json()
        assert resolved["type"] == "shotResolved"
        assert resolved["result"] == "SUNK"
        assert "winner" not in resolved
        assert "endReason" not in resolved
        sunk_marks = [
            cell["mark"]
            for cell in resolved["affectedCells"]
            if cell["coords"]["column"] == 0 and cell["coords"]["row"] == 0
        ]
        assert sunk_marks == ["SUNK"]
        over = ws.receive_json()
        assert over["type"] == "gameOver"
        assert over["winner"] == "Player"
        assert over["endReason"] == "FleetLost"
        assert over["seq"] == resolved["seq"]
    assert session_id not in fake_store.by_id
    assert len(fake_ledger.records) == 1
    assert fake_ledger.records[0].winner.value == "Player"
    assert fake_ledger.records[0].end_reason.value == "FleetLost"
    assert fake_ledger.counters["games"] == 1
    assert fake_ledger.counters["playerWins"] == 1


def _seed_empty_heatmap_session(store: FakeSessionStore) -> str:
    player_board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if (column + row) % 2 == 0:
                continue
            index = row * BOARD_SIZE + column
            old = player_board.cells[index]
            player_board.cells[index] = Cell(
                coords=old.coords, occupancy=old.occupancy, mark=Mark.MISS
            )
    destroyer = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0)),
            Deck(coords=CellCoordinate(column=0, row=1)),
        ],
    )
    backend_board = empty_board(Side.BACKEND)
    session = new_session(
        "ab" + "c" * 30,
        player_board,
        backend_board,
        Fleet(owner=Side.PLAYER, ships=[destroyer]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime.now(timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def test_should_send_session_aborted_when_heatmap_empty(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-076 then FT-075: SESSION_ABORTED RU/EN, slot gone, ledger unchanged."""
    session_id = _seed_empty_heatmap_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 1, "row": 0})
        player_shot = ws.receive_json()
        assert player_shot["type"] == "shotResolved"
        assert player_shot["shooter"] == "Player"
        aborted = ws.receive_json()
        assert aborted["type"] == "sessionAborted"
        assert aborted["code"] == "SESSION_ABORTED"
        assert aborted["messageRu"] == (
            "Партия прервана из-за ошибки сервера. Начните новую."
        )
        assert "new game" in aborted["message"].lower()
        assert "heatmap" not in aborted
    assert session_id not in fake_store.by_id
    assert fake_ledger.counters["games"] == 0
    assert fake_ledger.records == []


def _seed_forced_backend_cell(
    store: FakeSessionStore,
    *,
    session_id: str,
    player_cell: Cell,
    player_ships: list[Ship],
) -> str:
    player_board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if row == player_cell.coords.row and column == player_cell.coords.column:
                continue
            index = row * BOARD_SIZE + column
            old = player_board.cells[index]
            player_board.cells[index] = Cell(
                coords=old.coords, occupancy=old.occupancy, mark=Mark.MISS
            )
    index = player_cell.coords.row * BOARD_SIZE + player_cell.coords.column
    player_board.cells[index] = player_cell
    session = new_session(
        session_id,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=player_ships),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime.now(timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def _place_player_deck(
    board: Board, coords: CellCoordinate, ship_id: str
) -> None:
    index = coords.row * BOARD_SIZE + coords.column
    old = board.cells[index]
    board.cells[index] = Cell(
        coords=coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship_id),
        mark=old.mark,
    )


def _set_player_mark(board: Board, column: int, row: int, mark: Mark) -> None:
    index = row * BOARD_SIZE + column
    old = board.cells[index]
    board.cells[index] = Cell(
        coords=old.coords, occupancy=old.occupancy, mark=mark
    )


def test_should_send_backend_shot_when_battleship_hits_skip_decks(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-058 / FT-033 / UC-003 5.1: WS Target shot into UNCHECKED on axis; not abort, not silent Backend turn."""
    player_board = empty_board(Side.PLAYER)
    decks = (
        CellCoordinate(column=1, row=1),
        CellCoordinate(column=1, row=2),
        CellCoordinate(column=1, row=3),
        CellCoordinate(column=1, row=4),
    )
    battleship = Ship(
        id="p-bb-ws",
        type=ShipType.BATTLESHIP,
        length=4,
        facing=Facing.VERTICAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=decks[0], destroyed=True),
            Deck(coords=decks[1], destroyed=False),
            Deck(coords=decks[2], destroyed=True),
            Deck(coords=decks[3], destroyed=False),
        ],
    )
    for coords in decks:
        _place_player_deck(player_board, coords, battleship.id)
    _set_player_mark(player_board, 1, 1, Mark.HIT)
    _set_player_mark(player_board, 1, 3, Mark.HIT)
    _set_player_mark(player_board, 1, 0, Mark.MISS)
    _set_player_mark(player_board, 1, 5, Mark.MISS)
    session = new_session(
        "33" + "c" * 30,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[battleship]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime.now(timezone.utc),
    )
    fake_store.by_id[session.id] = session
    gaps = {(1, 2), (1, 4)}
    with api_client.websocket_connect(f"/sessions/{session.id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 9, "row": 9})
        player_shot = ws.receive_json()
        assert player_shot["type"] == "shotResolved"
        assert player_shot["shooter"] == "Player"
        assert player_shot["result"] == "MISS"
        assert player_shot["turn"] == "Backend"
        backend_shot = ws.receive_json()
        assert backend_shot["type"] == "shotResolved"
        assert backend_shot["shooter"] == "Backend"
        assert (
            backend_shot["coords"]["column"],
            backend_shot["coords"]["row"],
        ) in gaps
        assert backend_shot["result"] == "HIT"
        assert "heatmap" not in backend_shot


def test_should_send_backend_miss_when_player_misses(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-036 / FT-027 / FT-050: Backend shotResolved without heatmap fields."""
    hidden_boat = Ship(
        id="p-hidden",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=9, row=9))],
    )
    session_id = _seed_forced_backend_cell(
        fake_store,
        session_id="11" + "a" * 30,
        player_cell=Cell(
            coords=CellCoordinate(column=0, row=0),
            occupancy=Occupancy(kind=OccupancyKind.EMPTY),
        ),
        player_ships=[hidden_boat],
    )
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        snapshot = ws.receive_json()
        assert snapshot["type"] == "sessionSnapshot"
        assert "heatmap" not in snapshot["session"]
        ws.send_json({"type": "shot", "column": 5, "row": 5})
        player_shot = ws.receive_json()
        assert player_shot["type"] == "shotResolved"
        assert player_shot["shooter"] == "Player"
        assert player_shot["result"] == "MISS"
        backend_shot = ws.receive_json()
        assert backend_shot["type"] == "shotResolved"
        assert backend_shot["shooter"] == "Backend"
        assert backend_shot["result"] == "MISS"
        assert backend_shot["turn"] == "Player"
        assert backend_shot["seq"] == 2
        assert backend_shot["coords"]["column"] == 0
        assert backend_shot["coords"]["row"] == 0
        assert "heatmap" not in backend_shot
        assert "mode" not in backend_shot
        assert "targetShip" not in backend_shot


def test_should_send_game_over_when_backend_sinks_last_player_ship(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-036 / FT-025: Backend SUNK of last player ship → gameOver; ledger is UC-004."""
    coords = CellCoordinate(column=0, row=0)
    boat = Ship(
        id="p-last",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=coords)],
    )
    session_id = _seed_forced_backend_cell(
        fake_store,
        session_id="22" + "b" * 30,
        player_cell=Cell(
            coords=coords,
            occupancy=Occupancy(kind=OccupancyKind.DECK, ship=boat.id),
        ),
        player_ships=[boat],
    )
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 5, "row": 5})
        player_shot = ws.receive_json()
        assert player_shot["result"] == "MISS"
        backend_shot = ws.receive_json()
        assert backend_shot["type"] == "shotResolved"
        assert backend_shot["shooter"] == "Backend"
        assert backend_shot["result"] == "SUNK"
        assert "winner" not in backend_shot
        over = ws.receive_json()
        assert over["type"] == "gameOver"
        assert over["winner"] == "Backend"
        assert over["endReason"] == "FleetLost"
    assert session_id not in fake_store.by_id
    assert len(fake_ledger.records) == 1
    assert fake_ledger.records[0].winner.value == "Backend"
    assert fake_ledger.counters["backendWins"] == 1
    assert fake_ledger.counters["playerWins"] == 0


def test_should_reject_ws_when_session_aborted_already_deleted(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-067 / FT-075: after empty-heatmap abort the id is unavailable."""
    session_id = _seed_empty_heatmap_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 1, "row": 0})
        assert ws.receive_json()["type"] == "shotResolved"
        assert ws.receive_json()["type"] == "sessionAborted"
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{session_id}/ws") as again:
            again.receive_json()


def test_should_reject_ws_when_game_over_already_deleted(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """A0145 / FT-067: after GAME_OVER delivery reconnect is the same refusal as unknown id."""
    session_id = _seed_last_backend_ship(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 0, "row": 0})
        assert ws.receive_json()["type"] == "shotResolved"
        assert ws.receive_json()["type"] == "gameOver"
    assert len(fake_ledger.records) == 1
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{session_id}/ws") as again:
            again.receive_json()
    assert len(fake_ledger.records) == 1


def _seed_empty_heatmap_sunk_fleet(store: FakeSessionStore) -> str:
    player_board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if (column + row) % 2 == 0:
                continue
            index = row * BOARD_SIZE + column
            old = player_board.cells[index]
            player_board.cells[index] = Cell(
                coords=old.coords, occupancy=old.occupancy, mark=Mark.MISS
            )
    boat = Ship(
        id="p-sunk-hm",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.SUNK,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0), destroyed=True),
        ],
    )
    session = new_session(
        "de" + "f" * 30,
        player_board,
        empty_board(Side.BACKEND),
        Fleet(owner=Side.PLAYER, ships=[boat]),
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime.now(timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def test_should_send_game_over_when_heatmap_empty_and_fleet_sunk(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-052 / A0005: after Player MISS, empty heatmap + sunk fleet → gameOver, no Backend shot."""
    session_id = _seed_empty_heatmap_sunk_fleet(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": 1, "row": 0})
        player_shot = ws.receive_json()
        assert player_shot["type"] == "shotResolved"
        assert player_shot["shooter"] == "Player"
        assert player_shot["result"] == "MISS"
        over = ws.receive_json()
        assert over["type"] == "gameOver"
        assert over["winner"] == "Backend"
        assert over["endReason"] == "FleetLost"
        assert over["seq"] == player_shot["seq"]
    assert session_id not in fake_store.by_id
    assert len(fake_ledger.records) == 1
    assert fake_ledger.records[0].winner.value == "Backend"
    assert fake_ledger.counters["games"] == 1


def test_should_leave_ledger_when_idle_ttl_expired(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-053 / UC-004 E2: expired idle TTL refuses the channel and does not write statistics."""
    session_id = _seed_session(fake_store)
    session = fake_store.by_id[session_id]
    session.ttl_anchor = datetime.now(timezone.utc) - timedelta(seconds=1801)
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
            ws.receive_json()
    assert fake_ledger.records == []
    assert fake_ledger.counters["games"] == 0
    assert session_id in fake_store.by_id


def test_should_leave_ledger_when_game_over_session_reconnects(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """UC-004 5.1 / A0145: leftover GameOver handshake deletes JSON and does not append Ledger."""
    session_id = _seed_session(fake_store)
    session = fake_store.by_id[session_id]
    session.status = SessionStatus.GAME_OVER
    session.winner = Side.PLAYER
    session.end_reason = "FleetLost"
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
            ws.receive_json()
    assert session_id not in fake_store.by_id
    assert fake_ledger.records == []
    assert fake_ledger.counters["games"] == 0

