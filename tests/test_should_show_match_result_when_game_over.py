"""Battle UI for gameOver (UC-004 шаг 5). No QApplication.exec."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frontend.client.worker import GetStatisticsWorker
from frontend.domain.types import EndReason, Language, Mark
from frontend.i18n import I18n
from frontend.mock.static_scene import GameOverView
from frontend.ui.dialogs import GameOverDialog
from frontend.ui.main_window import MainWindow
from tests.test_should_show_shot_result_when_computer_board_clicked import (
    _connect_channel,
    _enter_battle,
    _shown_on,
    _shot_resolved,
    _window as _battle_window,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _game_over(
    *,
    winner: str = "Player",
    end_reason: str = "FleetLost",
    seq: int = 1,
) -> dict[str, object]:
    return {
        "type": "gameOver",
        "winner": winner,
        "endReason": end_reason,
        "seq": seq,
    }


def _patch_result_timer(monkeypatch: pytest.MonkeyPatch, *, fire: bool) -> None:
    def immediate(_msec: int, slot: object) -> None:
        if fire and callable(slot):
            slot()

    monkeypatch.setattr("frontend.ui.main_window.QTimer.singleShot", immediate)


def _window(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    *,
    shots: list[tuple[int, int]] | None = None,
    starts: list[int] | None = None,
    fire_result: bool = True,
) -> MainWindow:
    window = _battle_window(qapp, monkeypatch, shots=shots)
    if starts is not None:

        def fake_stats_start(self: GetStatisticsWorker) -> None:
            starts.append(1)

        monkeypatch.setattr(
            "frontend.ui.main_window.GetStatisticsWorker.start",
            fake_stats_start,
        )
    monkeypatch.setattr(window.stats_dialog, "exec", lambda: 0)
    _patch_result_timer(monkeypatch, fire=fire_result)
    return window


def test_should_fill_surrender_reason_when_dialog_presents(qapp: QApplication) -> None:
    """UC-005 шаг 6 / FT-077: game-over-reason is Surrender, not FleetLost."""
    del qapp
    dialog = GameOverDialog()
    i18n = I18n(Language.RU)
    dialog.present(
        i18n,
        GameOverView(player_won=False, end_reason=EndReason.SURRENDER, shot_count=0),
    )
    assert dialog.reason_label.objectName() == "game-over-reason"
    assert dialog.reason_label.text() == i18n.t("reason_surrender")
    assert dialog.winner_label.text() == i18n.t("you_lost")
    assert dialog.shots_label.text() == i18n.t("shots_count", n=0)
    assert dialog.reason_label.text() != i18n.t("reason_fleet")


def test_should_fill_result_labels_when_dialog_presents(qapp: QApplication) -> None:
    """A0118: game-over-dialog shows winner, FleetLost reason, and shot count."""
    del qapp
    dialog = GameOverDialog()
    i18n = I18n(Language.RU)
    dialog.present(
        i18n,
        GameOverView(player_won=True, end_reason=EndReason.FLEET_LOST, shot_count=12),
    )
    assert dialog.objectName() == "game-over-dialog"
    assert dialog.winner_label.accessibleName() == "game-over-winner"
    assert dialog.reason_label.objectName() == "game-over-reason"
    assert dialog.shots_label.objectName() == "game-over-shots"
    assert dialog.winner_label.text() == i18n.t("you_won")
    assert dialog.reason_label.text() == i18n.t("reason_fleet")
    assert dialog.shots_label.text() == i18n.t("shots_count", n=12)
    assert dialog.new_button.accessibleName() == "game-over-new-match"
    assert dialog.stats_button.accessibleName() == "game-over-open-stats"
    assert dialog.close_button.accessibleName() == "game-over-close"
    assert dialog.new_button.text() == i18n.t("new_game")
    assert dialog.stats_button.text() == i18n.t("open_stats")
    assert dialog.close_button.text() == i18n.t("close")


def test_should_show_result_dialog_when_game_over_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-004 шаг 5 / A0118: gameOver presents the result dialog (exec patched)."""
    presented: list[GameOverView] = []
    window = _window(qapp, monkeypatch)
    original = window.game_over_dialog.present

    def capture(i18n: object, view: GameOverView) -> None:
        presented.append(view)
        original(i18n, view)

    monkeypatch.setattr(window.game_over_dialog, "present", capture)
    monkeypatch.setattr(window.game_over_dialog, "exec", lambda: 0)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(_shot_resolved(seq=1, column=0, row=0, result="SUNK", turn="Player"))
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert presented == [
        GameOverView(player_won=True, end_reason=EndReason.FLEET_LOST, shot_count=1)
    ]
    assert window.game_over_dialog.objectName() == "game-over-dialog"
    assert window.game_over_dialog.winner_label.text() == window.i18n.t("you_won")
    assert window.stack.currentWidget() is window.lobby


def test_should_keep_sunk_on_board_when_game_over_follows(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0005: last deck stays SUNK after the separate gameOver frame."""
    window = _window(qapp, monkeypatch, fire_result=False)
    monkeypatch.setattr(window.game_over_dialog, "exec", lambda: 0)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(_shot_resolved(seq=1, column=4, row=5, result="SUNK", turn="Player"))
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert window.battle.backend_board.objectName() == "computer-board"
    assert window.battle.backend_board._cells[5][4].mark is Mark.SUNK
    assert window._live_scene is not None
    assert window._live_scene.match_over is True


def test_should_not_send_shot_when_match_already_over(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-047 / A0118: after gameOver the Computer board does not send a shot."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots, fire_result=False)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert window._live_scene is not None
    assert window._live_scene.match_over is True
    assert window._live_scene.player_turn is False
    window.battle.backend_board.cell_clicked.emit(3, 5)
    assert shots == []
    assert not window.battle._surrender_btn.isEnabled()
    assert not _shown_on(window.battle.computer_turn, window.battle)


def test_should_show_lobby_when_game_over_closed(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0118: close on the result dialog returns to the lobby, not a stored snapshot."""
    window = _window(qapp, monkeypatch)

    def close_exec() -> int:
        window.game_over_dialog.close_button.click()
        return 0

    monkeypatch.setattr(window.game_over_dialog, "exec", close_exec)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(_game_over(winner="Backend", seq=4))
    assert window.game_over_dialog.next_action is None
    assert window.stack.currentWidget() is window.lobby
    assert window._on_battle is False
    assert window._live_scene is None


def test_should_start_new_match_when_game_over_new_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0118: game-over-new-match starts POST /sessions after the result screen."""
    create_starts: list[int] = []
    window = _window(qapp, monkeypatch)

    def new_exec() -> int:
        window.game_over_dialog.new_button.click()
        return 0

    monkeypatch.setattr(window.game_over_dialog, "exec", new_exec)
    _enter_battle(window)
    _connect_channel(window)

    def fake_create_start(self: object) -> None:
        create_starts.append(1)

    monkeypatch.setattr(
        "frontend.ui.main_window.CreateSessionWorker.start",
        fake_create_start,
    )
    window._on_party_frame(_game_over(winner="Player", seq=2))
    assert window.game_over_dialog.next_action == "new"
    assert create_starts == [1]
    assert window.stack.currentWidget() is window.lobby


def test_should_open_stats_when_game_over_stats_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0118: game-over-open-stats opens the statistics dialog (exec patched)."""
    stats_execs: list[int] = []
    window = _window(qapp, monkeypatch)
    monkeypatch.setattr(window.stats_dialog, "exec", lambda: stats_execs.append(1) or 0)

    def stats_game_over_exec() -> int:
        window.game_over_dialog.stats_button.click()
        return 0

    monkeypatch.setattr(window.game_over_dialog, "exec", stats_game_over_exec)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert window.game_over_dialog.next_action == "stats"
    assert stats_execs == [1]
    assert window.stack.currentWidget() is window.lobby


def test_should_request_statistics_when_game_over_returns_to_lobby(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0135: after own GAME_OVER the lobby refresh calls GET /statistics."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    monkeypatch.setattr(window, "isVisible", lambda: True)
    monkeypatch.setattr(window.game_over_dialog, "exec", lambda: 0)
    _enter_battle(window)
    _connect_channel(window)
    starts.clear()
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert starts == [1]
    assert window._stats_phase == "loading"
    assert window.stack.currentWidget() is window.lobby


def test_should_ignore_second_game_over_when_result_already_shown(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One result dialog per match: a duplicate gameOver does not present again."""
    presents: list[int] = []
    window = _window(qapp, monkeypatch, fire_result=False)
    monkeypatch.setattr(window.game_over_dialog, "exec", lambda: 0)

    def count_present(*_args: object, **_kwargs: object) -> None:
        presents.append(1)

    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert window._result_shown is True
    monkeypatch.setattr(window.game_over_dialog, "present", count_present)
    window._on_party_frame(_game_over(winner="Player", seq=1))
    assert presents == []
