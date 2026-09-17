"""ApplyPlayerShot use case (UC-002 / FT-017)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.application.commit_game_over import CommitGameOver
from backend.application.errors import SessionNotFoundError, SessionPersistError
from backend.application.ports import LedgerRepository, SessionRepository
from backend.domain.session import Session
from backend.domain.shot import ShotApplication, ShotRejectedError, apply_player_shot


@dataclass(frozen=True, slots=True)
class ApplyPlayerShotResult:
    session: Session
    application: ShotApplication


class ApplyPlayerShot:
    def __init__(
        self,
        repository: SessionRepository,
        ledger: LedgerRepository | None = None,
    ) -> None:
        self._repository = repository
        self._ledger = ledger

    async def execute(
        self,
        session_id: str,
        column: int,
        row: int,
        *,
        now: datetime | None = None,
    ) -> ApplyPlayerShotResult:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError()

        instant = now or datetime.now(timezone.utc)
        try:
            application = apply_player_shot(
                session, column, row, now=instant
            )
        except ShotRejectedError:
            raise

        try:
            if application.game_over and self._ledger is not None:
                await CommitGameOver(self._repository, self._ledger).execute(session)
            else:
                await self._repository.save(session, refresh_idle=True)
        except SessionPersistError:
            raise
        except Exception as exc:
            raise SessionPersistError() from exc

        return ApplyPlayerShotResult(session=session, application=application)
