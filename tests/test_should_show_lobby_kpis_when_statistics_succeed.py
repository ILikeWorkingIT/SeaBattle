"""Lobby / stats dialog UI (UC-007). No QApplication.exec, worker does not run HTTP."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from frontend.client.statistics import StatisticsOutcome, format_avg_shots
from frontend.client.worker import GetStatisticsWorker
from frontend.domain.types import Language
from frontend.mock.static_scene import Snapshot
from frontend.ui.lobby_screen import LobbyScreen
from frontend.ui.main_window import MainWindow


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
    starts: list[int] | None = None,
) -> MainWindow:
    del qapp
    monkeypatch.setattr(
        "frontend.ui.main_window.CreateSessionWorker.start",
        lambda self: None,
    )

    def fake_start(self: GetStatisticsWorker) -> None:
        if starts is not None:
            starts.append(1)

    monkeypatch.setattr(
        "frontend.ui.main_window.GetStatisticsWorker.start",
        fake_start,
    )
    return MainWindow()


def _shown_on(widget: QWidget, ancestor: QWidget) -> bool:
    """Local setVisible flag. QWidget.isVisible() is False until ancestors are shown."""
    return widget.isVisibleTo(ancestor)


def _lobby_kpi(lobby: LobbyScreen, name: str) -> QLabel:
    for _caption, value in lobby._kpi_widgets:
        if value.accessibleName() == name:
            return value
    raise AssertionError(name)


def _dialog_kpi(window: MainWindow, name: str) -> QLabel:
    for _caption, value in window.stats_dialog._kpi_labels:
        if value.accessibleName() == name:
            return value
    raise AssertionError(name)


def _empty_success() -> StatisticsOutcome:
    return StatisticsOutcome(
        kind="success",
        snapshot=Snapshot(0, 0, 0, 0.0, []),
        http_status=200,
    )


def _populated_success() -> StatisticsOutcome:
    return StatisticsOutcome(
        kind="success",
        snapshot=Snapshot(4, 1, 3, 12.5, []),
        http_status=200,
    )


def test_should_skip_statistics_fetch_when_window_constructed(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S-01 / UC-007: MainWindow() without show() must not start GET /statistics."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    assert window.lobby is window.stack.currentWidget()
    assert window.lobby.start_button.accessibleName() == "start-match"
    assert starts == []
    assert window._stats_phase == "idle"
    assert window._stats_worker is None
    lobby = window.lobby
    assert not _shown_on(lobby._stats_loading, lobby)
    assert not _shown_on(lobby._stats_error, lobby)
    assert not _shown_on(lobby._stats_empty, lobby)


def test_should_show_stats_loading_when_first_shown(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 trigger: first showEvent loads statistics (not constructor)."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    window.showEvent(QShowEvent())
    assert starts == [1]
    assert window._stats_phase == "loading"
    lobby = window.lobby
    assert _shown_on(lobby._stats_loading, lobby)
    assert not _shown_on(lobby._stats_empty, lobby)
    assert not _shown_on(lobby._stats_error, lobby)
    assert lobby._stats_loading.objectName() == "lobby-stats-loading"
    assert lobby._stats_loading.text() == window.i18n.t("stats_loading")
    assert not _shown_on(lobby._kpi_cards[0], lobby)


def test_should_show_empty_zeros_when_games_are_zero(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 5.6 / US-007 AC4: games==0 is empty, not error; KPI zeros stay visible."""
    window = _window(qapp, monkeypatch)
    window.showEvent(QShowEvent())
    window._on_stats_outcome(_empty_success())
    assert window._stats_phase == "empty"
    lobby = window.lobby
    assert _shown_on(lobby._stats_empty, lobby)
    assert not _shown_on(lobby._stats_loading, lobby)
    assert not _shown_on(lobby._stats_error, lobby)
    assert lobby._stats_empty.objectName() == "lobby-stats-empty"
    assert lobby._stats_empty.text() == window.i18n.t("stats_empty")
    assert _shown_on(lobby._kpi_cards[0], lobby)
    assert _lobby_kpi(lobby, "kpi-games").text() == "0"
    assert _lobby_kpi(lobby, "kpi-player-wins").text() == "0"
    assert _lobby_kpi(lobby, "kpi-computer-wins").text() == "0"
    assert _lobby_kpi(lobby, "kpi-avg-shots").text() == format_avg_shots(0.0)


def test_should_show_kpi_values_when_statistics_succeed(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """US-007 AC1–AC2 / FT-038…FT-042: lobby KPI cards show live snapshot."""
    window = _window(qapp, monkeypatch)
    window.showEvent(QShowEvent())
    window._on_stats_outcome(_populated_success())
    assert window._stats_phase == "success"
    lobby = window.lobby
    assert not _shown_on(lobby._stats_empty, lobby)
    assert not _shown_on(lobby._stats_loading, lobby)
    assert not _shown_on(lobby._stats_error, lobby)
    assert _shown_on(lobby._kpi_cards[0], lobby)
    assert _lobby_kpi(lobby, "kpi-games").text() == "4"
    assert _lobby_kpi(lobby, "kpi-player-wins").text() == "1"
    assert _lobby_kpi(lobby, "kpi-computer-wins").text() == "3"
    assert _lobby_kpi(lobby, "kpi-avg-shots").text() == format_avg_shots(12.5)
    assert window.stack.currentWidget() is window.lobby
    assert window.lobby.start_button.isEnabled()


def test_should_show_stats_error_when_server_silent(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 5.2: timeout uses err_timeout; empty banner stays hidden."""
    window = _window(qapp, monkeypatch)
    window.showEvent(QShowEvent())
    window._on_stats_outcome(StatisticsOutcome(kind="timeout"))
    assert window._stats_phase == "error"
    lobby = window.lobby
    assert _shown_on(lobby._stats_error, lobby)
    assert not _shown_on(lobby._stats_loading, lobby)
    assert not _shown_on(lobby._stats_empty, lobby)
    assert lobby._stats_error.objectName() == "lobby-stats-error"
    assert lobby._stats_error.text() == window.i18n.t("err_timeout")
    assert not _shown_on(lobby._kpi_cards[0], lobby)
    assert window.lobby.start_button.isEnabled()
    assert window.lobby.start_button.objectName() == "Primary"


def test_should_show_stats_error_when_http_fails(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 E1: HTTP INTERNAL_ERROR is error, not empty zeros."""
    window = _window(qapp, monkeypatch)
    window.showEvent(QShowEvent())
    outcome = StatisticsOutcome(
        kind="http",
        http_status=500,
        code="INTERNAL_ERROR",
        message="Internal server error.",
        message_ru="Внутренняя ошибка сервера.",
    )
    window._on_stats_outcome(outcome)
    lobby = window.lobby
    assert window._stats_phase == "error"
    assert _shown_on(lobby._stats_error, lobby)
    assert not _shown_on(lobby._stats_empty, lobby)
    assert lobby._stats_error.text() == outcome.text_for(
        window.settings.language is Language.RU
    )


def test_should_request_statistics_when_returning_to_lobby(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 / A0135: return to lobby while visible requests a fresh GET."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    monkeypatch.setattr(window, "isVisible", lambda: True)
    window._on_stats_outcome(_populated_success())
    starts.clear()
    window._show_lobby()
    assert starts == [1]
    assert window._stats_phase == "loading"


def test_should_request_statistics_when_stats_dialog_opens(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 trigger: open-stats / menu-stats fetch without QDialog.exec."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    monkeypatch.setattr(window.stats_dialog, "exec", lambda: 0)
    assert window.lobby.stats_button.accessibleName() == "open-stats"
    assert window._act_stats.objectName() == "menu-stats"
    window.lobby.stats_button.click()
    assert starts == [1]
    assert window._stats_phase == "loading"
    dialog = window.stats_dialog
    assert _shown_on(dialog._loading, dialog)
    assert dialog._loading.objectName() == "stats-loading"
    assert not dialog.refresh_button.isEnabled()
    assert dialog.refresh_button.accessibleName() == "stats-refresh"


def test_should_request_statistics_when_refresh_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 шаг 1 / A0135: Refresh in the dialog starts another GET."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    window._on_stats_outcome(_populated_success())
    starts.clear()
    window.stats_dialog.refresh_button.click()
    assert starts == [1]
    assert window._stats_phase == "loading"
    assert not window.stats_dialog.refresh_button.isEnabled()


def test_should_show_dialog_empty_when_games_are_zero(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 5.6: dialog empty ≠ error; KPI zeros; table/chart stay available."""
    window = _window(qapp, monkeypatch)
    window._on_stats_outcome(_empty_success())
    dialog = window.stats_dialog
    assert _shown_on(dialog._empty, dialog)
    assert not _shown_on(dialog._error, dialog)
    assert not _shown_on(dialog._loading, dialog)
    assert dialog._empty.objectName() == "stats-empty"
    assert dialog._empty.text() == window.i18n.t("stats_empty")
    assert _shown_on(dialog._kpi_cards[0], dialog)
    assert _dialog_kpi(window, "dialog-kpi-games").text() == "0"
    assert _dialog_kpi(window, "dialog-kpi-avg-shots").text() == format_avg_shots(0.0)
    assert window.stats_dialog.refresh_button.isEnabled()


def test_should_show_dialog_success_when_snapshot_populated(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """US-007 AC2: dialog KPI match live snapshot after success."""
    window = _window(qapp, monkeypatch)
    window._on_stats_outcome(_populated_success())
    dialog = window.stats_dialog
    assert not _shown_on(dialog._empty, dialog)
    assert not _shown_on(dialog._error, dialog)
    assert not _shown_on(dialog._loading, dialog)
    assert _dialog_kpi(window, "dialog-kpi-games").text() == "4"
    assert _dialog_kpi(window, "dialog-kpi-player-wins").text() == "1"
    assert _dialog_kpi(window, "dialog-kpi-computer-wins").text() == "3"
    assert _dialog_kpi(window, "dialog-kpi-avg-shots").text() == format_avg_shots(12.5)


def test_should_ignore_second_request_when_stats_already_loading(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007: in-flight GET is not duplicated from Refresh or a second showEvent."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    window.showEvent(QShowEvent())
    window.showEvent(QShowEvent())
    window.stats_dialog.refresh_button.click()
    assert starts == [1]


def test_should_emit_outcome_when_statistics_worker_runs(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GetStatisticsWorker.run calls get_statistics (sync run, no live network)."""
    del qapp
    expected = _populated_success()
    monkeypatch.setattr(
        "frontend.client.worker.get_statistics",
        lambda: expected,
    )
    received: list[object] = []
    worker = GetStatisticsWorker()
    worker.finished_outcome.connect(received.append)
    worker.run()
    assert received == [expected]
