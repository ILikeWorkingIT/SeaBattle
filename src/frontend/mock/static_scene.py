"""Static mock scene for the visual UI shell (no domain engine)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from frontend.domain.types import (
    EndReason,
    Mark,
    ShipStatus,
    ShipType,
    ShotResult,
    Side,
)
from frontend.ui.cell_view import CellView


@dataclass(slots=True)
class ShipView:
    type: ShipType
    status: ShipStatus
    decks_hit: tuple[bool, ...]
    hide_intact_bars: bool = False
    deck_coords: tuple[tuple[int, int], ...] = ()
    type_known: bool = True


@dataclass(slots=True)
class ShotView:
    seq: int
    shooter: Side
    column: int
    row: int
    result: ShotResult


@dataclass(slots=True)
class Record:
    id: str
    session_id: str
    winner: Side
    shots: int
    end_reason: EndReason


@dataclass(slots=True)
class Snapshot:
    games: int
    player_wins: int
    backend_wins: int
    avg_shots: float
    records: list[Record] = field(default_factory=list)


@dataclass(slots=True)
class GameOverView:
    player_won: bool
    end_reason: EndReason
    shot_count: int


@dataclass(slots=True)
class BattleScene:
    session_id: str
    player_turn: bool
    ttl_seconds: int
    player_cells: list[list[CellView]]
    backend_cells: list[list[CellView]]
    player_ships: list[ShipView]
    backend_ships: list[ShipView]
    shots: list[ShotView]
    game_over: GameOverView
    last_shot_seq: int = 0
    match_over: bool = False


def _empty_grid() -> list[list[CellView]]:
    return [[CellView(Mark.UNCHECKED) for _ in range(10)] for _ in range(10)]


def _set(grid: list[list[CellView]], col: int, row: int, *, mark: Mark, ship: bool = False, last: bool = False) -> None:
    grid[row][col] = CellView(mark, ship, last)


def build_stats_snapshot() -> Snapshot:
    samples = (
        (Side.PLAYER, 41, EndReason.FLEET_LOST),
        (Side.BACKEND, 36, EndReason.FLEET_LOST),
        (Side.PLAYER, 52, EndReason.FLEET_LOST),
        (Side.BACKEND, 18, EndReason.SURRENDER),
        (Side.BACKEND, 44, EndReason.FLEET_LOST),
        (Side.PLAYER, 39, EndReason.FLEET_LOST),
        (Side.PLAYER, 47, EndReason.FLEET_LOST),
        (Side.BACKEND, 55, EndReason.FLEET_LOST),
        (Side.PLAYER, 33, EndReason.FLEET_LOST),
        (Side.BACKEND, 29, EndReason.SURRENDER),
        (Side.BACKEND, 48, EndReason.FLEET_LOST),
        (Side.PLAYER, 61, EndReason.FLEET_LOST),
    )
    records = [
        Record(str(uuid4()), str(uuid4()), winner, shots, reason)
        for winner, shots, reason in samples
    ]
    games = len(records)
    player_wins = sum(1 for item in records if item.winner is Side.PLAYER)
    backend_wins = games - player_wins
    avg = sum(item.shots for item in records) / games
    return Snapshot(games, player_wins, backend_wins, avg, records)


def build_battle_scene() -> BattleScene:
    """Mid-match snapshot: boards filled, no live rules."""
    player = _empty_grid()
    backend = _empty_grid()

    # Player fleet visible (own board)
    for col in range(4):
        _set(player, col, 1, mark=Mark.UNCHECKED, ship=True)
    for col in range(3):
        _set(player, col, 3, mark=Mark.HIT if col < 2 else Mark.UNCHECKED, ship=True)
    _set(player, 2, 3, mark=Mark.HIT, ship=True)
    for row in range(2):
        _set(player, 7, row + 5, mark=Mark.SUNK if row == 0 else Mark.SUNK, ship=True)
    _set(player, 7, 5, mark=Mark.SUNK, ship=True)
    _set(player, 7, 6, mark=Mark.SUNK, ship=True)
    _set(player, 0, 8, mark=Mark.UNCHECKED, ship=True)
    _set(player, 9, 9, mark=Mark.UNCHECKED, ship=True)
    _set(player, 4, 6, mark=Mark.MISS)
    _set(player, 5, 2, mark=Mark.MISS)
    _set(player, 8, 8, mark=Mark.MISS)
    _set(player, 2, 3, mark=Mark.HIT, ship=True, last=True)

    # Computer board: fog + revealed hits/misses
    _set(backend, 1, 1, mark=Mark.MISS)
    _set(backend, 3, 4, mark=Mark.MISS)
    _set(backend, 6, 2, mark=Mark.HIT, ship=True)
    _set(backend, 6, 3, mark=Mark.HIT, ship=True)
    _set(backend, 8, 7, mark=Mark.SUNK, ship=True)
    _set(backend, 0, 9, mark=Mark.MISS)
    _set(backend, 5, 5, mark=Mark.MISS)
    _set(backend, 6, 3, mark=Mark.HIT, ship=True, last=True)

    player_ships = [
        ShipView(ShipType.BATTLESHIP, ShipStatus.INTACT, (False, False, False, False)),
        ShipView(ShipType.CRUISER, ShipStatus.WOUNDED, (True, True, False)),
        ShipView(ShipType.CRUISER, ShipStatus.INTACT, (False, False, False)),
        ShipView(ShipType.DESTROYER, ShipStatus.SUNK, (True, True)),
        ShipView(ShipType.DESTROYER, ShipStatus.INTACT, (False, False)),
        ShipView(ShipType.DESTROYER, ShipStatus.INTACT, (False, False)),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,)),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,)),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,)),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,)),
    ]
    backend_ships = [
        ShipView(ShipType.BATTLESHIP, ShipStatus.INTACT, (False, False, False, False), True),
        ShipView(ShipType.CRUISER, ShipStatus.WOUNDED, (True, True, False), False),
        ShipView(ShipType.CRUISER, ShipStatus.INTACT, (False, False, False), True),
        ShipView(ShipType.DESTROYER, ShipStatus.SUNK, (True, True), False),
        ShipView(ShipType.DESTROYER, ShipStatus.INTACT, (False, False), True),
        ShipView(ShipType.DESTROYER, ShipStatus.INTACT, (False, False), True),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,), True),
        ShipView(ShipType.BOAT, ShipStatus.SUNK, (True,), False),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,), True),
        ShipView(ShipType.BOAT, ShipStatus.INTACT, (False,), True),
    ]
    shots = [
        ShotView(1, Side.PLAYER, 1, 1, ShotResult.MISS),
        ShotView(2, Side.BACKEND, 4, 6, ShotResult.MISS),
        ShotView(3, Side.PLAYER, 6, 2, ShotResult.HIT),
        ShotView(4, Side.PLAYER, 6, 3, ShotResult.HIT),
        ShotView(5, Side.BACKEND, 2, 3, ShotResult.HIT),
        ShotView(6, Side.PLAYER, 8, 7, ShotResult.SUNK),
        ShotView(7, Side.BACKEND, 7, 5, ShotResult.HIT),
        ShotView(8, Side.BACKEND, 7, 6, ShotResult.SUNK),
        ShotView(9, Side.PLAYER, 3, 4, ShotResult.MISS),
        ShotView(10, Side.BACKEND, 5, 2, ShotResult.MISS),
        ShotView(11, Side.PLAYER, 0, 9, ShotResult.MISS),
        ShotView(12, Side.PLAYER, 5, 5, ShotResult.MISS),
    ]
    return BattleScene(
        session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        player_turn=True,
        ttl_seconds=18 * 60 + 42,
        player_cells=player,
        backend_cells=backend,
        player_ships=player_ships,
        backend_ships=backend_ships,
        shots=shots,
        game_over=GameOverView(player_won=False, end_reason=EndReason.SURRENDER, shot_count=len(shots)),
    )


STATS_SNAPSHOT = build_stats_snapshot()
BATTLE_SCENE = build_battle_scene()
LOBBY_SLOTS_USED = 0
