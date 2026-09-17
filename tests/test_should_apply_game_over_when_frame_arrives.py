"""Client apply of gameOver (UC-004). No GUI, no live WS."""

from __future__ import annotations

from frontend.client.party_frames import apply_game_over, apply_shot_resolved
from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import EndReason, Mark
from frontend.mock.static_scene import BattleScene
from tests.test_should_post_sessions_when_client_starts import created_session_payload


def _scene() -> BattleScene:
    return session_state_to_scene(created_session_payload())


def _game_over(
    *,
    winner: str = "Player",
    end_reason: str = "FleetLost",
    seq: int | None = 1,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "gameOver",
        "winner": winner,
        "endReason": end_reason,
    }
    if seq is not None:
        payload["seq"] = seq
    return payload


def _player_sunk(*, seq: int, column: int, row: int) -> dict[str, object]:
    return {
        "type": "shotResolved",
        "seq": seq,
        "shooter": "Player",
        "coords": {"column": column, "row": row},
        "result": "SUNK",
        "affectedCells": [{"coords": {"column": column, "row": row}, "mark": "SUNK"}],
        "turn": "Player",
        "remainTtlSeconds": 1800,
    }


def test_should_set_match_over_when_game_over_arrives() -> None:
    """UC-004 шаг 5 / A0118: gameOver sets match_over and stops the Player turn."""
    scene = _scene()
    assert scene.match_over is False
    assert apply_game_over(scene, _game_over(winner="Player", seq=7)) is True
    assert scene.match_over is True
    assert scene.player_turn is False
    assert scene.game_over.player_won is True
    assert scene.game_over.end_reason is EndReason.FLEET_LOST
    assert scene.game_over.shot_count == 7


def test_should_mark_computer_win_when_backend_is_winner() -> None:
    """UC-004: winner Backend is a Player loss on the result view."""
    scene = _scene()
    assert apply_game_over(scene, _game_over(winner="Backend", seq=3)) is True
    assert scene.game_over.player_won is False
    assert scene.match_over is True


def test_should_mark_surrender_when_game_over_arrives() -> None:
    """UC-005 / FT-077: gameOver endReason Surrender is a Computer win; seq may be omitted."""
    scene = _scene()
    payload = _game_over(winner="Backend", end_reason="Surrender", seq=None)
    assert apply_game_over(scene, payload) is True
    assert scene.game_over.end_reason is EndReason.SURRENDER
    assert scene.game_over.player_won is False
    assert scene.game_over.shot_count == 0
    assert scene.match_over is True
    assert scene.player_turn is False


def test_should_count_local_shots_when_seq_omitted() -> None:
    """OpenAPI GameOverEvent: seq omitted → shot_count from the local log."""
    scene = _scene()
    assert apply_shot_resolved(scene, _player_sunk(seq=1, column=0, row=0)) is True
    assert apply_game_over(scene, _game_over(seq=None)) is True
    assert scene.game_over.shot_count == 1


def test_should_reject_when_game_over_fields_invalid() -> None:
    """Malformed gameOver does not freeze the match."""
    scene = _scene()
    assert apply_game_over(scene, {"type": "gameOver", "winner": "?", "endReason": "FleetLost"}) is False
    assert scene.match_over is False
    assert scene.player_turn is True


def test_should_keep_sunk_marks_when_game_over_follows() -> None:
    """A0005: SUNK is a separate shotResolved; gameOver does not repaint cells."""
    scene = _scene()
    sunk = _player_sunk(seq=1, column=2, row=3)
    assert apply_shot_resolved(scene, sunk) is True
    cell = scene.backend_cells[3][2]
    assert cell.mark is Mark.SUNK
    assert apply_game_over(scene, _game_over(winner="Player", seq=1)) is True
    assert scene.backend_cells[3][2].mark is Mark.SUNK
    assert scene.backend_cells[3][2].last_shot is True
    assert scene.match_over is True
