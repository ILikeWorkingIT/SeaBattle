"""Party WS client (UC-002). No live socket; send_shot is a JSON command."""

from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frontend.client.config import party_ws_url
from frontend.client.party_channel import PartyChannelWorker
from frontend.client.party_frames import apply_shot_resolved
from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import Mark, ShotResult, Side
from tests.test_should_post_sessions_when_client_starts import created_session_payload


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _scene():
    return session_state_to_scene(created_session_payload())


def _resolved(
    *,
    seq: int,
    column: int,
    row: int,
    result: str,
    turn: str,
    affected: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    cells = affected or [
        {"coords": {"column": column, "row": row}, "mark": result},
    ]
    return {
        "type": "shotResolved",
        "seq": seq,
        "shooter": "Player",
        "coords": {"column": column, "row": row},
        "result": result,
        "affectedCells": cells,
        "turn": turn,
        "remainTtlSeconds": 1800,
    }


def test_should_build_party_ws_url_when_http_base() -> None:
    """FT-055 / OpenAPI party WS: shot path is /sessions/{id}/ws, not REST /shots."""
    session_id = "a1b2c3d4e5f6789012345678abcdef01"
    url = party_ws_url(session_id, "http://localhost:8000")
    assert url == f"ws://localhost:8000/sessions/{session_id}/ws"
    assert "/shots" not in url


def test_should_use_wss_when_https_base() -> None:
    """FT-055: https API origin maps to wss party channel."""
    session_id = "a1b2c3d4e5f6789012345678abcdef01"
    url = party_ws_url(session_id, "https://example.test:8443")
    assert url == f"wss://example.test:8443/sessions/{session_id}/ws"


def test_should_emit_shot_json_when_send_shot(qapp: QApplication) -> None:
    """UC-002 / FT-017 / FT-055: command type is shot with integer coords."""
    del qapp
    captured: list[str] = []
    worker = PartyChannelWorker("a1b2c3d4e5f6789012345678abcdef01")
    worker._send_text.connect(captured.append)
    worker.send_shot(4, 7)
    assert json.loads(captured[0]) == {"type": "shot", "column": 4, "row": 7}


def test_should_mark_miss_and_pass_turn_when_shot_resolved() -> None:
    """FT-018 / FT-017: MISS paints Computer board and turn leaves Player."""
    scene = _scene()
    payload = _resolved(seq=1, column=9, row=9, result="MISS", turn="Backend")
    assert apply_shot_resolved(scene, payload) is True
    cell = scene.backend_cells[9][9]
    assert cell.mark is Mark.MISS
    assert cell.last_shot is True
    assert scene.player_turn is False
    assert scene.shots[-1].result is ShotResult.MISS
    assert scene.shots[-1].shooter is Side.PLAYER


def test_should_mark_hit_and_keep_turn_when_shot_resolved() -> None:
    """FT-019 / FT-023: HIT on Computer board keeps Player turn."""
    scene = _scene()
    payload = _resolved(seq=1, column=2, row=3, result="HIT", turn="Player")
    assert apply_shot_resolved(scene, payload) is True
    cell = scene.backend_cells[3][2]
    assert cell.mark is Mark.HIT
    assert cell.has_ship is True
    assert scene.player_turn is True


def test_should_mark_sunk_and_perimeter_when_shot_resolved() -> None:
    """FT-020 / FT-021 / FT-024: SUNK decks plus perimeter MISS; turn stays Player."""
    scene = _scene()
    payload = _resolved(
        seq=1,
        column=0,
        row=2,
        result="SUNK",
        turn="Player",
        affected=[
            {"coords": {"column": 0, "row": 2}, "mark": "SUNK"},
            {"coords": {"column": 0, "row": 1}, "mark": "MISS"},
            {"coords": {"column": 1, "row": 2}, "mark": "MISS"},
        ],
    )
    assert apply_shot_resolved(scene, payload) is True
    assert scene.backend_cells[2][0].mark is Mark.SUNK
    assert scene.backend_cells[1][0].mark is Mark.MISS
    assert scene.backend_cells[2][1].mark is Mark.MISS
    assert scene.player_turn is True


def test_should_ignore_frame_when_seq_stale() -> None:
    """A0124 / OpenAPI seq: stale shotResolved does not mutate the scene."""
    scene = _scene()
    first = _resolved(seq=2, column=1, row=1, result="MISS", turn="Backend")
    assert apply_shot_resolved(scene, first) is True
    again = _resolved(seq=2, column=5, row=5, result="HIT", turn="Player")
    assert apply_shot_resolved(scene, again) is False
    assert scene.backend_cells[5][5].mark is Mark.UNCHECKED
    assert scene.backend_cells[1][1].mark is Mark.MISS
