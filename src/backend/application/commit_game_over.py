"""Commit GAME_OVER to Ledger and release the FT-004 slot (UC-004)."""

from __future__ import annotations

from backend.application.errors import LedgerWriteError, SessionPersistError
from backend.application.ports import LedgerRepository, SessionRepository
from backend.domain.ledger import Record, record_from_outcome
from backend.domain.session import Session
from backend.domain.types import EndReason, SessionStatus

_WRITE_ATTEMPTS = 3


def ledger_record_for_session(session: Session) -> Record:
    if session.status is not SessionStatus.GAME_OVER:
        raise SessionPersistError()
    if session.winner is None or not session.end_reason:
        raise SessionPersistError()
    return record_from_outcome(
        session_id=session.id,
        winner=session.winner,
        shots=len(session.shots),
        end_reason=EndReason(session.end_reason),
    )


class CommitGameOver:
    def __init__(
        self,
        sessions: SessionRepository,
        ledger: LedgerRepository,
    ) -> None:
        self._sessions = sessions
        self._ledger = ledger

    async def execute(self, session: Session) -> None:
        """Fix GAME_OVER + statistics; retry the write without a second outcome (A0129)."""
        record = ledger_record_for_session(session)
        last_error: Exception | None = None
        for _ in range(_WRITE_ATTEMPTS):
            try:
                await self._ledger.record_outcome(record)
                await self._sessions.release_slot(session.id)
                await self._sessions.save(session, refresh_idle=False)
                return
            except LedgerWriteError as exc:
                last_error = exc
            except SessionPersistError:
                raise
            except Exception as exc:
                last_error = exc
        raise SessionPersistError() from last_error
