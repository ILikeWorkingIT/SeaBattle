"""Application ports for session persistence and registry (FT-004)."""

from __future__ import annotations

from typing import Protocol

from backend.domain.ledger import Ledger, Record, Snapshot
from backend.domain.session import Session


class SessionRepository(Protocol):
    async def save_new(self, session: Session) -> bool:
        """
        Persist session and claim a registry slot atomically.

        Returns False if the active-session limit is already reached (FT-049).
        """

    async def get(self, session_id: str) -> Session | None:
        """Load session by id, or None if missing / expired."""

    async def save(self, session: Session, *, refresh_idle: bool = False) -> None:
        """
        Overwrite session payload.

        When ``refresh_idle`` is True (accepted shot), Redis TTL resets to idleTtl.
        Otherwise EX follows remain TTL so reconnect does not extend idle (FT-005).
        """

    async def delete(self, session_id: str) -> None:
        """Remove session JSON and registry slot (e.g. after GAME_OVER)."""

    async def release_slot(self, session_id: str) -> None:
        """Drop the FT-004 registry member immediately (A0128). Session JSON may remain until delivery (A0145)."""


class SessionRegistry(Protocol):
    async def active_count(self) -> int:
        """Number of sessions currently counted toward FT-004."""


class LedgerRepository(Protocol):
    async def load(self) -> Ledger:
        """Load completed-game records (empty ledger if none)."""

    async def load_snapshot(self) -> Snapshot:
        """
        Consistent read of global counters.

        Must not touch session keys or idle TTL (UC-007).
        """

    async def record_outcome(self, record: Record) -> bool:
        """
        Append one GAME_OVER row and bump HASH counters.

        Returns True if the row was new, False if this sessionId was already recorded
        (retry without a second GAME_OVER / double count, A0129).
        """
