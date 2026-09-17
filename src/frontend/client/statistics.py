from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal

from frontend.client.config import GET_STATISTICS_TIMEOUT_SECONDS, api_base_url
from frontend.i18n import STRINGS
from frontend.mock.static_scene import Snapshot

_CANON_MESSAGES: dict[str, tuple[str, str]] = {
    "INTERNAL_ERROR": (STRINGS["en"]["err_internal"], STRINGS["ru"]["err_internal"]),
    "VALIDATION_ERROR": (STRINGS["en"]["err_validation"], STRINGS["ru"]["err_validation"]),
}


@dataclass(frozen=True, slots=True)
class StatisticsOutcome:
    kind: Literal["success", "timeout", "unreachable", "http"]
    snapshot: Snapshot | None = None
    http_status: int | None = None
    code: str | None = None
    message: str = ""
    message_ru: str = ""

    def text_for(self, russian: bool) -> str:
        chosen = self.message_ru if russian else self.message
        if not chosen:
            if self.kind in {"timeout", "unreachable"}:
                chosen = STRINGS["ru" if russian else "en"]["err_timeout"]
            else:
                pair = _CANON_MESSAGES.get(self.code or "")
                if pair is not None:
                    chosen = pair[1] if russian else pair[0]
                elif self.http_status:
                    chosen = f"HTTP {self.http_status}"
                else:
                    fallback = _CANON_MESSAGES["INTERNAL_ERROR"]
                    chosen = fallback[1] if russian else fallback[0]
        marker = self._diagnostic_marker()
        if marker is None or marker in chosen:
            return chosen
        return f"{chosen} ({marker})"

    def _diagnostic_marker(self) -> str | None:
        if self.code:
            if self.http_status and self.http_status != 500:
                return f"{self.code}, HTTP {self.http_status}"
            return self.code
        if self.http_status:
            return f"HTTP {self.http_status}"
        return None


def get_statistics(base_url: str | None = None, timeout: float | None = None) -> StatisticsOutcome:
    url = f"{(base_url or api_base_url()).rstrip('/')}/statistics"
    wait = GET_STATISTICS_TIMEOUT_SECONDS if timeout is None else timeout
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=wait) as response:
            raw = response.read().decode("utf-8")
            status = int(response.status)
            payload = _parse_json_object(raw)
            if status == 200 and payload is not None:
                try:
                    snapshot = snapshot_from_payload(payload)
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    return _from_error_payload(200, {"code": "INTERNAL_ERROR"})
                return StatisticsOutcome(kind="success", snapshot=snapshot, http_status=200)
            return _from_error_payload(status, payload)
    except TimeoutError:
        return StatisticsOutcome(kind="timeout")
    except socket.timeout:
        return StatisticsOutcome(kind="timeout")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return _from_error_payload(int(exc.code), _parse_json_object(raw))
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, TimeoutError | socket.timeout):
            return StatisticsOutcome(kind="timeout")
        return StatisticsOutcome(kind="unreachable")
    except json.JSONDecodeError:
        return _from_error_payload(0, {"code": "INTERNAL_ERROR"})
    except OSError:
        return StatisticsOutcome(kind="unreachable")


def snapshot_from_payload(payload: dict[str, object]) -> Snapshot:
    games = _as_nonneg_int(payload["games"], "games")
    player_wins = _as_nonneg_int(payload["playerWins"], "playerWins")
    backend_wins = _as_nonneg_int(payload["backendWins"], "backendWins")
    avg_shots = _as_nonneg_number(payload["avgShots"], "avgShots")
    if player_wins + backend_wins != games:
        raise ValueError("wins invariant")
    if games == 0 and avg_shots != 0:
        raise ValueError("avgShots must be 0 when games is 0")
    return Snapshot(games, player_wins, backend_wins, avg_shots, [])


def format_avg_shots(avg_shots: float) -> str:
    return f"{avg_shots:.1f}"


def _from_error_payload(status: int, payload: dict[str, object] | None) -> StatisticsOutcome:
    code: str | None = None
    message = ""
    message_ru = ""
    if payload is not None:
        raw_code = payload.get("code")
        if isinstance(raw_code, str) and raw_code:
            code = raw_code
        raw_en = payload.get("message")
        raw_ru = payload.get("messageRu")
        if isinstance(raw_en, str):
            message = raw_en
        if isinstance(raw_ru, str):
            message_ru = raw_ru
        detail = payload.get("detail")
        if not message and not message_ru and isinstance(detail, str) and detail:
            message = detail
            message_ru = detail
    if code is None and status == 500:
        code = "INTERNAL_ERROR"
    if not message and not message_ru and code in _CANON_MESSAGES:
        message, message_ru = _CANON_MESSAGES[code]
    return StatisticsOutcome(
        kind="http",
        http_status=status,
        code=code,
        message=message,
        message_ru=message_ru,
    )


def _parse_json_object(raw: str) -> dict[str, object] | None:
    if not raw.strip():
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        return None
    return data


def _as_nonneg_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(name)
    if value < 0:
        raise ValueError(name)
    return value


def _as_nonneg_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(name)
    if value < 0:
        raise ValueError(name)
    return float(value)
