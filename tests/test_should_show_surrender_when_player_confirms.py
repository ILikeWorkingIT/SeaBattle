"""Battle UI / party client for UC-005 surrender. No QApplication.exec."""

from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from frontend.client.party_channel import PartyChannelWorker
from frontend.domain.types import EndReason, Language
from frontend.i18n import I18n
from frontend.mock.static_scene import GameOverView
from frontend.ui.dialogs import SurrenderDialog
from frontend.ui.main_window import MainWindow
from tests.test_should_show_match_result_when_game_over import (
    _game_over,
    _patch_result_timer,
)
from tests.test_should_show_shot_result_when_computer_board_clicked import (
    _connect_channel,
    _enter_battle,
    _shown_on,
    _window as _battle_window,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _window(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    *,
    surrenders: list[int] | None = None,
    shots: list[tuple[int, int]] | None = None,
    fire_result: bool = True,
) -> MainWindow:
    window = _battle_window(qapp, monkeypatch, shots=shots)
    if surrenders is not None:

        def fake_surrender(self: PartyChannelWorker) -> None:
            del self
            surrenders.append(1)

        monkeypatch.setattr(
            "frontend.ui.main_window.PartyChannelWorker.send_surrender",
            fake_surrender,
        )
    monkeypatch.setattr(window.game_over_dialog, "exec", lambda: 0)
    _patch_result_timer(monkeypatch, fire=fire_result)
    return window


def _confirm_yes(window: MainWindow) -> None:
    window.surrender_dialog._yes.click()


def _confirm_no(window: MainWindow) -> None:
    window.surrender_dialog._no.click()


def _open_surrender(window: MainWindow, monkeypatch: pytest.MonkeyPatch, *, accept: bool) -> None:
    def fake_exec() -> int:
        if accept:
            _confirm_yes(window)
        else:
            _confirm_no(window)
        return 0

    monkeypatch.setattr(window.surrender_dialog, "exec", fake_exec)
    window.battle._surrender_btn.click()


def test_should_emit_surrender_json_when_send_surrender(qapp: QApplication) -> None:
    """A0130 / FT-077: party command is {type: surrender}, not REST."""
    del qapp
    captured: list[str] = []
    worker = PartyChannelWorker("a1b2c3d4e5f6789012345678abcdef01")
    worker._send_text.connect(captured.append)
    worker.send_surrender()
    assert json.loads(captured[0]) == {"type": "surrender"}


def test_should_fill_confirm_labels_when_surrender_dialog_presents(qapp: QApplication) -> None:
    """A0119: surrender-dialog asks «Вы уверены?» before any WS command."""
    del qapp
    dialog = SurrenderDialog()
    i18n = I18n(Language.RU)
    dialog.retranslate(i18n)
    assert dialog.objectName() == "surrender-dialog"
    assert dialog._yes.accessibleName() == "surrender-confirm"
    assert dialog._no.accessibleName() == "surrender-cancel"
    assert dialog.windowTitle() == i18n.t("surrender_title")
    assert dialog._title.text() == i18n.t("surrender_title")
    assert dialog._body.text() == i18n.t("surrender_body")
    assert dialog._yes.text() == i18n.t("confirm")
    assert dialog._no.text() == i18n.t("cancel")


def test_should_open_confirm_dialog_when_surrender_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0119: battle-surrender opens the confirm dialog (exec patched)."""
    execs: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=[])
    monkeypatch.setattr(
        window.surrender_dialog,
        "exec",
        lambda: execs.append(1) or 0,
    )
    _enter_battle(window)
    _connect_channel(window)
    assert window.battle._surrender_btn.accessibleName() == "battle-surrender"
    assert window.battle._surrender_btn.isEnabled()
    window.battle._surrender_btn.click()
    assert execs == [1]
    assert window._surrender_phase == "idle"


def test_should_open_confirm_dialog_when_menu_surrender_triggered(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0119: menu-surrender uses the same confirm dialog, not a silent exit."""
    execs: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=[])
    monkeypatch.setattr(
        window.surrender_dialog,
        "exec",
        lambda: execs.append(1) or 0,
    )
    _enter_battle(window)
    _connect_channel(window)
    assert window._act_surrender.objectName() == "menu-surrender"
    assert window._act_surrender.isEnabled()
    window._act_surrender.trigger()
    assert execs == [1]
    assert window._surrender_phase == "idle"


def test_should_not_send_surrender_when_confirm_cancelled(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-005 5.3 / A0119: cancel does not send a surrender frame."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders)
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=False)
    assert surrenders == []
    assert window._surrender_phase == "idle"
    assert window._live_scene is not None
    assert window._live_scene.match_over is False
    assert not _shown_on(window.battle.surrender_loading, window.battle)
    assert not _shown_on(window.battle.surrender_error, window.battle)


def test_should_show_surrender_loading_when_confirm_accepted(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0131 / A0130: after confirm, UI waits for gameOver; no local outcome."""
    surrenders: list[int] = []
    presents: list[GameOverView] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders, fire_result=False)
    monkeypatch.setattr(
        window.game_over_dialog,
        "present",
        lambda *_args, **_kwargs: presents.append(GameOverView(False, EndReason.SURRENDER, 0)),
    )
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=True)
    battle = window.battle
    assert surrenders == [1]
    assert window._surrender_phase == "loading"
    assert battle.surrender_loading.objectName() == "battle-surrender-loading"
    assert _shown_on(battle.surrender_loading, battle)
    assert not _shown_on(battle.surrender_error, battle)
    assert battle.surrender_loading.text() == window.i18n.t("surrendering")
    assert not battle._surrender_btn.isEnabled()
    assert not window._act_surrender.isEnabled()
    assert window._live_scene is not None
    assert window._live_scene.match_over is False
    assert presents == []


def test_should_ignore_second_surrender_when_already_pending(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0131: while loading, a second confirm does not send another frame."""
    surrenders: list[int] = []
    execs: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders, fire_result=False)
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=True)
    assert surrenders == [1]
    monkeypatch.setattr(
        window.surrender_dialog,
        "exec",
        lambda: execs.append(1) or 0,
    )
    window.battle._surrender_btn.click()
    window._act_surrender.trigger()
    window._after_surrender()
    assert execs == []
    assert surrenders == [1]
    assert window._surrender_phase == "loading"


def test_should_show_surrender_error_when_channel_missing(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-005 5.2: confirm without an open party channel shows error, not GAME_OVER."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders)
    _enter_battle(window)
    _open_surrender(window, monkeypatch, accept=True)
    battle = window.battle
    assert surrenders == []
    assert window._surrender_phase == "error"
    assert battle.surrender_error.objectName() == "battle-surrender-error"
    assert _shown_on(battle.surrender_error, battle)
    assert not _shown_on(battle.surrender_loading, battle)
    assert battle.surrender_error.text() == window.i18n.t("err_surrender")
    assert window._live_scene is not None
    assert window._live_scene.match_over is False
    assert battle._surrender_btn.isEnabled()


def test_should_show_surrender_error_when_channel_drops(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-005 5.2: disconnect while pending is an error; it is not a local surrender."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders, fire_result=False)
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=True)
    window._on_party_frame({"type": "_disconnected"})
    battle = window.battle
    assert surrenders == [1]
    assert window._surrender_phase == "error"
    assert _shown_on(battle.surrender_error, battle)
    assert not _shown_on(battle.surrender_loading, battle)
    assert battle.surrender_error.text() == window.i18n.t("err_surrender")
    assert window._live_scene is not None
    assert window._live_scene.match_over is False


def test_should_show_surrender_error_when_ws_rejects(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-005 5.1 / A0137 / FT-059: VALIDATION_ERROR maps to i18n, not fixture messageRu."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders, fire_result=False)
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=True)
    window._on_party_frame(
        {
            "type": "error",
            "code": "VALIDATION_ERROR",
            "message": "bad payload",
            "messageRu": "неверная полезная нагрузка",
        }
    )
    battle = window.battle
    assert window._surrender_phase == "error"
    assert window.stack.currentWidget() is battle
    assert _shown_on(battle.surrender_error, battle)
    assert not _shown_on(battle.surrender_loading, battle)
    assert battle.surrender_error.text() == window.i18n.t("err_validation")
    assert window._live_scene is not None
    assert window._live_scene.match_over is False


def test_should_not_send_surrender_when_window_closes(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-005 E2 / FT-077: closing the window is not a surrender frame."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders)
    _enter_battle(window)
    _connect_channel(window)
    window.closeEvent(QCloseEvent())
    assert surrenders == []
    assert window._party is None
    assert window._live_scene is not None
    assert window._live_scene.match_over is False


def test_should_allow_surrender_when_computer_turn(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0092: surrender stays enabled while the Computer holds the turn."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders, fire_result=False)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        {
            "type": "shotResolved",
            "seq": 1,
            "shooter": "Backend",
            "coords": {"column": 0, "row": 0},
            "result": "HIT",
            "affectedCells": [{"coords": {"column": 0, "row": 0}, "mark": "HIT"}],
            "turn": "Backend",
            "remainTtlSeconds": 1800,
        }
    )
    assert window._live_scene is not None
    assert window._live_scene.player_turn is False
    assert window.battle._surrender_btn.isEnabled()
    _open_surrender(window, monkeypatch, accept=True)
    assert surrenders == [1]
    assert window._surrender_phase == "loading"


def test_should_not_send_shot_when_surrender_pending(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0131: Computer-board clicks are blocked while surrender is in flight."""
    surrenders: list[int] = []
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders, shots=shots, fire_result=False)
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=True)
    window.battle.backend_board.cell_clicked.emit(3, 5)
    assert shots == []
    assert surrenders == [1]
    assert window._surrender_phase == "loading"


def test_should_show_result_when_surrender_game_over_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-005 шаг 5–6: outcome is the server gameOver Surrender, after loading."""
    surrenders: list[int] = []
    presented: list[GameOverView] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders)
    original = window.game_over_dialog.present

    def capture(i18n: object, view: GameOverView) -> None:
        presented.append(view)
        original(i18n, view)

    monkeypatch.setattr(window.game_over_dialog, "present", capture)
    _enter_battle(window)
    _connect_channel(window)
    _open_surrender(window, monkeypatch, accept=True)
    assert window._surrender_phase == "loading"
    window._on_party_frame(_game_over(winner="Backend", end_reason="Surrender", seq=None))
    assert surrenders == [1]
    assert presented == [
        GameOverView(player_won=False, end_reason=EndReason.SURRENDER, shot_count=0)
    ]
    assert window.game_over_dialog.reason_label.objectName() == "game-over-reason"
    assert window.game_over_dialog.reason_label.text() == window.i18n.t("reason_surrender")
    assert window.game_over_dialog.winner_label.text() == window.i18n.t("you_lost")
    assert window.stack.currentWidget() is window.lobby
    assert not window.battle._surrender_btn.isEnabled()
