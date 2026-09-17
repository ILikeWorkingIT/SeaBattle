from __future__ import annotations

import json

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWebSockets import QWebSocket

from frontend.client.config import PARTY_CHANNEL_TIMEOUT_SECONDS, party_ws_url
from frontend.i18n import STRINGS

_VALIDATION = (
    "VALIDATION_ERROR",
    STRINGS["en"]["err_validation"],
    STRINGS["ru"]["err_validation"],
)


class PartyChannelWorker(QObject):
    """Party WebSocket on the GUI thread (reconnect after Docker stop is not a QThread)."""

    incoming = Signal(object)
    _send_text = Signal(str)

    def __init__(
        self,
        session_id: str,
        parent: QObject | None = None,
        *,
        handshake_timeout_seconds: float | None = None,
        retry_handshake: bool = False,
    ) -> None:
        super().__init__(parent)
        self._url = party_ws_url(session_id)
        self._handshake_timeout_seconds = (
            PARTY_CHANNEL_TIMEOUT_SECONDS
            if handshake_timeout_seconds is None
            else handshake_timeout_seconds
        )
        self._retry_handshake = retry_handshake
        self._socket = QWebSocket("", parent=self)
        self._handshake = QTimer(self)
        self._handshake.setSingleShot(True)
        self._opened = False
        self._closing = False
        self._drop_emitted = False
        self._handshake.timeout.connect(self._on_handshake_timeout)
        self._socket.textMessageReceived.connect(self._on_text)
        self._socket.errorOccurred.connect(self._on_error)
        self._socket.disconnected.connect(self._on_disconnected)
        self._send_text.connect(self._socket.sendTextMessage)

    def send_shot(self, column: int, row: int) -> None:
        self._send_text.emit(json.dumps({"type": "shot", "column": column, "row": row}))

    def send_surrender(self) -> None:
        self._send_text.emit(json.dumps({"type": "surrender"}))

    def shutdown(self) -> None:
        self._closing = True
        self._handshake.stop()
        self._socket.abort()

    def start(self) -> None:
        self._opened = False
        self._closing = False
        self._drop_emitted = False
        self._handshake.start(int(self._handshake_timeout_seconds * 1000))
        self._socket.open(QUrl(self._url))

    def _emit_channel_error(
        self,
        code: str,
        message: str,
        message_ru: str,
        *,
        retry: bool,
    ) -> None:
        if self._drop_emitted or self._closing:
            return
        self._drop_emitted = True
        self._handshake.stop()
        self.incoming.emit(
            {
                "type": "_channel_error",
                "code": code,
                "message": message,
                "messageRu": message_ru,
                "retry": retry,
            }
        )
        self._socket.abort()

    def _emit_disconnected(self) -> None:
        if self._drop_emitted or self._closing:
            return
        self._drop_emitted = True
        self._handshake.stop()
        self.incoming.emit({"type": "_disconnected"})
        self._socket.abort()

    def _handshake_transport_failed(self) -> None:
        if self._retry_handshake:
            self._emit_channel_error(
                "TIMEOUT",
                STRINGS["en"]["err_timeout"],
                STRINGS["ru"]["err_timeout"],
                retry=True,
            )
            return
        close_code = int(self._socket.closeCode())
        if close_code == 1008:
            self._emit_channel_error(
                "SESSION_UNAVAILABLE",
                STRINGS["en"]["err_session_unavailable"],
                STRINGS["ru"]["err_session_unavailable"],
                retry=False,
            )
            return
        self._emit_channel_error(
            "TIMEOUT",
            STRINGS["en"]["err_timeout"],
            STRINGS["ru"]["err_timeout"],
            retry=True,
        )

    def _on_text(self, text: str) -> None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            self.incoming.emit(
                {
                    "type": "error",
                    "code": _VALIDATION[0],
                    "message": _VALIDATION[1],
                    "messageRu": _VALIDATION[2],
                }
            )
            return
        if not isinstance(payload, dict):
            self.incoming.emit(
                {
                    "type": "error",
                    "code": _VALIDATION[0],
                    "message": _VALIDATION[1],
                    "messageRu": _VALIDATION[2],
                }
            )
            return
        if payload.get("type") == "sessionSnapshot":
            self._opened = True
            self._handshake.stop()
        if payload.get("type") == "error" and payload.get("code") == "SESSION_UNAVAILABLE":
            self._emit_channel_error(
                "SESSION_UNAVAILABLE",
                str(payload.get("message") or STRINGS["en"]["err_session_unavailable"]),
                str(payload.get("messageRu") or STRINGS["ru"]["err_session_unavailable"]),
                retry=self._retry_handshake,
            )
            return
        self.incoming.emit(payload)

    def _on_handshake_timeout(self) -> None:
        if not self._opened and not self._closing:
            self._emit_channel_error(
                "TIMEOUT",
                STRINGS["en"]["err_timeout"],
                STRINGS["ru"]["err_timeout"],
                retry=True,
            )

    def _on_error(self, _error: QAbstractSocket.SocketError) -> None:
        if self._closing or self._drop_emitted:
            return
        if self._opened:
            self._emit_disconnected()
            return
        self._handshake_transport_failed()

    def _on_disconnected(self) -> None:
        if self._closing or self._drop_emitted:
            return
        if self._opened:
            self._emit_disconnected()
            return
        self._handshake_transport_failed()
