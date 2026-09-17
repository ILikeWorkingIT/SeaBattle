"""Client apply of Backend shotResolved (UC-003). No GUI, no live WS."""

from __future__ import annotations

from frontend.client.party_frames import apply_shot_resolved
from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import Mark, ShotResult, Side
from frontend.mock.static_scene import BattleScene
from tests.test_should_post_sessions_when_client_starts import created_session_payload


def _scene() -> BattleScene:
    return session_state_to_scene(created_session_payload())


def _backend_resolved(
    *,
    seq: int,
    column: int,
    row: int,
    result: str,
    turn: str,
    affected: list[dict[str, object]] | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    cells = affected or [
        {"coords": {"column": column, "row": row}, "mark": result},
    ]
    payload: dict[str, object] = {
        "type": "shotResolved",
        "seq": seq,
        "shooter": "Backend",
        "coords": {"column": column, "row": row},
        "result": result,
        "affectedCells": cells,
        "turn": turn,
        "remainTtlSeconds": 1800,
    }
    if extra:
        payload.update(extra)
    return payload


def test_should_mark_player_cell_when_backend_misses() -> None:
    """UC-003 шаг 7 / FT-036: Backend MISS paints the Player board, not Computer."""
    scene = _scene()
    payload = _backend_resolved(seq=1, column=4, row=7, result="MISS", turn="Player")
    assert apply_shot_resolved(scene, payload) is True
    cell = scene.player_cells[7][4]
    assert cell.mark is Mark.MISS
    assert cell.last_shot is True
    assert scene.backend_cells[7][4].mark is Mark.UNCHECKED
    assert scene.player_turn is True
    assert scene.shots[-1].shooter is Side.BACKEND
    assert scene.shots[-1].result is ShotResult.MISS


def test_should_keep_backend_turn_when_backend_hits() -> None:
    """UC-003 / FT-036: Backend HIT stays on Player board and keeps Computer turn."""
    scene = _scene()
    payload = _backend_resolved(seq=1, column=0, row=0, result="HIT", turn="Backend")
    assert apply_shot_resolved(scene, payload) is True
    cell = scene.player_cells[0][0]
    assert cell.mark is Mark.HIT
    assert cell.has_ship is True
    assert scene.player_turn is False
    assert scene.backend_cells[0][0].mark is Mark.UNCHECKED


def test_should_mark_sunk_on_player_board_when_backend_sinks() -> None:
    """FT-036 / FT-021: Backend SUNK plus perimeter MISS on the Player field."""
    scene = _scene()
    payload = _backend_resolved(
        seq=1,
        column=0,
        row=0,
        result="SUNK",
        turn="Backend",
        affected=[
            {"coords": {"column": 0, "row": 0}, "mark": "SUNK"},
            {"coords": {"column": 1, "row": 0}, "mark": "MISS"},
            {"coords": {"column": 0, "row": 1}, "mark": "MISS"},
        ],
    )
    assert apply_shot_resolved(scene, payload) is True
    assert scene.player_cells[0][0].mark is Mark.SUNK
    assert scene.player_cells[0][1].mark is Mark.MISS
    assert scene.player_cells[1][0].mark is Mark.MISS
    assert scene.backend_cells[0][0].mark is Mark.UNCHECKED
    assert scene.player_turn is False


def test_should_ignore_heatmap_when_backend_shot_resolved() -> None:
    """FT-050 / A0095: heatmap / Hunt-Target on the wire are not stored on the scene."""
    scene = _scene()
    payload = _backend_resolved(
        seq=1,
        column=3,
        row=3,
        result="MISS",
        turn="Player",
        extra={
            "heatmap": [[0.9] * 10] * 10,
            "mode": "Hunt",
            "weights": {"00": 12},
        },
    )
    assert apply_shot_resolved(scene, payload) is True
    assert not hasattr(scene, "heatmap")
    assert not hasattr(scene, "mode")
    assert scene.player_cells[3][3].mark is Mark.MISS
    assert "heatmap" not in scene.__slots__
