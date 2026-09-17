"""Client GET /statistics (UC-007). urllib is mocked — no live HTTP."""

from __future__ import annotations

import json
from email.message import Message
from io import BytesIO
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from frontend.client.statistics import (
    format_avg_shots,
    get_statistics,
    snapshot_from_payload,
)


def statistics_payload(
    *,
    games: int = 4,
    player_wins: int = 1,
    backend_wins: int = 3,
    avg_shots: float = 12.5,
) -> dict[str, Any]:
    return {
        "games": games,
        "playerWins": player_wins,
        "backendWins": backend_wins,
        "avgShots": avg_shots,
    }


class _FakeHttpResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._raw = body.encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeHttpResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_should_get_statistics_without_body_when_requesting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 / OpenAPI getStatistics / FT-042: GET /statistics, empty body."""
    captured: dict[str, object] = {}

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["data"] = request.data
        captured["timeout"] = timeout
        captured["accept"] = request.get_header("Accept")
        return _FakeHttpResponse(200, json.dumps(statistics_payload(games=0, player_wins=0, backend_wins=0, avg_shots=0)))

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test:8000", timeout=7.0)
    assert captured["url"] == "http://api.test:8000/statistics"
    assert captured["method"] == "GET"
    assert captured["data"] is None
    assert captured["timeout"] == 7.0
    assert captured["accept"] == "application/json"
    assert outcome.kind == "success"


def test_should_return_success_when_http_200_populated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """US-007 AC2 / FT-038…FT-042 / A0159: 200 maps games, wins, avgShots."""
    payload = statistics_payload()

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        return _FakeHttpResponse(200, json.dumps(payload))

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test")
    assert outcome.kind == "success"
    assert outcome.http_status == 200
    assert outcome.snapshot is not None
    assert outcome.snapshot.games == 4
    assert outcome.snapshot.player_wins == 1
    assert outcome.snapshot.backend_wins == 3
    assert outcome.snapshot.avg_shots == 12.5


def test_should_return_zero_snapshot_when_http_200_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 5.6 / US-007 AC4 / FT-041: games==0 and avgShots==0 is success, not error."""
    payload = statistics_payload(games=0, player_wins=0, backend_wins=0, avg_shots=0)

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        return _FakeHttpResponse(200, json.dumps(payload))

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test")
    assert outcome.kind == "success"
    assert outcome.snapshot is not None
    assert outcome.snapshot.games == 0
    assert outcome.snapshot.avg_shots == 0.0


def test_should_return_http_error_when_status_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """UC-007 E1: 500 INTERNAL_ERROR is an HTTP failure, no snapshot."""
    body = json.dumps(
        {
            "code": "INTERNAL_ERROR",
            "message": "Internal server error.",
            "messageRu": "Внутренняя ошибка сервера.",
        }
    ).encode("utf-8")

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        raise HTTPError(
            "http://api.test/statistics",
            500,
            "Internal Server Error",
            Message(),
            BytesIO(body),
        )

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test")
    assert outcome.kind == "http"
    assert outcome.http_status == 500
    assert outcome.code == "INTERNAL_ERROR"
    assert outcome.snapshot is None
    assert outcome.text_for(True) == "Внутренняя ошибка сервера. (INTERNAL_ERROR)"
    assert outcome.text_for(False) == "Internal server error. (INTERNAL_ERROR)"


def test_should_return_timeout_when_statistics_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 5.2: client timeout is distinct from HTTP refusal."""

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        raise TimeoutError()

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test", timeout=1.0)
    assert outcome.kind == "timeout"
    assert outcome.snapshot is None
    assert outcome.text_for(True) == "Сервер не ответил."
    assert outcome.text_for(False) == "The server did not respond."


def test_should_return_unreachable_when_url_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """UC-007 5.2: URLError without timeout is unreachable."""

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        raise URLError("connection refused")

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test")
    assert outcome.kind == "unreachable"
    assert outcome.snapshot is None
    assert outcome.text_for(True) == "Сервер не ответил."


def test_should_treat_inconsistent_payload_as_internal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-007 E1: 200 with wins ≠ games is not shown as counters."""
    payload = statistics_payload(games=2, player_wins=2, backend_wins=1, avg_shots=1.0)

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        return _FakeHttpResponse(200, json.dumps(payload))

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test")
    assert outcome.kind == "http"
    assert outcome.code == "INTERNAL_ERROR"
    assert outcome.snapshot is None
    assert "INTERNAL_ERROR" in outcome.text_for(True)


def test_should_show_http_status_when_statistics_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not map FastAPI 404 {detail} to INTERNAL_ERROR."""
    body = json.dumps({"detail": "Not Found"}).encode("utf-8")

    def fake_urlopen(request: Request, timeout: float | None = None) -> _FakeHttpResponse:
        del request, timeout
        raise HTTPError(
            "http://api.test/statistics",
            404,
            "Not Found",
            Message(),
            BytesIO(body),
        )

    monkeypatch.setattr(
        "frontend.client.statistics.urllib.request.urlopen",
        fake_urlopen,
    )
    outcome = get_statistics(base_url="http://api.test")
    assert outcome.kind == "http"
    assert outcome.http_status == 404
    assert outcome.code is None
    assert outcome.snapshot is None
    assert "404" in outcome.text_for(True)
    assert "INTERNAL_ERROR" not in outcome.text_for(True)


def test_should_reject_when_zero_games_have_nonzero_avg() -> None:
    """UC-007 5.6 / FT-041: avgShots must be 0 when games is 0."""
    with pytest.raises(ValueError):
        snapshot_from_payload(
            statistics_payload(games=0, player_wins=0, backend_wins=0, avg_shots=1.0)
        )


def test_should_format_avg_shots_with_one_decimal() -> None:
    """A0159: display one decimal; wire value stays a number on the client snapshot."""
    assert format_avg_shots(0) == "0.0"
    assert format_avg_shots(47.3) == "47.3"
