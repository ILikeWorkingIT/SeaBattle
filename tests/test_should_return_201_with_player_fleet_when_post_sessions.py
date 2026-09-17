"""API tests for POST /sessions (UC-001, OpenAPI createSession)."""

from __future__ import annotations

import re

import pytest

from backend.domain.placement import PlacementTimeoutError
from tests.conftest import FakeSessionStore


def test_should_return_201_with_player_fleet_when_post_sessions(
    api_client,
    fake_store: FakeSessionStore,
) -> None:
    """UC-001 / FT-001 / FT-014 / FT-016 / A0156 / FT-080 / A0158: successful start."""
    response = api_client.post("/sessions")
    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(r"[0-9a-f]{32}", body["sessionId"])
    assert body["mode"] == "PvE"
    assert body["status"] == "Active"
    assert body["turn"] == "Player"
    assert body["idleTtlSeconds"] == 1800
    remain = body["remainTtlSeconds"]
    assert isinstance(remain, int)
    # OpenAPI: remain is leftover at response time, not the 1800 example.
    assert 1799 <= remain <= body["idleTtlSeconds"]
    assert len(body["playerFleet"]["ships"]) == 10
    assert body["playerBoard"]["owner"] == "Player"
    assert len(body["playerBoard"]["cells"]) == 100
    assert body["backendBoard"]["owner"] == "Backend"
    assert body["shots"] == []
    assert "backendFleet" not in body
    assert len(fake_store.saved) == 1


def test_should_hide_backend_occupancy_when_session_created(api_client) -> None:
    """FT-015 / NFT-009: backend board cells expose mark only."""
    body = api_client.post("/sessions").json()
    for cell in body["backendBoard"]["cells"]:
        assert set(cell.keys()) == {"coords", "mark"}
        assert "occupancy" not in cell
        assert cell["mark"] == "Unchecked"


def test_should_return_400_when_create_session_has_body(api_client) -> None:
    """UC-001 alt 5.1 / A0157: body not allowed on create."""
    response = api_client.post("/sessions", json={})
    assert response.status_code == 400
    error = response.json()
    assert error["code"] == "VALIDATION_ERROR"
    assert "message" in error and "messageRu" in error


def test_should_return_409_when_session_limit_reached(api_client, fake_store) -> None:
    """FT-049 / A0156: fourth concurrent session refused."""
    for _ in range(3):
        assert api_client.post("/sessions").status_code == 201
    response = api_client.post("/sessions")
    assert response.status_code == 409
    assert response.json()["code"] == "SESSION_LIMIT_REACHED"
    assert len(fake_store.saved) == 3


def test_should_return_503_when_placement_window_expires(
    api_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-010 / NFT-015 / A0156: start failed without occupying a slot."""

    def _boom(*, deadline_monotonic: float, rng=None):
        raise PlacementTimeoutError()

    monkeypatch.setattr(
        "backend.application.start_session.generate_placement_pair",
        _boom,
    )
    response = api_client.post("/sessions")
    assert response.status_code == 503
    assert response.json()["code"] == "SESSION_START_FAILED"


def test_should_return_500_when_persist_fails_after_generation(
    api_client,
    fake_store: FakeSessionStore,
) -> None:
    """UC-001 E1 / A0081: internal error; no slot kept."""
    fake_store.fail_persist = True
    response = api_client.post("/sessions")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert fake_store.saved == []
