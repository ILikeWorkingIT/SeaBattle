"""ApplySurrender use case (UC-005 / FT-077). Include UC-004 on success."""

from __future__ import annotations

from dataclasses import dataclass

from backend.application.commit_game_over import CommitGameOver
from backend.application.errors import SessionNotFoundError, SessionPersistError
from backend.application.ports import LedgerRepository, SessionRepository
from backend.domain.session import Session
from backend.domain.surrender import apply_surrender


@dataclass(frozen=True, slots=True)
class ApplySurrenderResult:
    session: Session


class ApplySurrender:
    def __init__(
        self,
        sessions: SessionRepository,
        ledger: LedgerRepository,
    ) -> None:
        self._sessions = sessions
        self._ledger = ledger

    async def execute(self, session_id: str) -> ApplySurrenderResult:
        session = await self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError()

        apply_surrender(session)
        try:
            await CommitGameOver(self._sessions, self._ledger).execute(session)
        except SessionPersistError:
            raise
        except Exception as exc:
            raise SessionPersistError() from exc
        return ApplySurrenderResult(session=session)
