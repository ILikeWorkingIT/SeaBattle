from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Language(str, Enum):
    RU = "RU"
    EN = "EN"


class Side(str, Enum):
    PLAYER = "Player"
    BACKEND = "Backend"


class SessionStatus(str, Enum):
    ACTIVE = "Active"
    GAME_OVER = "GameOver"


class EndReason(str, Enum):
    FLEET_LOST = "FleetLost"
    SURRENDER = "Surrender"


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


SHIP_LENGTH: dict[ShipType, int] = {
    ShipType.BATTLESHIP: 4,
    ShipType.CRUISER: 3,
    ShipType.DESTROYER: 2,
    ShipType.BOAT: 1,
}

FLEET_SPEC: tuple[ShipType, ...] = (
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

RU_LETTERS = ("А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "К")
EN_LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")


def letters_for(language: Language) -> tuple[str, ...]:
    return RU_LETTERS if language is Language.RU else EN_LETTERS


@dataclass(frozen=True, slots=True)
class CellCoordinate:
    column: int
    row: int

    def __post_init__(self) -> None:
        if not (0 <= self.column <= 9 and 0 <= self.row <= 9):
            raise ValueError("CellCoordinate out of range")

    @property
    def code(self) -> str:
        return f"{self.column}{self.row}"

    def as_tuple(self) -> tuple[int, int]:
        return self.column, self.row


@dataclass(frozen=True, slots=True)
class DisplayCoord:
    letter: str
    number: int

    def text(self) -> str:
        return f"{self.letter}{self.number}"


def display_coord(coords: CellCoordinate, language: Language) -> DisplayCoord:
    return DisplayCoord(letters_for(language)[coords.column], coords.row + 1)


def glyph_for(mark: Mark) -> str:
    match mark:
        case Mark.SUNK:
            return "X"
        case Mark.HIT:
            return "★"
        case Mark.MISS:
            return "–"
        case Mark.UNCHECKED:
            return ""
        case _:
            never: Mark = mark
            raise ValueError(f"Unhandled mark: {never}")
