"""GetStatistics use case (UC-007 / FT-042). Read-only; no GAME_OVER write."""

from __future__ import annotations

from dataclasses import dataclass

from backend.application.errors import LedgerReadError
from backend.application.ports import LedgerRepository
from backend.domain.ledger import InconsistentLedgerError, Snapshot


@dataclass(frozen=True, slots=True)
class GetStatisticsResult:
    snapshot: Snapshot


class GetStatistics:
    def __init__(self, ledger: LedgerRepository) -> None:
        self._ledger = ledger

    async def execute(self) -> GetStatisticsResult:
        try:
            snapshot = await self._ledger.load_snapshot()
        except InconsistentLedgerError as exc:
            raise LedgerReadError() from exc
        except LedgerReadError:
            raise
        except Exception as exc:
            raise LedgerReadError() from exc
        return GetStatisticsResult(snapshot=snapshot)
