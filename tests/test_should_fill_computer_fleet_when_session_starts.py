"""Client SessionState → fleets after start (S-04-1). No HTTP."""

from __future__ import annotations

from typing import Any

from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import FLEET_SPEC, SHIP_LENGTH, ShipStatus, ShipType
from tests.test_should_post_sessions_when_client_starts import created_session_payload

_PLAYER_KINDS: tuple[tuple[str, int], ...] = (
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Cruiser", 3),
    ("Destroyer", 2),
    ("Destroyer", 2),
    ("Destroyer", 2),
    ("Boat", 1),
    ("Boat", 1),
    ("Boat", 1),
    ("Boat", 1),
)


def full_start_payload() -> dict[str, Any]:
    """FT-009 playerFleet (10 ships) plus Computer placeholder on the client."""
    payload = created_session_payload()
    ships: list[dict[str, Any]] = []
    for row, (type_name, length) in enumerate(_PLAYER_KINDS):
        ships.append(
            {
                "type": type_name,
                "status": "Intact",
                "decks": [
                    {
                        "destroyed": False,
                        "coords": {"column": column, "row": row},
                    }
                    for column in range(length)
                ],
            }
        )
    payload["playerFleet"] = {"ships": ships}
    return payload


def test_should_fill_computer_fleet_when_session_starts() -> None:
    """FT-009 / FT-015: Computer rows are spec composition, all INTACT, decks hidden."""
    scene = session_state_to_scene(created_session_payload())
    assert [ship.type for ship in scene.backend_ships] == list(FLEET_SPEC)
    for ship, kind in zip(scene.backend_ships, FLEET_SPEC, strict=True):
        assert ship.status is ShipStatus.INTACT
        assert ship.hide_intact_bars is True
        assert ship.decks_hit == tuple(False for _ in range(SHIP_LENGTH[kind]))


def test_should_map_ten_player_ships_when_fleet_payload_complete() -> None:
    """FT-009: playerFleet of 10 ships maps 1:1; Computer still 10 placeholders."""
    scene = session_state_to_scene(full_start_payload())
    assert len(scene.player_ships) == 10
    assert [ship.type for ship in scene.player_ships] == list(FLEET_SPEC)
    assert all(ship.status is ShipStatus.INTACT for ship in scene.player_ships)
    assert all(ship.hide_intact_bars is False for ship in scene.player_ships)
    assert scene.player_ships[0].deck_coords == (
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
    )
    assert len(scene.backend_ships) == 10
    assert scene.player_ships[0].type is ShipType.BATTLESHIP
