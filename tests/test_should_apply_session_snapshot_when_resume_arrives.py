"""Client mapping of sessionSnapshot on resume (UC-006). No GUI, no live WS."""

from __future__ import annotations

import pytest

from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import Mark, ShotResult, Side
from tests.test_should_post_sessions_when_client_starts import created_session_payload


def resume_session_payload() -> dict[str, object]:
    payload = created_session_payload()
    payload["turn"] = "Backend"
    payload["remainTtlSeconds"] = 65
    payload["shots"] = [
        {
            "seq": 1,
            "shooter": "Player",
            "coords": {"column": 0, "row": 0},
            "result": "MISS",
        }
    ]
    payload["backendBoard"] = {
        "cells": [{"coords": {"column": 0, "row": 0}, "mark": "MISS"}]
    }
    return payload


def test_should_map_shots_turn_and_ttl_when_resume_snapshot_complete() -> None:
    """UC-006 / FT-054 / FT-080: resume snapshot maps boards, shots, turn, remain TTL."""
    scene = session_state_to_scene(resume_session_payload())
    assert scene.session_id == created_session_payload()["sessionId"]
    assert scene.player_turn is False
    assert scene.ttl_seconds == 65
    assert scene.match_over is False
    assert len(scene.shots) == 1
    shot = scene.shots[0]
    assert shot.seq == 1
    assert shot.shooter is Side.PLAYER
    assert shot.column == 0
    assert shot.row == 0
    assert shot.result is ShotResult.MISS
    assert scene.last_shot_seq == 1
    assert scene.backend_cells[0][0].mark is Mark.MISS
    assert scene.backend_cells[0][0].has_ship is False


def test_should_raise_when_resume_snapshot_omits_ttl() -> None:
    """UC-006: remainTtlSeconds is required on SessionState / sessionSnapshot.session."""
    payload = resume_session_payload()
    del payload["remainTtlSeconds"]
    with pytest.raises(KeyError):
        session_state_to_scene(payload)


def test_should_raise_when_resume_snapshot_turn_invalid() -> None:
    """UC-006: turn must be Player or Backend."""
    payload = resume_session_payload()
    payload["turn"] = "Spectator"
    with pytest.raises(ValueError):
        session_state_to_scene(payload)


def test_should_raise_when_resume_snapshot_shots_not_list() -> None:
    """UC-006: shots history must be an array."""
    payload = resume_session_payload()
    payload["shots"] = {}
    with pytest.raises(TypeError):
        session_state_to_scene(payload)
