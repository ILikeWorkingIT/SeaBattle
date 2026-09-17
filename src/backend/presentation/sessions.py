"""HTTP routes for session creation (UC-001) and REST shot/surrender rejection."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.errors import (
    SessionLimitReachedError,
    SessionPersistError,
    SessionStartFailedError,
)
from backend.application.start_session import StartSession
from backend.infrastructure.redis_session_store import RedisSessionStore
from backend.presentation.schemas import ErrorBody, SessionStateOut, session_to_api

router = APIRouter(tags=["Sessions"])


def _error(status: int, code: str, message: str, message_ru: str) -> JSONResponse:
    body = ErrorBody(code=code, message=message, messageRu=message_ru)
    return JSONResponse(status_code=status, content=body.model_dump())


@router.post(
    "/sessions",
    response_model=SessionStateOut,
    status_code=201,
    responses={
        400: {"model": ErrorBody},
        409: {"model": ErrorBody},
        500: {"model": ErrorBody},
        503: {"model": ErrorBody},
    },
)
async def create_session(request: Request) -> SessionStateOut | JSONResponse:
    """Create a PvE session and return the player's fleet (UC-001)."""
    raw = await request.body()
    if raw:
        return _error(
            400,
            "VALIDATION_ERROR",
            "Request body is not allowed.",
            "Тело запроса не допускается.",
        )

    store: RedisSessionStore = request.app.state.session_store
    settings = request.app.state.settings
    use_case = StartSession(
        store,
        store,
        start_window_seconds=settings.session_start_window_seconds,
    )

    try:
        result = await use_case.execute()
    except SessionLimitReachedError:
        return _error(
            409,
            "SESSION_LIMIT_REACHED",
            "No free session slot.",
            "Нет свободного слота сессии.",
        )
    except SessionStartFailedError:
        return _error(
            503,
            "SESSION_START_FAILED",
            "Could not start a session.",
            "Не удалось начать партию.",
        )
    except SessionPersistError:
        return _error(
            500,
            "INTERNAL_ERROR",
            "Internal server error.",
            "Внутренняя ошибка сервера.",
        )

    return session_to_api(result.session)


@router.post(
    "/sessions/{session_id}/shots",
    responses={400: {"model": ErrorBody}, 500: {"model": ErrorBody}},
)
async def reject_shot_over_rest(session_id: str) -> JSONResponse:
    """FT-055 / A0089: player shots are accepted only on the party WebSocket."""
    del session_id  # identity not revealed (A0001)
    return _error(
        400,
        "SHOT_WRONG_CHANNEL",
        "Shots must be sent on the party channel.",
        "Выстрел принимается только по каналу партии.",
    )


@router.post(
    "/sessions/{session_id}/surrender",
    responses={400: {"model": ErrorBody}, 500: {"model": ErrorBody}},
)
async def reject_surrender_over_rest(session_id: str) -> JSONResponse:
    """FT-077 / A0130: surrender is accepted only on the party WebSocket."""
    del session_id  # identity not revealed (A0001)
    return _error(
        400,
        "SURRENDER_WRONG_CHANNEL",
        "Surrender must be sent on the party channel.",
        "Сдача принимается только по каналу партии.",
    )
