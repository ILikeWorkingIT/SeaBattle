"""PartyChannelWorker handshake retry (S-07). Qt mocks, no live socket, no exec."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWidgets import QApplication

from frontend.client.config import (
    PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS,
    PARTY_CHANNEL_TIMEOUT_SECONDS,
)
from frontend.client.party_channel import PartyChannelWorker
from tests.test_should_reconnect_party_when_channel_drops import (
    _fire_reconnect,
    _window as _reconnect_window,
)
from tests.test_should_show_shot_result_when_computer_board_clicked import (
    _connect_channel,
    _enter_battle,
)

_SESSION_ID = "a1b2c3d4e5f6789012345678abcdef01"


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _install_handshake_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    close_code: int,
    emit: str,
) -> None:
    class FakeSocket(QObject):
        textMessageReceived = Signal(str)
        errorOccurred = Signal(QAbstractSocket.SocketError)
        disconnected = Signal()

        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            super().__init__()
            self._close_code = close_code

        def closeCode(self) -> int:
            return self._close_code

        def open(self, _url: object) -> None:
            if emit == "error":
                self.errorOccurred.emit(
                    QAbstractSocket.SocketError.ConnectionRefusedError
                )
            elif emit == "disconnected":
                self.disconnected.emit()

        def abort(self) -> None:
            return

        def sendTextMessage(self, text: str) -> None:
            del text

    class FakeTimer(QObject):
        timeout = Signal()

        def __init__(self, parent: QObject | None = None) -> None:
            super().__init__(parent)

        def setSingleShot(self, _on: bool) -> None:
            return

        def start(self, _msec: int = 0) -> None:
            return

        def stop(self) -> None:
            return

    monkeypatch.setattr("frontend.client.party_channel.QWebSocket", FakeSocket)
    monkeypatch.setattr("frontend.client.party_channel.QTimer", FakeTimer)


def _channel_error_from_run(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    *,
    close_code: int,
    emit: str,
) -> dict[str, object]:
    del qapp
    _install_handshake_fakes(monkeypatch, close_code=close_code, emit=emit)
    frames: list[object] = []
    worker = PartyChannelWorker(_SESSION_ID, retry_handshake=False)
    worker.incoming.connect(frames.append)
    worker.start()
    assert len(frames) == 1
    payload = frames[0]
    assert isinstance(payload, dict)
    assert payload.get("type") == "_channel_error"
    return payload


def test_should_set_retry_true_when_handshake_close_is_abnormal(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006 5.2: abnormal close 1006 (RST) retries handshake, not SESSION_UNAVAILABLE."""
    payload = _channel_error_from_run(
        qapp, monkeypatch, close_code=1006, emit="disconnected"
    )
    assert payload["retry"] is True
    assert payload["code"] == "TIMEOUT"


def test_should_set_retry_true_when_handshake_close_is_zero(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006 5.2: close 0 during handshake is transport drop, retry=True."""
    payload = _channel_error_from_run(
        qapp, monkeypatch, close_code=0, emit="disconnected"
    )
    assert payload["retry"] is True
    assert payload["code"] == "TIMEOUT"


def test_should_set_retry_true_when_handshake_connection_refused(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006 5.2: ConnectionRefused on handshake is transport, not close 1008."""
    payload = _channel_error_from_run(qapp, monkeypatch, close_code=0, emit="error")
    assert payload["retry"] is True
    assert payload["code"] == "TIMEOUT"


def test_should_set_retry_false_when_handshake_close_is_policy_violation(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-067: close 1008 is SESSION_UNAVAILABLE and must not retry."""
    payload = _channel_error_from_run(
        qapp, monkeypatch, close_code=1008, emit="disconnected"
    )
    assert payload["retry"] is False
    assert payload["code"] == "SESSION_UNAVAILABLE"


def test_should_keep_retrying_when_resume_handshake_close_is_policy_violation(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006 5.2: same-launch resume retries even if Qt reports close 1008 (Docker)."""
    del qapp
    _install_handshake_fakes(monkeypatch, close_code=1008, emit="disconnected")
    frames: list[object] = []
    worker = PartyChannelWorker(_SESSION_ID, retry_handshake=True)
    worker.incoming.connect(frames.append)
    worker.start()
    payload = frames[0]
    assert isinstance(payload, dict)
    assert payload["retry"] is True
    assert payload["code"] == "TIMEOUT"


def test_should_use_full_timeout_when_first_party_handshake(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-002 5.2: first party open uses the full handshake timeout, not resume 4s."""
    workers: list[PartyChannelWorker] = []

    def capture_start(self: PartyChannelWorker) -> None:
        workers.append(self)

    window = _reconnect_window(qapp, monkeypatch)
    monkeypatch.setattr(
        "frontend.ui.main_window.PartyChannelWorker.start",
        capture_start,
    )
    _enter_battle(window)
    _connect_channel(window)
    assert len(workers) == 1
    assert workers[0]._handshake_timeout_seconds == PARTY_CHANNEL_TIMEOUT_SECONDS
    assert PARTY_CHANNEL_TIMEOUT_SECONDS != PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS


def test_should_use_four_second_timeout_when_resume_handshake(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-006 5.2: same-launch resume handshake timeout is 4s."""
    workers: list[PartyChannelWorker] = []

    def capture_start(self: PartyChannelWorker) -> None:
        workers.append(self)

    window = _reconnect_window(qapp, monkeypatch)
    monkeypatch.setattr(
        "frontend.ui.main_window.PartyChannelWorker.start",
        capture_start,
    )
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame({"type": "_disconnected"})
    _fire_reconnect(window)
    assert len(workers) == 2
    assert workers[1]._handshake_timeout_seconds == PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS
    assert workers[1]._retry_handshake is True
    assert PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS == 4.0
