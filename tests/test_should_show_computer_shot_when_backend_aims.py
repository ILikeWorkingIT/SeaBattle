"""Battle UI for Backend shotResolved (UC-003). No QApplication.exec."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QAbstractAnimation
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from frontend.domain.types import CellCoordinate, Language, Mark, display_coord
from tests.test_should_show_shot_result_when_computer_board_clicked import (
    _connect_channel,
    _enter_battle,
    _shown_on,
    _window,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _backend_shot(
    *,
    seq: int,
    column: int,
    row: int,
    result: str,
    turn: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "shotResolved",
        "seq": seq,
        "shooter": "Backend",
        "coords": {"column": column, "row": row},
        "result": result,
        "affectedCells": [{"coords": {"column": column, "row": row}, "mark": result}],
        "turn": turn,
        "remainTtlSeconds": 1800,
    }
    if extra:
        payload.update(extra)
    return payload


def _last_toast_text(window) -> str:
    card = window.toasts._cards[-1]
    label = card.findChild(QLabel)
    assert label is not None
    return label.text()


def _stop_aim_effects(window) -> None:
    window.battle._aim_anim.stop()
    window.battle.player_board._pulse_timer.stop()
    window.battle.backend_board._pulse_timer.stop()


def test_should_show_player_mark_when_backend_shot_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-003 шаг 7 / FT-036: Backend frame paints player-board; Computer cell stays empty."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(seq=1, column=5, row=6, result="MISS", turn="Player")
    )
    battle = window.battle
    assert battle.player_board.objectName() == "player-board"
    assert battle.player_board._cells[6][5].mark is Mark.MISS
    assert battle.backend_board._cells[6][5].mark is Mark.UNCHECKED
    assert window._shot_phase == "success"
    assert not _shown_on(battle.shot_error, battle)
    assert not _shown_on(battle.shot_loading, battle)
    assert not _shown_on(battle.shot_empty, battle)
    _stop_aim_effects(window)


def test_should_show_backend_toast_when_computer_aims(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-036: toast names Computer shot and cell, not Player miss/hit keys."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(seq=1, column=0, row=0, result="HIT", turn="Backend")
    )
    cell = display_coord(CellCoordinate(0, 0), Language.RU).text()
    expected = window.i18n.t("toast_backend_shot", result="HIT", cell=cell)
    assert _last_toast_text(window) == expected
    assert window.i18n.t("toast_hit") not in expected
    _stop_aim_effects(window)


def test_should_show_computer_turn_when_backend_keeps_turn(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0117 / UC-003 шаг 7: aiming badge pulses without QApplication.exec."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(seq=1, column=2, row=2, result="HIT", turn="Backend")
    )
    battle = window.battle
    assert battle.computer_turn.objectName() == "battle-computer-turn"
    assert _shown_on(battle.computer_turn, battle)
    assert battle.computer_turn.text() == window.i18n.t("aiming")
    assert battle._turn_badge.text() == window.i18n.t("turn_backend")
    assert battle._aim_anim.state() == QAbstractAnimation.State.Running
    assert window._live_scene is not None
    assert window._live_scene.player_turn is False
    _stop_aim_effects(window)


def test_should_hide_computer_turn_when_backend_misses(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-036: Backend MISS returns the turn; aiming badge hides; Player click still works."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(seq=1, column=8, row=8, result="MISS", turn="Player")
    )
    battle = window.battle
    assert window._live_scene is not None
    assert window._live_scene.player_turn is True
    assert not _shown_on(battle.computer_turn, battle)
    assert battle._turn_badge.text() == window.i18n.t("turn_player")
    battle.backend_board.cell_clicked.emit(1, 1)
    assert shots == [(1, 1)]
    _stop_aim_effects(window)


def test_should_pulse_player_board_when_backend_shot_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0117: last-shot pulse runs on player-board, not computer-board."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(seq=1, column=9, row=1, result="MISS", turn="Player")
    )
    assert window.battle.player_board._pulse_timer.isActive()
    assert not window.battle.backend_board._pulse_timer.isActive()
    assert window.battle.player_board._cells[1][9].last_shot is True
    _stop_aim_effects(window)


def test_should_not_send_shot_when_not_player_turn(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-036 / disabled: Computer board click is cut while turn is Backend."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(seq=1, column=3, row=4, result="HIT", turn="Backend")
    )
    window.battle.backend_board.cell_clicked.emit(7, 7)
    assert shots == []
    assert window._shot_phase == "success"
    assert _last_toast_text(window) == window.i18n.t("err_not_turn")
    _stop_aim_effects(window)


def test_should_omit_heatmap_when_backend_frame_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-050: leaked heatmap on the frame is not a widget and does not replace aiming copy."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _backend_shot(
            seq=1,
            column=1,
            row=2,
            result="HIT",
            turn="Backend",
            extra={"heatmap": [[1] * 10] * 10, "mode": "Target"},
        )
    )
    battle = window.battle
    assert battle.findChild(QWidget, "heatmap") is None
    assert not hasattr(window._live_scene, "heatmap")
    assert battle.computer_turn.text() == window.i18n.t("aiming")
    assert "Hunt" not in battle.computer_turn.text()
    assert "Target" not in battle.computer_turn.text()
    _stop_aim_effects(window)
