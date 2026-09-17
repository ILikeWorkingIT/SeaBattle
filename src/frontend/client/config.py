from __future__ import annotations

import os

DEFAULT_API_BASE_URL = "http://localhost:8000"
# Longer than NFT-015 p95 success (2 s) so a slow but valid 503 from the start window
# can still arrive; UC-001 5.2 treats no response as timeout.
CREATE_SESSION_TIMEOUT_SECONDS = 30.0
# UC-007 5.2: no response → timeout; GET has no start-window 503.
GET_STATISTICS_TIMEOUT_SECONDS = 30.0
# UC-002 5.2: first party handshake / silent socket → timeout.
PARTY_CHANNEL_TIMEOUT_SECONDS = 30.0
# UC-006 5.2: resume handshake while docker-proxy / :8000 may hang (not the first open).
PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS = 4.0
# UC-006 5.2: delay between resume attempts of the same process (one worker).
PARTY_RECONNECT_DELAY_SECONDS = 2.0


def api_base_url() -> str:
    raw = os.environ.get("SEA_BATTLE_API_URL", DEFAULT_API_BASE_URL).strip()
    return raw.rstrip("/") or DEFAULT_API_BASE_URL


def party_ws_url(session_id: str, base_url: str | None = None) -> str:
    http = (base_url or api_base_url()).rstrip("/")
    if http.startswith("https://"):
        origin = "wss://" + http.removeprefix("https://")
    elif http.startswith("http://"):
        origin = "ws://" + http.removeprefix("http://")
    else:
        origin = "ws://" + http
    return f"{origin}/sessions/{session_id}/ws"
