"""API tests for UC-006: resume party channel, replace stale WS, idle TTL frame."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect, WebSocketState

from backend.domain.placement import generate_placement_pair
from backend.domain.session import Cell, Shot, new_session
from backend.domain.types import Mark, OccupancyKind, ShotResult, Side
from tests.conftest import FakeLedgerStore, FakeSessionStore


def _seed_session(store: FakeSessionStore) -> str:
    pair = generate_placement_pair(deadline_monotonic=time.monotonic() + 2.0)
    session = new_session(
        "a1" + "b" * 30,
        pair.player_board,
        pair.backend_board,
        pair.player_fleet,
        pair.backend_fleet,
        ttl_anchor=datetime.now(timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def _seed_session_with_shot_history(store: FakeSessionStore) -> str:
    session_id = _seed_session(store)
    session = store.by_id[session_id]
    empty = next(
        cell
        for cell in session.backend_board.cells
        if cell.occupancy.kind is OccupancyKind.EMPTY
    )
    index = empty.coords.row * session.backend_board.size + empty.coords.column
    session.backend_board.cells[index] = Cell(
        coords=empty.coords, occupancy=empty.occupancy, mark=Mark.MISS
    )
    session.shots.append(
        Shot(
            seq=1,
            shooter=Side.PLAYER,
            coords=empty.coords,
            result=ShotResult.MISS,
        )
    )
    session.turn = Side.BACKEND
    return session_id


class _StaleSocket:
    client_state = WebSocketState.DISCONNECTED


def test_should_send_snapshot_when_ws_reconnects_after_drop(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-054 / FT-002: resume of the same launch returns an equivalent snapshot."""
    session_id = _seed_session(fake_store)
    session = fake_store.by_id[session_id]
    anchor = session.ttl_anchor

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as first:
        snap = first.receive_json()
        assert snap["type"] == "sessionSnapshot"
        assert snap["session"]["sessionId"] == session_id
        assert "backendFleet" not in snap["session"]
        assert "heatmap" not in snap["session"]
        assert "remainTtlSeconds" in snap["session"]

    assert session_id in fake_store.by_id
    assert fake_store.by_id[session_id].connected is False
    assert fake_store.by_id[session_id].ttl_anchor == anchor

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as second:
        resume = second.receive_json()
        assert resume["type"] == "sessionSnapshot"
        assert resume["session"]["sessionId"] == session_id
        assert resume["session"]["ttlAnchor"] == snap["session"]["ttlAnchor"]
        assert resume["session"]["turn"] == snap["session"]["turn"]
        assert "backendFleet" not in resume["session"]
        assert "heatmap" not in resume["session"]

    assert fake_store.by_id[session_id].ttl_anchor == anchor


def test_should_keep_slot_when_ws_disconnects(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-074 / A0008: drop is not surrender; the session stays in the limit."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
    assert session_id in fake_store.by_id
    assert session_id not in fake_store.released


def test_should_replace_ws_when_previous_socket_is_stale(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """A0133: half-open socket is resume, not FT-068."""
    session_id = _seed_session(fake_store)
    hub = api_client.app.state.party_hub
    hub.attach(session_id, _StaleSocket())
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        snap = ws.receive_json()
        assert snap["type"] == "sessionSnapshot"
        assert snap["session"]["sessionId"] == session_id
    assert hub.get(session_id) is None


def test_should_reject_second_ws_when_party_already_connected(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-068: a live second frontend is refused before accept."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as first:
        assert first.receive_json()["type"] == "sessionSnapshot"
        with pytest.raises(WebSocketDisconnect):
            with api_client.websocket_connect(f"/sessions/{session_id}/ws") as second:
                second.receive_json()
        first.send_json({"type": "shot", "column": "bad", "row": 0})
        error = first.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "SHOT_INVALID_PAYLOAD"


def test_should_send_ttl_expired_when_idle_elapses_while_connected(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-066 / FT-053: connected idle expiry is ttlExpired, not GAME_OVER."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        fake_store.by_id[session_id].ttl_anchor = datetime.now(timezone.utc) - timedelta(
            seconds=1801
        )
        frame = ws.receive_json()
        assert frame == {"type": "ttlExpired"}
    assert session_id not in fake_store.by_id
    assert fake_ledger.records == []
    assert fake_ledger.counters["games"] == 0


def test_should_send_equivalent_snapshot_when_ws_resumes_with_shots(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """FT-002 / FT-054: resume snapshot includes boards, shot history and turn."""
    session_id = _seed_session_with_shot_history(fake_store)
    stored = fake_store.by_id[session_id]
    missed = stored.shots[0]
    missed_code = missed.coords.code
    anchor = stored.ttl_anchor

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as first:
        snap = first.receive_json()
        assert snap["type"] == "sessionSnapshot"
        session = snap["session"]
        assert session["turn"] == "Backend"
        assert session["status"] == "Active"
        assert session["shots"] == [
            {
                "seq": 1,
                "shooter": "Player",
                "coords": {
                    "column": missed.coords.column,
                    "row": missed.coords.row,
                    "code": missed_code,
                },
                "result": "MISS",
            }
        ]
        backend_cell = next(
            cell
            for cell in session["backendBoard"]["cells"]
            if cell["coords"]["code"] == missed_code
        )
        assert backend_cell["mark"] == "MISS"
        assert "occupancy" not in backend_cell
        assert "backendFleet" not in session

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as second:
        resume = second.receive_json()
        assert resume["type"] == "sessionSnapshot"
        assert resume["session"]["shots"] == snap["session"]["shots"]
        assert resume["session"]["turn"] == snap["session"]["turn"]
        assert resume["session"]["ttlAnchor"] == snap["session"]["ttlAnchor"]
        resume_cell = next(
            cell
            for cell in resume["session"]["backendBoard"]["cells"]
            if cell["coords"]["code"] == missed_code
        )
        assert resume_cell["mark"] == "MISS"

    assert fake_store.by_id[session_id].ttl_anchor == anchor


def test_should_reject_ws_when_session_id_malformed(api_client: TestClient) -> None:
    """FT-067 / UC-006 5.1: unusable id format is the same refusal as unknown id."""
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{'g' + 'a' * 31}/ws") as ws:
            ws.receive_json()


def test_should_accept_resume_when_ttl_nearly_elapsed(
    api_client: TestClient, fake_store: FakeSessionStore
) -> None:
    """UC-006 5.6 / FT-005: resume seconds before idle expiry succeeds and does not extend TTL."""
    session_id = _seed_session(fake_store)
    session = fake_store.by_id[session_id]
    session.ttl_anchor = datetime.now(timezone.utc) - timedelta(seconds=1790)
    anchor = session.ttl_anchor

    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        snap = ws.receive_json()
        assert snap["type"] == "sessionSnapshot"
        remain = snap["session"]["remainTtlSeconds"]
        assert 1 <= remain <= 10

    assert fake_store.by_id[session_id].ttl_anchor == anchor


def test_should_reject_ws_when_reconnects_after_ttl_expired(
    api_client: TestClient,
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> None:
    """FT-067 / FT-066: after ttlExpired the id is unavailable; no GAME_OVER."""
    session_id = _seed_session(fake_store)
    with api_client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        assert ws.receive_json()["type"] == "sessionSnapshot"
        fake_store.by_id[session_id].ttl_anchor = datetime.now(timezone.utc) - timedelta(
            seconds=1801
        )
        assert ws.receive_json() == {"type": "ttlExpired"}
    with pytest.raises(WebSocketDisconnect):
        with api_client.websocket_connect(f"/sessions/{session_id}/ws") as again:
            again.receive_json()
    assert session_id not in fake_store.by_id
    assert fake_ledger.records == []
    assert fake_ledger.counters["games"] == 0
