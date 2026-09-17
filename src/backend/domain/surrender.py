"""Apply an explicit player surrender (UC-005 / FT-077)."""

from __future__ import annotations

from backend.domain.session import Session
from backend.domain.types import EndReason, SessionStatus, Side


class SurrenderRejectedError(Exception):
    """Surrender refused without a new GAME_OVER outcome."""

    def __init__(self, code: str, message: str, message_ru: str) -> None:
        super().__init__(code)
        self.code = code
        self.message = message
        self.message_ru = message_ru


def apply_surrender(session: Session) -> None:
    """Mark Backend win with endReason Surrender. Allowed on either turn (A0092)."""
    if session.status is SessionStatus.GAME_OVER:
        raise SurrenderRejectedError(
            "SHOT_GAME_OVER",
            "The match is already over.",
            "Партия уже завершена.",
        )
    session.status = SessionStatus.GAME_OVER
    session.winner = Side.BACKEND
    session.end_reason = EndReason.SURRENDER.value
