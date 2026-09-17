"""WebSocket party channel (UC-002…UC-006): snapshot, shots, surrender, resume."""

from __future__ import annotations

import asyncio
import re
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.application.apply_shot import ApplyPlayerShot
from backend.application.apply_surrender import ApplySurrender
from backend.application.errors import SessionNotFoundError, SessionPersistError
from backend.application.play_backend_turns import PlayBackendTurns
from backend.domain.session import Session
from backend.domain.shot import ShotApplication, ShotRejectedError
from backend.domain.surrender import SurrenderRejectedError
from backend.domain.types import SessionStatus, Side
from backend.infrastructure.redis_session_store import RedisSessionStore
from backend.presentation.party_hub import PartyHub
from backend.presentation.schemas import session_to_api

router = APIRouter(tags=["Real-time"])

_SESSION_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
_TTL_POLL_SECONDS = 0.05


def _ws_error(code: str, message: str, message_ru: str) -> dict[str, str]:
    return {
        "type": "error",
        "code": code,
        "message": message,
        "messageRu": message_ru,
    }


def _coords_payload(column: int, row: int, code: str) -> dict[str, int | str]:
    return {"column": column, "row": row, "code": code}


def _shot_resolved_event(application: ShotApplication) -> dict[str, Any]:
    shot = application.shot
    return {
        "type": "shotResolved",
        "seq": shot.seq,
        "shooter": shot.shooter.value,
        "coords": _coords_payload(
            shot.coords.column, shot.coords.row, shot.coords.code
        ),
        "result": shot.result.value,
        "affectedCells": [
            {
                "coords": _coords_payload(
                    cell.coords.column, cell.coords.row, cell.coords.code
                ),
                "mark": cell.mark.value,
            }
            for cell in application.affected_cells
        ],
        "turn": application.turn.value,
        "remainTtlSeconds": application.remain_ttl_seconds,
    }


def _game_over_event(session: Session, seq: int | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "gameOver",
        "winner": session.winner.value if session.winner else None,
        "endReason": session.end_reason,
    }
    if seq is not None and seq >= 1:
        payload["seq"] = seq
    return payload


def _session_aborted_event() -> dict[str, str]:
    return {
        "type": "sessionAborted",
        "code": "SESSION_ABORTED",
        "message": (
            "The match was interrupted due to a server error. Start a new game."
        ),
        "messageRu": "Партия прервана из-за ошибки сервера. Начните новую.",
    }


def _ttl_expired_event() -> dict[str, str]:
    return {"type": "ttlExpired"}


async def _close_quietly(websocket: WebSocket) -> None:
    with suppress(Exception):
        await websocket.close()


async def _reject_handshake(websocket: WebSocket, status_code: int) -> None:
    """Refuse upgrade before accept (FT-067 / FT-068)."""
    del status_code
    await websocket.close(code=1008)


async def _watch_idle_ttl(
    websocket: WebSocket,
    store: RedisSessionStore,
    hub: PartyHub,
    session_id: str,
) -> None:
    """Push ttlExpired while the client is still on the channel (FT-066)."""
    try:
        while True:
            async with hub.lock_for(session_id):
                session = await store.get(session_id)
                if session is None:
                    return
                if session.remain_ttl_seconds() <= 0:
                    with suppress(Exception):
                        await websocket.send_json(_ttl_expired_event())
                    await store.delete(session_id)
                    await _close_quietly(websocket)
                    return
            await asyncio.sleep(_TTL_POLL_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception:
        return


@router.websocket("/sessions/{session_id}/ws")
async def open_party_channel(websocket: WebSocket, session_id: str) -> None:
    store: RedisSessionStore = websocket.app.state.session_store
    hub: PartyHub = websocket.app.state.party_hub

    if not _SESSION_ID_RE.fullmatch(session_id):
        await _reject_handshake(websocket, 404)
        return

    session = await store.get(session_id)
    if session is None or session.remain_ttl_seconds() <= 0:
        await _reject_handshake(websocket, 404)
        return
    if session.status is SessionStatus.GAME_OVER:
        await store.delete(session_id)
        await _reject_handshake(websocket, 404)
        return

    async with hub.lock_for(session_id):
        previous = hub.get(session_id)
        if previous is not None and hub.is_live(previous):
            await _reject_handshake(websocket, 409)
            return
        if previous is not None:
            hub.detach(session_id, previous)
            await _close_quietly(previous)

        await websocket.accept()
        hub.attach(session_id, websocket)
        session.connected = True
        try:
            await store.save(session, refresh_idle=False)
        except Exception:
            hub.detach(session_id, websocket)
            await websocket.close(code=1011)
            return

    ttl_watch: asyncio.Task[None] | None = None
    try:
        await websocket.send_json(
            {"type": "sessionSnapshot", "session": session_to_api(session).model_dump()}
        )
        ttl_watch = asyncio.create_task(
            _watch_idle_ttl(websocket, store, hub, session_id)
        )

        while True:
            try:
                payload = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                await websocket.send_json(
                    _ws_error(
                        "VALIDATION_ERROR",
                        "Request body is missing required fields or has the wrong type.",
                        "В запросе нет обязательных полей или неверный тип данных.",
                    )
                )
                continue

            if not isinstance(payload, dict):
                await websocket.send_json(
                    _ws_error(
                        "VALIDATION_ERROR",
                        "Request body is missing required fields or has the wrong type.",
                        "В запросе нет обязательных полей или неверный тип данных.",
                    )
                )
                continue

            msg_type = payload.get("type")
            if msg_type == "surrender":
                async with hub.lock_for(session_id):
                    ledger = websocket.app.state.ledger_store
                    try:
                        result = await ApplySurrender(store, ledger).execute(
                            session_id
                        )
                    except SurrenderRejectedError as exc:
                        await websocket.send_json(
                            _ws_error(exc.code, exc.message, exc.message_ru)
                        )
                        continue
                    except SessionNotFoundError:
                        await websocket.send_json(
                            _ws_error(
                                "SESSION_UNAVAILABLE",
                                "Session is unavailable.",
                                "Сессия недоступна.",
                            )
                        )
                        break
                    except SessionPersistError:
                        await websocket.send_json(
                            _ws_error(
                                "INTERNAL_ERROR",
                                "Internal server error.",
                                "Внутренняя ошибка сервера.",
                            )
                        )
                        continue

                    last_seq = (
                        result.session.shots[-1].seq
                        if result.session.shots
                        else None
                    )
                    await websocket.send_json(
                        _game_over_event(result.session, last_seq)
                    )
                    await store.delete(session_id)
                    break
                continue

            if msg_type != "shot":
                await websocket.send_json(
                    _ws_error(
                        "VALIDATION_ERROR",
                        "Request body is missing required fields or has the wrong type.",
                        "В запросе нет обязательных полей или неверный тип данных.",
                    )
                )
                continue

            column = payload.get("column")
            row = payload.get("row")
            if not isinstance(column, int) or not isinstance(row, int):
                await websocket.send_json(
                    _ws_error(
                        "SHOT_INVALID_PAYLOAD",
                        "Shot payload must include integer column and row.",
                        "В выстреле нужны целые column и row.",
                    )
                )
                continue

            async with hub.lock_for(session_id):
                ledger = websocket.app.state.ledger_store
                use_case = ApplyPlayerShot(store, ledger)
                try:
                    result = await use_case.execute(session_id, column, row)
                except ShotRejectedError as exc:
                    await websocket.send_json(
                        _ws_error(exc.code, exc.message, exc.message_ru)
                    )
                    continue
                except SessionNotFoundError:
                    await websocket.send_json(
                        _ws_error(
                            "SESSION_UNAVAILABLE",
                            "Session is unavailable.",
                            "Сессия недоступна.",
                        )
                    )
                    break
                except SessionPersistError:
                    await websocket.send_json(
                        _ws_error(
                            "INTERNAL_ERROR",
                            "Internal server error.",
                            "Внутренняя ошибка сервера.",
                        )
                    )
                    continue

                await websocket.send_json(_shot_resolved_event(result.application))
                if result.application.game_over:
                    await websocket.send_json(
                        _game_over_event(
                            result.session, result.application.shot.seq
                        )
                    )
                    await store.delete(session_id)
                    break

                if result.application.turn is not Side.BACKEND:
                    continue

                try:
                    backend = await PlayBackendTurns(
                        store, ledger=ledger
                    ).execute(session_id)
                except SessionNotFoundError:
                    await websocket.send_json(
                        _ws_error(
                            "SESSION_UNAVAILABLE",
                            "Session is unavailable.",
                            "Сессия недоступна.",
                        )
                    )
                    break
                except SessionPersistError:
                    await websocket.send_json(
                        _ws_error(
                            "INTERNAL_ERROR",
                            "Internal server error.",
                            "Внутренняя ошибка сервера.",
                        )
                    )
                    continue

                last_seq = result.application.shot.seq
                for application in backend.applications:
                    await websocket.send_json(_shot_resolved_event(application))
                    last_seq = application.shot.seq

                if backend.aborted:
                    await websocket.send_json(_session_aborted_event())
                    await store.delete(session_id)
                    break
                if backend.game_over:
                    seq: int | None = last_seq
                    if not backend.applications and not backend.session.shots:
                        seq = None
                    elif not backend.applications and backend.session.shots:
                        seq = backend.session.shots[-1].seq
                    await websocket.send_json(
                        _game_over_event(backend.session, seq)
                    )
                    await store.delete(session_id)
                    break
    finally:
        if ttl_watch is not None:
            ttl_watch.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await ttl_watch
        hub.detach(session_id, websocket)
        remaining = await store.get(session_id)
        if remaining is not None:
            remaining.connected = False
            try:
                await store.save(remaining, refresh_idle=False)
            except Exception:
                pass
