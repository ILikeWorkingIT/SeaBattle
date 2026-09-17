"""PlayBackendTurns use case (UC-003): heatmap aim + shots on the player board."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.application.commit_game_over import CommitGameOver
from backend.application.errors import SessionNotFoundError, SessionPersistError
from backend.application.ports import LedgerRepository, SessionRepository
from backend.domain.heatmap import AimOutcome, compute_aim
from backend.domain.session import Session
from backend.domain.shot import ShotApplication, apply_backend_shot
from backend.domain.types import EndReason, SessionStatus, ShipStatus, ShotResult, Side


@dataclass(frozen=True, slots=True)
class PlayBackendTurnsResult:
    session: Session
    applications: tuple[ShotApplication, ...]
    game_over: bool
    aborted: bool


def _player_fleet_destroyed(session: Session) -> bool:
    ships = session.player_fleet.ships
    if not ships:
        return False
    return all(ship.status is ShipStatus.SUNK for ship in ships)


def _mark_backend_win(session: Session) -> None:
    session.status = SessionStatus.GAME_OVER
    session.winner = Side.BACKEND
    session.end_reason = EndReason.FLEET_LOST.value


class PlayBackendTurns:
    def __init__(
        self,
        repository: SessionRepository,
        rng: random.Random | None = None,
        *,
        ledger: LedgerRepository | None = None,
    ) -> None:
        self._repository = repository
        self._rng = rng or random.Random()
        self._ledger = ledger

    async def execute(
        self,
        session_id: str,
        *,
        now: datetime | None = None,
    ) -> PlayBackendTurnsResult:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError()

        instant = now or datetime.now(timezone.utc)
        applications: list[ShotApplication] = []

        while (
            session.status is SessionStatus.ACTIVE
            and session.turn is Side.BACKEND
            and len(applications) < 20
        ):
            aim = compute_aim(session, self._rng)
            if aim.outcome is AimOutcome.EMPTY:
                if _player_fleet_destroyed(session):
                    _mark_backend_win(session)
                    await self._persist(session, refresh_idle=False, game_over=True)
                    return PlayBackendTurnsResult(
                        session=session,
                        applications=tuple(applications),
                        game_over=True,
                        aborted=False,
                    )
                return PlayBackendTurnsResult(
                    session=session,
                    applications=tuple(applications),
                    game_over=False,
                    aborted=True,
                )

            assert aim.pick is not None
            application = apply_backend_shot(
                session, aim.pick.column, aim.pick.row, now=instant
            )
            await self._persist(
                session, refresh_idle=True, game_over=application.game_over
            )
            applications.append(application)
            if application.game_over or application.shot.result is ShotResult.MISS:
                break

        return PlayBackendTurnsResult(
            session=session,
            applications=tuple(applications),
            game_over=any(item.game_over for item in applications),
            aborted=False,
        )

    async def _persist(
        self,
        session: Session,
        *,
        refresh_idle: bool,
        game_over: bool,
    ) -> None:
        try:
            if game_over and self._ledger is not None:
                await CommitGameOver(self._repository, self._ledger).execute(session)
            else:
                await self._repository.save(session, refresh_idle=refresh_idle)
        except SessionPersistError:
            raise
        except Exception as exc:
            raise SessionPersistError() from exc
