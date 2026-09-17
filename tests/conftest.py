"""Shared fixtures for backend tests (no live Redis / Docker)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.application.errors import LedgerWriteError
from backend.domain.ledger import (
    InconsistentLedgerError,
    Ledger,
    Record,
    Snapshot,
    snapshot_from_counters,
    snapshot_from_records,
)
from backend.domain.session import Session
from backend.domain.types import SLOT_LIMIT, Side
from backend.infrastructure.settings import Settings
from backend.presentation.party_hub import PartyHub
from backend.presentation.sessions import router as sessions_router
from backend.presentation.statistics import router as statistics_router
from backend.presentation.ws import router as ws_router


class FakeSessionStore:
    """In-memory stand-in for RedisSessionStore (FT-004 registry + session)."""

    def __init__(self, *, limit_full: bool = False) -> None:
        self.limit_full = limit_full
        self.saved: list[Session] = []
        self.by_id: dict[str, Session] = {}
        self.released: set[str] = set()
        self.fail_persist = False

    async def active_count(self) -> int:
        if self.limit_full:
            return SLOT_LIMIT
        return sum(1 for sid in self.by_id if sid not in self.released)

    async def save_new(self, session: Session) -> bool:
        if self.fail_persist:
            raise RuntimeError("persist failed")
        if self.limit_full or len(self.by_id) >= SLOT_LIMIT:
            return False
        self.saved.append(session)
        self.by_id[session.id] = session
        self.released.discard(session.id)
        return True

    async def get(self, session_id: str) -> Session | None:
        return self.by_id.get(session_id)

    async def save(self, session: Session, *, refresh_idle: bool = False) -> None:
        del refresh_idle
        if self.fail_persist:
            raise RuntimeError("persist failed")
        self.by_id[session.id] = session

    async def release_slot(self, session_id: str) -> None:
        self.released.add(session_id)

    async def delete(self, session_id: str) -> None:
        self.by_id.pop(session_id, None)
        self.released.discard(session_id)


class FakeLedgerStore:
    """In-memory journal (HASH counters + records). No live Redis."""

    def __init__(self) -> None:
        self.records: list[Record] = []
        self.counters: dict[str, int] = {
            "games": 0,
            "playerWins": 0,
            "backendWins": 0,
            "shotsSum": 0,
        }
        self.fail_read = False
        self.fail_write_remaining = 0
        self.inconsistent = False

    async def load(self) -> Ledger:
        if self.fail_read:
            raise RuntimeError("ledger unavailable")
        if self.inconsistent:
            raise InconsistentLedgerError("wins exceed games")
        return Ledger(records=tuple(self.records))

    async def load_snapshot(self) -> Snapshot:
        ledger = await self.load()
        if ledger.records:
            return snapshot_from_records(ledger.records)
        return snapshot_from_counters(
            games=self.counters["games"],
            player_wins=self.counters["playerWins"],
            backend_wins=self.counters["backendWins"],
            shots_sum=self.counters["shotsSum"],
        )

    async def record_outcome(self, record: Record) -> bool:
        if self.fail_write_remaining > 0:
            self.fail_write_remaining -= 1
            raise LedgerWriteError()
        if any(row.session_id == record.session_id for row in self.records):
            return False
        self.records.append(record)
        self.counters["games"] += 1
        if record.winner is Side.PLAYER:
            self.counters["playerWins"] += 1
        else:
            self.counters["backendWins"] += 1
        self.counters["shotsSum"] += record.shots
        return True


@pytest.fixture
def fake_store() -> FakeSessionStore:
    return FakeSessionStore()


@pytest.fixture
def fake_ledger() -> FakeLedgerStore:
    return FakeLedgerStore()


@pytest.fixture
def api_client(
    fake_store: FakeSessionStore,
    fake_ledger: FakeLedgerStore,
) -> Iterator[TestClient]:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.session_store = fake_store
        app.state.ledger_store = fake_ledger
        app.state.settings = Settings(session_start_window_seconds=2.0)
        app.state.party_hub = PartyHub()
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(sessions_router)
    app.include_router(statistics_router)
    app.include_router(ws_router)
    with TestClient(app) as client:
        yield client
