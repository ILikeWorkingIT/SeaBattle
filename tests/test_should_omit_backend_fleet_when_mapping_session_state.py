"""Mapper tests: Session → OpenAPI SessionState (FT-015)."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from backend.domain.placement import generate_placement_pair
from backend.domain.session import new_session
from backend.domain.types import OccupancyKind
from backend.presentation.schemas import session_to_api


def test_should_omit_backend_fleet_when_mapping_session_state() -> None:
    """FT-015 / OpenAPI SessionState: backendFleet never serialized."""
    pair = generate_placement_pair(deadline_monotonic=time.monotonic() + 2.0)
    session = new_session(
        "a" * 32,
        pair.player_board,
        pair.backend_board,
        pair.player_fleet,
        pair.backend_fleet,
        ttl_anchor=datetime(2026, 8, 25, 15, 0, 0, tzinfo=timezone.utc),
    )
    payload = session_to_api(session).model_dump()
    assert "backendFleet" not in payload
    assert payload["sessionId"] == "a" * 32
    assert payload["ttlAnchor"].endswith("Z")
    backend_decks = [
        c
        for c in pair.backend_board.cells
        if c.occupancy.kind is OccupancyKind.DECK
    ]
    assert backend_decks
    public_cells = payload["backendBoard"]["cells"]
    assert all("occupancy" not in cell for cell in public_cells)
