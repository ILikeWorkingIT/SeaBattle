"""In-process party-channel connection registry (FT-068, A0133)."""

from __future__ import annotations

import asyncio

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class PartyHub:
    """Tracks the single live WebSocket per session id."""

    def __init__(self) -> None:
        self._sockets: dict[str, WebSocket] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def get(self, session_id: str) -> WebSocket | None:
        return self._sockets.get(session_id)

    def is_live(self, websocket: WebSocket) -> bool:
        """True only while the socket can still carry frames (FT-068)."""
        state = getattr(websocket, "client_state", None)
        return state == WebSocketState.CONNECTED

    def attach(self, session_id: str, websocket: WebSocket) -> None:
        self._sockets[session_id] = websocket

    def detach(self, session_id: str, websocket: WebSocket) -> None:
        current = self._sockets.get(session_id)
        if current is websocket:
            del self._sockets[session_id]

    def lock_for(self, session_id: str) -> asyncio.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]
