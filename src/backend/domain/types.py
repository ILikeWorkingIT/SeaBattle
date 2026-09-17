"""Shared domain enums and small value objects for Sea Battle MVP."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(str, Enum):
    PLAYER = "Player"
    BACKEND = "Backend"


class GameMode(str, Enum):
    PVE = "PvE"


class SessionStatus(str, Enum):
    ACTIVE = "Active"
    GAME_OVER = "GameOver"


class ShipType(str, Enum):
    BATTLESHIP = "Battleship"
    CRUISER = "Cruiser"
    DESTROYER = "Destroyer"
    BOAT = "Boat"


class ShipStatus(str, Enum):
    INTACT = "Intact"
    WOUNDED = "Wounded"
    SUNK = "Sunk"


class Facing(str, Enum):
    HORIZONTAL = "Horizontal"
    VERTICAL = "Vertical"


class Mark(str, Enum):
    UNCHECKED = "Unchecked"
    MISS = "MISS"
    HIT = "HIT"
    SUNK = "SUNK"


class ShotResult(str, Enum):
    MISS = "MISS"
    HIT = "HIT"
    SUNK = "SUNK"


class EndReason(str, Enum):
    FLEET_LOST = "FleetLost"
    SURRENDER = "Surrender"


class OccupancyKind(str, Enum):
    EMPTY = "Empty"
    DECK = "Deck"


class HeatmapMode(str, Enum):
    HUNT = "Hunt"
    TARGET = "Target"


class AimOutcome(str, Enum):
    PICKED = "Picked"
    EMPTY = "Empty"


class TargetAreaKind(str, Enum):
    CROSS = "Cross"
    AXIS = "Axis"


SHIP_LENGTH: dict[ShipType, int] = {
    ShipType.BATTLESHIP: 4,
    ShipType.CRUISER: 3,
    ShipType.DESTROYER: 2,
    ShipType.BOAT: 1,
}

# FT-009: 1 battleship, 2 cruisers, 3 destroyers, 4 boats
FLEET_BLUEPRINT: tuple[ShipType, ...] = (
    ShipType.BATTLESHIP,
    ShipType.CRUISER,
    ShipType.CRUISER,
    ShipType.DESTROYER,
    ShipType.DESTROYER,
    ShipType.DESTROYER,
    ShipType.BOAT,
    ShipType.BOAT,
    ShipType.BOAT,
    ShipType.BOAT,
)

BOARD_SIZE = 10
IDLE_TTL_SECONDS = 1800
SLOT_LIMIT = 3


@dataclass(frozen=True, slots=True)
class CellCoordinate:
    column: int
    row: int

    def __post_init__(self) -> None:
        if not (0 <= self.column < BOARD_SIZE and 0 <= self.row < BOARD_SIZE):
            raise ValueError("coordinate out of board")

    @property
    def code(self) -> str:
        """FT-063: two-digit column-row code (A3 → 02)."""
        return f"{self.column}{self.row}"
