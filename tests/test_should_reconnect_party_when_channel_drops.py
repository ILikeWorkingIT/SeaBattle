"""Battle UI auto-reconnect of the same launch (UC-006). No QApplication.exec."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit

from frontend.client.party_channel import PartyChannelWorker
from frontend.ui.main_window import MainWindow
from tests.test_should_apply_session_snapshot_when_resume_arrives import resume_session_payload
from tests.test_should_post_sessions_when_client_starts import created_session_payload
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
    starts: list[int] | None = None,
    surrenders: list[int] | None = None,
) -> MainWindow:
    monkeypatch.setattr("frontend.ui.main_window.PARTY_RECONNECT_DELAY_SECONDS", 0)
    window = _battle_window(qapp, monkeypatch)
    if starts is not None:

        def fake_start(self: PartyChannelWorker) -> None:
            del self
            starts.append(1)

        monkeypatch.setattr(
            "frontend.ui.main_window.PartyChannelWorker.start",
            fake_start,
        )
    if surrenders is not None:

        def fake_surrender(self: PartyChannelWorker) -> None:
            del self
            surrenders.append(1)

        monkeypatch.setattr(
            "frontend.ui.main_window.PartyChannelWorker.send_surrender",
            fake_surrender,
        )

    def forbid_result_dialog() -> int:
        raise AssertionError("gameOver dialog must not open")

    monkeypatch.setattr(window.game_over_dialog, "exec", forbid_result_dialog)
    return window


def _fire_reconnect(window: MainWindow) -> None:
    assert window._party_reconnect_timer.isActive()
    window._party_reconnect_timer.stop()
    window._party_reconnect_timer.timeout.emit()


def test_should_reconnect_party_when_channel_disconnected(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006 / A0133: _disconnected of the same launch schedules a new party worker."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    _enter_battle(window)
    _connect_channel(window)
    assert starts == [1]
    assert window._channel_phase == "success"
    window._on_party_frame({"type": "_disconnected"})
    assert window._channel_phase == "error"
    assert window._channel_error == window.i18n.t("err_timeout")
    assert _shown_on(window.battle.channel_error, window.battle)
    assert window._live_scene is not None
    assert window._live_scene.match_over is False
    _fire_reconnect(window)
    assert starts == [1, 1]
    assert window._channel_phase == "loading"
    window._on_party_frame({"type": "sessionSnapshot", "session": resume_session_payload()})
    assert window._channel_phase == "success"
    scene = window._live_scene
    assert scene is not None
    assert scene.player_turn is False
    assert scene.ttl_seconds == 65
    assert len(scene.shots) == 1


def test_should_show_ttl_mmss_when_battle_snapshot_bound(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-080 / US-006 AC3 / A0120: remaining idle TTL is shown as mm:ss."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    _connect_channel(window)
    assert window.battle._ttl_label.text() == "30:00"
    assert window.battle._ttl_bar.value() == 1800
    window._on_party_frame({"type": "sessionSnapshot", "session": resume_session_payload()})
    assert window.battle._ttl_label.text() == "01:05"
    assert window.battle._ttl_bar.value() == 65


def test_should_leave_match_without_surrender_when_ttl_expired(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-066: ttlExpired removes the party without GAME_OVER / surrender WS."""
    surrenders: list[int] = []
    window = _window(qapp, monkeypatch, surrenders=surrenders)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame({"type": "ttlExpired"})
    assert surrenders == []
    assert window._result_shown is False
    assert window._live_scene is not None
    assert window._live_scene.match_over is True
    assert window._channel_error == window.i18n.t("toast_ttl")
    assert not window._party_reconnect_timer.isActive()
    assert window._party is None


def test_should_omit_session_id_when_qsettings_keys_listed(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0093 / A0132: session id stays in process memory; QSettings has no session key; no id field."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    _connect_channel(window)
    scene = window._live_scene
    assert scene is not None
    session_id = scene.session_id
    keys = [str(key) for key in window.settings._settings.allKeys()]
    values = [str(window.settings._settings.value(key) or "") for key in keys]
    assert not any("session" in key.lower() for key in keys)
    assert session_id not in values
    assert window.lobby.findChildren(QLineEdit) == []
    assert window.battle.findChildren(QLineEdit) == []


def test_should_reject_incomplete_snapshot_when_session_payload_broken(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006: a broken sessionSnapshot does not replace the live scene."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    _connect_channel(window)
    before = window._live_scene
    assert before is not None
    window._on_party_frame(
        {
            "type": "sessionSnapshot",
            "session": {"sessionId": created_session_payload()["sessionId"]},
        }
    )
    assert window._live_scene is before
    assert window._channel_phase == "error"
    assert window._party_reconnect_timer.isActive()


def test_should_stop_reconnect_when_handshake_unavailable(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-067: SESSION_UNAVAILABLE handshake does not retry."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        {
            "type": "_channel_error",
            "code": "SESSION_UNAVAILABLE",
            "message": "Session is unavailable.",
            "messageRu": "Сессия недоступна.",
            "retry": False,
        }
    )
    assert window._channel_phase == "error"
    assert window._channel_error in {
        "Сессия недоступна.",
        "Session is unavailable.",
    }
    assert not window._party_reconnect_timer.isActive()


def test_should_stop_reconnect_when_returning_to_lobby(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006: leaving battle stops the same-launch reconnect timer."""
    starts: list[int] = []
    window = _window(qapp, monkeypatch, starts=starts)
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame({"type": "_disconnected"})
    assert window._party_reconnect_timer.isActive()
    window._show_lobby()
    assert not window._party_reconnect_timer.isActive()
    assert starts == [1]
    assert window.stack.currentWidget() is window.lobby
