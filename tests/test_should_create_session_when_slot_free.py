"""Unit tests for StartSession use case (UC-001)."""

from __future__ import annotations

import pytest

from backend.application.errors import SessionLimitReachedError
from backend.application.start_session import StartSession
from tests.conftest import FakeSessionStore


@pytest.mark.asyncio
async def test_should_create_session_when_slot_free() -> None:
    """FT-001 / A0149: session id is 32 hex; first turn is Player."""
    store = FakeSessionStore()
    result = await StartSession(store, store, start_window_seconds=2.0).execute()
    assert result.session.id
    assert len(result.session.id) == 32
    assert all(ch in "0123456789abcdef" for ch in result.session.id)
    assert result.session.turn.value == "Player"
    assert len(store.saved) == 1


@pytest.mark.asyncio
async def test_should_reject_when_three_sessions_active() -> None:
    """FT-049: soft-check refuses before generation when slots are full."""
    store = FakeSessionStore(limit_full=True)
    with pytest.raises(SessionLimitReachedError):
        await StartSession(store, store, start_window_seconds=2.0).execute()
