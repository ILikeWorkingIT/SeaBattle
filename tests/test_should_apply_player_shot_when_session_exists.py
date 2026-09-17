"""Use-case tests for ApplyPlayerShot (UC-002)."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from backend.application.apply_shot import ApplyPlayerShot
from backend.application.errors import SessionNotFoundError, SessionPersistError
from backend.domain.placement import generate_placement_pair
from backend.domain.session import new_session
from backend.domain.types import OccupancyKind
from tests.conftest import FakeSessionStore


def _put_session(store: FakeSessionStore) -> str:
    pair = generate_placement_pair(deadline_monotonic=time.monotonic() + 2.0)
    session = new_session(
        "a1" + "b" * 30,
        pair.player_board,
        pair.backend_board,
        pair.player_fleet,
        pair.backend_fleet,
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    store.by_id[session.id] = session
    return session.id


def _first_empty(store: FakeSessionStore, session_id: str) -> tuple[int, int]:
    session = store.by_id[session_id]
    for cell in session.backend_board.cells:
        if cell.occupancy.kind is OccupancyKind.EMPTY:
            return cell.coords.column, cell.coords.row
    raise AssertionError("no empty cell")


@pytest.mark.asyncio
async def test_should_apply_player_shot_when_session_exists() -> None:
    """FT-017: accepted miss persists and passes the turn."""
    store = FakeSessionStore()
    session_id = _put_session(store)
    column, row = _first_empty(store, session_id)
    result = await ApplyPlayerShot(store).execute(session_id, column, row)
    assert result.application.shot.seq == 1
    assert store.by_id[session_id].shots


@pytest.mark.asyncio
async def test_should_raise_when_session_missing_on_shot() -> None:
    """UC-002 E1: unknown id does not create a session."""
    store = FakeSessionStore()
    with pytest.raises(SessionNotFoundError):
        await ApplyPlayerShot(store).execute("a" * 32, 0, 0)


@pytest.mark.asyncio
async def test_should_raise_persist_error_when_save_fails_after_shot() -> None:
    """UC-002 E2: persist failure after a legal shot."""
    store = FakeSessionStore()
    session_id = _put_session(store)
    column, row = _first_empty(store, session_id)
    store.fail_persist = True
    with pytest.raises(SessionPersistError):
        await ApplyPlayerShot(store).execute(session_id, column, row)
