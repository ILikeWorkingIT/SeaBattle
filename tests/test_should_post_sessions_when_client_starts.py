"""Client POST /sessions (UC-001). urllib is mocked — no live HTTP."""

from __future__ import annotations

import json
from email.message import Message
from io import BytesIO
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from frontend.client.session_start import create_session, session_state_to_scene
from frontend.domain.types import FLEET_SPEC, Mark, ShipStatus, ShipType


def created_session_payload(*, leak_backend_deck: bool = False) -> dict[str, Any]:
    """Minimal OpenAPI SessionState shape for a successful create."""
    backend_cell: dict[str, Any] = {
        "coords": {"column": 0, "row": 0},
        "mark": "Unchecked",
    }
    if leak_backend_deck:
        backend_cell["occupancy"] = {"kind": "Deck", "ship": "hidden"}
    return {
        "sessionId": "a1b2c3d4e5f6789012345678abcdef01",
        "turn": "Player",
        "remainTtlSeconds": 1800,
        "playerBoard": {
            "cells": [
                {
                    "coords": {"column": 0, "row": 0},
                    "occupancy": {"kind": "Deck", "ship": "ship01"},
                    "mark": "Unchecked",
                }
            ]
        },
        "backendBoard": {"cells": [backend_cell]},
        "playerFleet": {
            "ships": [
                {
                    "type": "Battleship",
                    "status": "Intact",
                    "decks": [
                        {
                            "destroyed": False,
                            "coords": {"column": column, "row": 0},
                        }
                        for column in range(4)
                    ],
                }
            ]
        },
        "shots": [],
    }


class _FakeHttpResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._raw = body.encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeHttpResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_should_post_sessions_without_body_when_creating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-001 / OpenAPI createSession / A0155: POST /sessions, empty body."""
    captured: dict[str, object] = {}

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["data"] = request.data
        captured["timeout"] = timeout
        captured["accept"] = request.get_header("Accept")
        return _FakeHttpResponse(201, json.dumps(created_session_payload()))

    monkeypatch.setattr(
        "frontend.client.session_start.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = create_session(base_url="http://api.test:8000", timeout=7.0)
    assert captured["url"] == "http://api.test:8000/sessions"
    assert captured["method"] == "POST"
    assert captured["data"] is None
    assert captured["timeout"] == 7.0
    assert captured["accept"] == "application/json"
    assert outcome.kind == "success"


def test_should_return_success_when_http_201(monkeypatch: pytest.MonkeyPatch) -> None:
    """UC-001 / FT-001 / FT-014 / FT-016 / A0156: 201 maps to a playable scene."""
    payload = created_session_payload()

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        return _FakeHttpResponse(201, json.dumps(payload))

    monkeypatch.setattr(
        "frontend.client.session_start.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = create_session(base_url="http://api.test")
    assert outcome.kind == "success"
    assert outcome.http_status == 201
    assert outcome.scene is not None
    assert outcome.scene.session_id == payload["sessionId"]
    assert outcome.scene.player_turn is True


def test_should_return_limit_error_when_http_409(monkeypatch: pytest.MonkeyPatch) -> None:
    """FT-049 / A0156 / A0157: 409 SESSION_LIMIT_REACHED, no scene."""
    body = json.dumps(
        {
            "code": "SESSION_LIMIT_REACHED",
            "message": "No free session slot.",
            "messageRu": "Нет свободного слота сессии.",
        }
    ).encode("utf-8")

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        raise HTTPError(
            "http://api.test/sessions",
            409,
            "Conflict",
            Message(),
            BytesIO(body),
        )

    monkeypatch.setattr(
        "frontend.client.session_start.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = create_session(base_url="http://api.test")
    assert outcome.kind == "http"
    assert outcome.http_status == 409
    assert outcome.code == "SESSION_LIMIT_REACHED"
    assert outcome.scene is None
    assert outcome.text_for(True) == "Нет свободного слота сессии."
    assert outcome.text_for(False) == "No free session slot."


def test_should_return_timeout_when_network_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-001 5.2 / A0123: client timeout is distinct from HTTP refusal."""

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        raise TimeoutError()

    monkeypatch.setattr(
        "frontend.client.session_start.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = create_session(base_url="http://api.test", timeout=1.0)
    assert outcome.kind == "timeout"
    assert outcome.scene is None
    assert outcome.text_for(True) == "Сервер не ответил."
    assert outcome.text_for(False) == "The server did not respond."


def test_should_mark_player_decks_when_mapping_session() -> None:
    """FT-006 / FT-014: player occupancy Deck is visible on the own board."""
    scene = session_state_to_scene(created_session_payload())
    assert len(scene.player_cells) == 10
    assert all(len(row) == 10 for row in scene.player_cells)
    assert scene.player_cells[0][0].has_ship is True
    assert scene.player_cells[0][0].mark is Mark.UNCHECKED
    assert len(scene.player_ships) == 1
    assert scene.player_ships[0].type is ShipType.BATTLESHIP


def test_should_hide_enemy_occupancy_when_mapping_backend_board() -> None:
    """FT-015: Computer board never shows enemy decks, even if occupancy leaked."""
    scene = session_state_to_scene(created_session_payload(leak_backend_deck=True))
    assert [ship.type for ship in scene.backend_ships] == list(FLEET_SPEC)
    assert all(ship.status is ShipStatus.INTACT for ship in scene.backend_ships)
    assert all(ship.hide_intact_bars is True for ship in scene.backend_ships)
    assert not any(cell.has_ship for row in scene.backend_cells for cell in row)
