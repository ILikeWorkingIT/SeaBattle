"""StartSession use case (UC-001 / FT-001)."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.application.errors import (
    SessionLimitReachedError,
    SessionPersistError,
    SessionStartFailedError,
)
from backend.application.ports import SessionRegistry, SessionRepository
from backend.domain.placement import PlacementTimeoutError, generate_placement_pair
from backend.domain.session import Session, new_session
from backend.domain.types import SLOT_LIMIT


@dataclass(frozen=True, slots=True)
class StartSessionResult:
    session: Session


class StartSession:
    def __init__(
        self,
        repository: SessionRepository,
        registry: SessionRegistry,
        *,
        start_window_seconds: float = 2.0,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._start_window_seconds = start_window_seconds

    async def execute(self) -> StartSessionResult:
        if await self._registry.active_count() >= SLOT_LIMIT:
            raise SessionLimitReachedError()

        deadline = time.monotonic() + self._start_window_seconds
        try:
            placement = generate_placement_pair(deadline_monotonic=deadline)
        except PlacementTimeoutError as exc:
            raise SessionStartFailedError() from exc

        session_id = secrets.token_hex(16)
        session = new_session(
            session_id,
            placement.player_board,
            placement.backend_board,
            placement.player_fleet,
            placement.backend_fleet,
            ttl_anchor=datetime.now(timezone.utc),
        )

        try:
            claimed = await self._repository.save_new(session)
        except Exception as exc:
            raise SessionPersistError() from exc

        if not claimed:
            raise SessionLimitReachedError()

        return StartSessionResult(session=session)
