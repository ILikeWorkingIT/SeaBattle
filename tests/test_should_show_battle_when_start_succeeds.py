"""Lobby / battle start UI (UC-001). No QApplication.exec, worker does not run HTTP."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from frontend.client.session_start import StartSessionOutcome, session_state_to_scene
from frontend.domain.types import FLEET_SPEC, Language, ShipStatus
from frontend.ui.main_window import MainWindow
from tests.test_should_post_sessions_when_client_starts import created_session_payload


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _window(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    del qapp
    monkeypatch.setattr(
        "frontend.ui.main_window.CreateSessionWorker.start",
        lambda self: None,
    )
    return MainWindow()


def _shown_on_lobby(widget: QWidget, lobby: QWidget) -> bool:
    """Local setVisible flag. QWidget.isVisible() is False until ancestors are shown."""
    return widget.isVisibleTo(lobby)


def test_should_show_loading_when_start_match_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-001 trigger: Primary / start-match / menu-new-match enter loading."""
    window = _window(qapp, monkeypatch)
    start = window.lobby.start_button
    assert start.objectName() == "Primary"
    assert start.accessibleName() == "start-match"
    assert window._act_new.objectName() == "menu-new-match"
    lobby = window.lobby
    assert _shown_on_lobby(lobby._empty, lobby)
    assert not _shown_on_lobby(lobby._loading, lobby)
    assert not _shown_on_lobby(lobby._error, lobby)
    start.click()
    assert window._start_phase == "loading"
    assert _shown_on_lobby(lobby._loading, lobby)
    assert not _shown_on_lobby(lobby._empty, lobby)
    assert not _shown_on_lobby(lobby._error, lobby)
    assert not start.isEnabled()
    assert start.text() == window.i18n.t("starting")
    assert not window._act_new.isEnabled()


def test_should_show_slot_error_when_limit_reached(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-049 / A0157: 409 keeps lobby, shows slot refusal, no battle."""
    window = _window(qapp, monkeypatch)
    window.lobby.start_button.click()
    outcome = StartSessionOutcome(
        kind="http",
        http_status=409,
        code="SESSION_LIMIT_REACHED",
    )
    window._on_start_outcome(outcome)
    assert window._start_phase == "error"
    assert window.stack.currentWidget() is window.lobby
    lobby = window.lobby
    assert _shown_on_lobby(lobby._error, lobby)
    assert not _shown_on_lobby(lobby._loading, lobby)
    assert not _shown_on_lobby(lobby._empty, lobby)
    assert lobby._error.text() == outcome.text_for(
        window.settings.language is Language.RU
    )
    assert window.lobby.start_button.isEnabled()


def test_should_show_timeout_error_when_server_silent(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-001 5.2 / A0123: timeout uses err_timeout, not HTTP refusal text."""
    window = _window(qapp, monkeypatch)
    window._act_new.trigger()
    window._on_start_outcome(StartSessionOutcome(kind="timeout"))
    assert window._start_phase == "error"
    assert window.stack.currentWidget() is window.lobby
    lobby = window.lobby
    assert _shown_on_lobby(lobby._error, lobby)
    assert not _shown_on_lobby(lobby._loading, lobby)
    assert not _shown_on_lobby(lobby._empty, lobby)
    assert lobby._error.text() == window.i18n.t("err_timeout")
    assert window.lobby.start_button.isEnabled()


def test_should_show_own_fleet_without_enemy_ships_when_start_succeeds(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-001 / FT-014 / FT-015 / FT-016: battle shows own decks, hidden Computer fleet."""
    window = _window(qapp, monkeypatch)
    window.lobby.start_button.click()
    scene = session_state_to_scene(created_session_payload())
    window._on_start_outcome(
        StartSessionOutcome(kind="success", scene=scene, http_status=201)
    )
    assert window._start_phase == "success"
    assert window.stack.currentWidget() is window.battle
    assert window.battle.player_board.title == window.i18n.t("board_player")
    assert window.battle.backend_board.title == window.i18n.t("board_backend")
    player_cells = window.battle.player_board._cells
    backend_cells = window.battle.backend_board._cells
    assert any(cell.has_ship for row in player_cells for cell in row)
    assert not any(cell.has_ship for row in backend_cells for cell in row)
    assert window._live_scene is not None
    assert [ship.type for ship in window._live_scene.backend_ships] == list(
        FLEET_SPEC
    )
    assert all(
        ship.status is ShipStatus.INTACT for ship in window._live_scene.backend_ships
    )
    assert all(
        ship.hide_intact_bars is True for ship in window._live_scene.backend_ships
    )
    assert window._live_scene.player_turn is True
