"""GET /statistics (UC-007, operationId getStatistics)."""

from __future__ import annotations

import pytest

from backend.application.errors import LedgerReadError
from backend.application.get_statistics import GetStatistics
from backend.domain.ledger import Record
from backend.domain.types import EndReason, Side
from tests.conftest import FakeLedgerStore, FakeSessionStore


def test_should_return_zeros_when_get_statistics_empty(api_client) -> None:
    """OpenAPI empty example; UC-007 5.6."""
    response = api_client.get("/statistics")
    assert response.status_code == 200
    assert response.json() == {
        "games": 0,
        "playerWins": 0,
        "backendWins": 0,
        "avgShots": 0,
    }


def test_should_leave_session_untouched_when_get_statistics(
    api_client,
    fake_store: FakeSessionStore,
) -> None:
    created = api_client.post("/sessions")
    assert created.status_code == 201
    session_id = created.json()["sessionId"]
    before = fake_store.by_id[session_id]
    anchor = before.ttl_anchor
    turn = before.turn
    shots_len = len(before.shots)
    stats = api_client.get("/statistics")
    assert stats.status_code == 200
    after = fake_store.by_id[session_id]
    assert after.ttl_anchor == anchor
    assert after.turn == turn
    assert len(after.shots) == shots_len


def test_should_return_aggregates_when_ledger_has_records(
    api_client,
    fake_ledger: FakeLedgerStore,
) -> None:
    fake_ledger.records = [
        Record("r1", "a" * 32, Side.PLAYER, 40, EndReason.FLEET_LOST),
        Record("r2", "b" * 32, Side.BACKEND, 54, EndReason.FLEET_LOST),
    ]
    response = api_client.get("/statistics")
    assert response.status_code == 200
    body = response.json()
    assert body["games"] == 2
    assert body["playerWins"] == 1
    assert body["backendWins"] == 1
    assert body["avgShots"] == 47.0


def test_should_return_500_when_ledger_inconsistent(
    api_client,
    fake_ledger: FakeLedgerStore,
) -> None:
    fake_ledger.inconsistent = True
    response = api_client.get("/statistics")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"


@pytest.mark.asyncio
async def test_should_read_hash_counters_when_records_empty() -> None:
    store = FakeLedgerStore()
    store.counters = {
        "games": 10,
        "playerWins": 6,
        "backendWins": 4,
        "shotsSum": 473,
    }
    result = await GetStatistics(store).execute()
    assert result.snapshot.games == 10
    assert result.snapshot.player_wins == 6
    assert result.snapshot.backend_wins == 4
    assert result.snapshot.avg_shots == 47.3


@pytest.mark.asyncio
async def test_should_raise_ledger_read_when_store_fails() -> None:
    store = FakeLedgerStore()
    store.fail_read = True
    with pytest.raises(LedgerReadError):
        await GetStatistics(store).execute()


def test_should_return_500_when_ledger_unavailable(
    api_client,
    fake_ledger: FakeLedgerStore,
) -> None:
    """UC-007 E1 / OpenAPI 500: store failure maps to INTERNAL_ERROR."""
    fake_ledger.fail_read = True
    response = api_client.get("/statistics")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"


def test_should_return_hash_snapshot_when_records_empty(
    api_client,
    fake_ledger: FakeLedgerStore,
) -> None:
    """OpenAPI populated example; A0159 avgShots as JSON number."""
    fake_ledger.records = []
    fake_ledger.counters = {
        "games": 10,
        "playerWins": 6,
        "backendWins": 4,
        "shotsSum": 473,
    }
    response = api_client.get("/statistics")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "games": 10,
        "playerWins": 6,
        "backendWins": 4,
        "avgShots": 47.3,
    }
    assert isinstance(body["avgShots"], float)


def test_should_leave_ledger_untouched_when_get_statistics(
    api_client,
    fake_ledger: FakeLedgerStore,
) -> None:
    """UC-007 E2 / FT-056: GET does not append or alter aggregates."""
    row = Record("r1", "a" * 32, Side.PLAYER, 40, EndReason.FLEET_LOST)
    fake_ledger.records = [row]
    fake_ledger.counters = {
        "games": 1,
        "playerWins": 1,
        "backendWins": 0,
        "shotsSum": 40,
    }
    response = api_client.get("/statistics")
    assert response.status_code == 200
    assert fake_ledger.records == [row]
    assert fake_ledger.counters == {
        "games": 1,
        "playerWins": 1,
        "backendWins": 0,
        "shotsSum": 40,
    }


def test_should_reject_when_post_statistics(
    api_client,
    fake_ledger: FakeLedgerStore,
) -> None:
    """UC-007 5.1 / E2: write on the read path is rejected."""
    response = api_client.post("/statistics")
    assert response.status_code == 405
    assert fake_ledger.records == []
