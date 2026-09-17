"""API tests for UC-005: REST surrender reject and party WebSocket surrender."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from anyio import WouldBlock
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from backend.domain.placement import generate_placement_pair
from backend.domain.session import Shot, new_session
from backend.domain.types import (
    CellCoordinate,
    EndReason,
    OccupancyKind,
    SessionStatus,
    ShotResult,
    Side,
)
from tests.conftest import FakeLedgerStore, FakeSessionStore

# Player MISS + Backend chain + gameOver; board is 10×10. Not a wait-until-close loop.
_MAX_PARTY_FRAMES = 120


def _seed_session(store: FakeSessionStore, *, turn: Side = Side.PLAYER) -> str:
    pair = generate_placement_pair(deadline_monotonic=time.monotonic() + 2.0)
    session = new_session(
        "c" * 32,
        pair.player_board,
        pair.backend_board,
        pair.player_fleet,
        pair.backend_fleet,
        ttl_anchor=datetime.now(timezone.utc),
    )
    session.turn = turn
    store.by_id[session.id] = session
    return session.id


def _first_empty_coords(store: FakeSessionStore, session_id: str) -> tuple[int, int]:
    session = store.by_id[session_id]
    for cell in session.backend_board.cells:
        if cell.occupancy.kind is OccupancyKind.EMPTY:
            return cell.coords.column, cell.coords.row
    raise AssertionError("no empty cell")


def _receive_queued_json(ws: WebSocketTestSession) -> dict[str, Any] | None:
    """Take a frame already in the TestClient stream; do not block for disconnect."""
    try:
        message = ws.portal.call(ws._send_rx.receive_nowait)
    except WouldBlock:
        return None
    if message["type"] == "websocket.close":
        return None
    text = message.get("text")
    if not isinstance(text, str):
        return None
    payload = json.loads(text)
    if not isinstance(payload, dict):
        return None
    return payload


def _collect_until_game_over(ws: WebSocketTestSession) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for _ in range(_MAX_PARTY_FRAMES):
        frame = ws.receive_json()
        frames.append(frame)
        if frame["type"] != "gameOver":
            continue
        while True:
            extra = _receive_queued_json(ws)
            if extra is None:
                break
            frames.append(extra)
        return frames
    types = [frame.get("type") for frame in frames]
    raise AssertionError(f"no gameOver within {_MAX_PARTY_FRAMES} frames: {types}")


def test_should_return_400_surrender_wrong_channel_when_post_surrender(
    api_client: TestClient,
) -> None:
    """A0130 / A0157: REST surrender always refuses without mutating state."""
    response = api_client.post(
        f"/sessions/{'d' * 32}/surrender",
        json={"type": "surrender"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "SURRENDER_WRONG_CHANNEL"
    assert body["message"] == "Surrender must be sent on the party channel."
    assert body["messageRu"] == "Сдача принимается только по каналу партии."


def test_should_leave_session_unchanged_when_post_surrender(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-077 / A0001: REST does not reveal or mutate an existing session."""
    session_id = _seed_session(fake_store)
    response = api_client.post(
        f"/sessions/{session_id}/surrender",
        json={"type": "surrender"},
    )
    assert response.status_code == 400
    session = fake_store.by_id[session_id]
    assert session.status is SessionStatus.ACTIVE
    assert session.winner is None
    assert session.end_reason is None
    assert session.shots == []
    assert session.turn is Side.PLAYER
    assert fake_ledger.records == []
    assert session_id not in fake_store.released


def test_should_send_game_over_without_seq_when_ws_surrender_zero_shots(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """UC-005: WS `{type: surrender}` → gameOver Surrender; seq omitted if no shots."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "surrender"})
        over = ws.receive_json()
        assert over["type"] == "gameOver"
        assert over["winner"] == "Backend"
        assert over["endReason"] == "Surrender"
        assert "seq" not in over
    assert session_id not in fake_store.by_id
    assert len(fake_ledger.records) == 1
    assert fake_ledger.records[0].end_reason is EndReason.SURRENDER
    assert fake_ledger.records[0].shots == 0
    assert fake_ledger.counters["backendWins"] == 1


def test_should_include_seq_when_ws_surrender_after_shots(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """OpenAPI GameOverEvent: last shot seq is present when the party had shots."""
    session_id = _seed_session(fake_store)
    fake_store.by_id[session_id].shots = [
        Shot(
            seq=2,
            shooter=Side.PLAYER,
            coords=CellCoordinate(column=1, row=1),
            result=ShotResult.MISS,
        )
    ]
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "surrender"})
        over = ws.receive_json()
        assert over["type"] == "gameOver"
        assert over["seq"] == 2
        assert over["endReason"] == "Surrender"
    assert fake_ledger.records[0].shots == 1


def test_should_accept_ws_surrender_when_backend_turn(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """A0092: surrender while turn is Backend still ends with Backend win."""
    session_id = _seed_session(fake_store, turn=Side.BACKEND)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "surrender"})
        over = ws.receive_json()
        assert over["type"] == "gameOver"
        assert over["winner"] == "Backend"
        assert over["endReason"] == "Surrender"
    assert len(fake_ledger.records) == 1


def test_should_keep_session_when_ws_disconnects_without_surrender(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """A0092: disconnect is not surrender; no GAME_OVER, no Ledger row."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
    session = fake_store.by_id[session_id]
    assert session.status is SessionStatus.ACTIVE
    assert session.winner is None
    assert fake_ledger.records == []
    assert session_id not in fake_store.released


def test_should_send_one_game_over_when_shot_then_surrender(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-077 / UC-005 5.5: shot then surrender on the lock → one GAME_OVER, one Record."""
    session_id = _seed_session(fake_store)
    column, row = _first_empty_coords(fake_store, session_id)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "shot", "column": column, "row": row})
        ws.send_json({"type": "surrender"})
        frames = _collect_until_game_over(ws)
    overs = [frame for frame in frames if frame["type"] == "gameOver"]
    assert len(overs) == 1
    assert len(fake_ledger.records) == 1
    assert fake_ledger.counters["games"] == 1


def test_should_send_one_game_over_when_surrender_then_shot(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-077: surrender first cancels a queued shot; still one GAME_OVER Surrender."""
    session_id = _seed_session(fake_store)
    column, row = _first_empty_coords(fake_store, session_id)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        ws.send_json({"type": "surrender"})
        ws.send_json({"type": "shot", "column": column, "row": row})
        frames = _collect_until_game_over(ws)
    overs = [frame for frame in frames if frame["type"] == "gameOver"]
    assert len(overs) == 1
    assert overs[0]["winner"] == "Backend"
    assert overs[0]["endReason"] == "Surrender"
    assert len(fake_ledger.records) == 1
    assert fake_ledger.records[0].end_reason is EndReason.SURRENDER
    assert fake_ledger.counters["games"] == 1
