"""Domain tests for fleet placement (FT-009…FT-013)."""

from __future__ import annotations

import random
import time

from backend.domain.placement import (
    PlacementTimeoutError,
    assert_fleet_valid,
    generate_placement_pair,
)


def test_should_generate_valid_fleets_when_window_allows() -> None:
    """FT-009…FT-013: composition, spacing, two boards."""
    pair = generate_placement_pair(
        deadline_monotonic=time.monotonic() + 2.0,
        rng=random.Random(42),
    )
    assert_fleet_valid(pair.player_fleet)
    assert_fleet_valid(pair.backend_fleet)
    assert pair.player_board.owner.value == "Player"
    assert pair.backend_board.owner.value == "Backend"
    assert len(pair.player_board.cells) == 100
    deck_cells = [
        c
        for c in pair.player_board.cells
        if c.occupancy.kind.value == "Deck"
    ]
    assert len(deck_cells) == 20


def test_should_raise_when_start_window_already_elapsed() -> None:
    """FT-010 / NFT-015: no placement outside the start window."""
    try:
        generate_placement_pair(deadline_monotonic=time.monotonic() - 0.01)
        raised = False
    except PlacementTimeoutError:
        raised = True
    assert raised
