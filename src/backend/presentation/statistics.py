"""HTTP GET /statistics (UC-007, operationId getStatistics)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.errors import LedgerReadError
from backend.application.get_statistics import GetStatistics
from backend.application.ports import LedgerRepository
from backend.presentation.schemas import ErrorBody, StatisticsSnapshotOut

router = APIRouter(tags=["Statistics"])


def _error(status: int, code: str, message: str, message_ru: str) -> JSONResponse:
    body = ErrorBody(code=code, message=message, messageRu=message_ru)
    return JSONResponse(status_code=status, content=body.model_dump())


@router.get(
    "/statistics",
    response_model=StatisticsSnapshotOut,
    responses={500: {"model": ErrorBody}},
)
async def get_statistics(request: Request) -> StatisticsSnapshotOut | JSONResponse:
    """Return global aggregates over GAME_OVER records; zeros if none (FT-042)."""
    store: LedgerRepository = request.app.state.ledger_store
    try:
        result = await GetStatistics(store).execute()
    except LedgerReadError:
        return _error(
            500,
            "INTERNAL_ERROR",
            "Internal server error.",
            "Внутренняя ошибка сервера.",
        )

    snap = result.snapshot
    return StatisticsSnapshotOut(
        games=snap.games,
        playerWins=snap.player_wins,
        backendWins=snap.backend_wins,
        avgShots=snap.avg_shots,
    )
