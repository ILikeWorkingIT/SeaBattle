"""Client fleet rows after shotResolved (S-04-1). No GUI, no live WS."""

from __future__ import annotations

import pytest

from frontend.client.party_frames import apply_shot_resolved
from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import ShipStatus, ShipType, ShotResult, Side
from frontend.mock.static_scene import BattleScene
from tests.test_should_fill_computer_fleet_when_session_starts import full_start_payload
from tests.test_should_post_sessions_when_client_starts import created_session_payload


def _scene(*, full_player: bool = False) -> BattleScene:
    payload = full_start_payload() if full_player else created_session_payload()
    return session_state_to_scene(payload)


def _resolved(
    *,
    shooter: str,
    seq: int,
    column: int,
    row: int,
    result: str,
    turn: str,
    affected: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    cells = affected or [
        {"coords": {"column": column, "row": row}, "mark": result},
    ]
    return {
        "type": "shotResolved",
        "seq": seq,
        "shooter": shooter,
        "coords": {"column": column, "row": row},
        "result": result,
        "affectedCells": cells,
        "turn": turn,
        "remainTtlSeconds": 1800,
    }


def _buffer_miss(occupied: tuple[tuple[int, int], ...]) -> list[dict[str, object]]:
    occupied_set = set(occupied)
    cells: list[dict[str, object]] = []
    seen: set[tuple[int, int]] = set()
    for column, row in occupied:
        for delta_col in (-1, 0, 1):
            for delta_row in (-1, 0, 1):
                col = column + delta_col
                r = row + delta_row
                if not (0 <= col <= 9 and 0 <= r <= 9):
                    continue
                if (col, r) in occupied_set or (col, r) in seen:
                    continue
                seen.add((col, r))
                cells.append({"coords": {"column": col, "row": r}, "mark": "MISS"})
    return cells


def _player_hit(seq: int, column: int, row: int) -> dict[str, object]:
    return _resolved(
        shooter="Player",
        seq=seq,
        column=column,
        row=row,
        result="HIT",
        turn="Player",
    )


def _player_sunk_last_deck(
    seq: int,
    column: int,
    row: int,
    occupied: tuple[tuple[int, int], ...],
) -> dict[str, object]:
    cells: list[dict[str, object]] = [
        {"coords": {"column": column, "row": row}, "mark": "SUNK"},
        *_buffer_miss(occupied),
    ]
    return _resolved(
        shooter="Player",
        seq=seq,
        column=column,
        row=row,
        result="SUNK",
        turn="Player",
        affected=cells,
    )


def test_should_wound_player_ship_when_backend_hits_deck() -> None:
    """FT-019 / FT-036: Backend HIT on a known player deck sets WOUNDED and that bar."""
    scene = _scene()
    payload = _resolved(
        shooter="Backend",
        seq=1,
        column=0,
        row=0,
        result="HIT",
        turn="Backend",
    )
    assert apply_shot_resolved(scene, payload) is True
    ship = scene.player_ships[0]
    assert ship.status is ShipStatus.WOUNDED
    assert ship.decks_hit[0] is True
    assert ship.decks_hit[1:] == (False, False, False)
    assert ship.type_known is True
    assert scene.shots[-1].shooter is Side.BACKEND
    assert scene.shots[-1].result is ShotResult.HIT


def test_should_sink_player_ship_when_backend_sinks() -> None:
    """FT-020 / FT-036: Backend SUNK marks the player ship SUNK on all decks."""
    scene = _scene()
    payload = _resolved(
        shooter="Backend",
        seq=1,
        column=0,
        row=0,
        result="SUNK",
        turn="Backend",
    )
    assert apply_shot_resolved(scene, payload) is True
    ship = scene.player_ships[0]
    assert ship.status is ShipStatus.SUNK
    assert ship.decks_hit == (True, True, True, True)
    assert ship.type_known is True
    assert ship.hide_intact_bars is False


def test_should_hide_computer_type_when_player_hits() -> None:
    """FT-015 / FT-019: Player HIT uses one fleet slot: unnamed WOUNDED, not an 11th row."""
    scene = _scene()
    payload = _resolved(
        shooter="Player",
        seq=1,
        column=2,
        row=3,
        result="HIT",
        turn="Player",
    )
    assert apply_shot_resolved(scene, payload) is True
    wounded = [ship for ship in scene.backend_ships if ship.status is ShipStatus.WOUNDED]
    assert len(wounded) == 1
    row = wounded[0]
    assert row.type_known is False
    assert row.hide_intact_bars is True
    assert row.decks_hit == (True,)
    intact = [ship for ship in scene.backend_ships if ship.status is ShipStatus.INTACT]
    assert len(intact) == 9
    assert all(ship.hide_intact_bars is True for ship in intact)
    assert all(ship.type_known is True for ship in intact)
    assert len(scene.backend_ships) == 10


def test_should_keep_ten_computer_ships_when_player_hits() -> None:
    """FT-009 / FT-015 / FT-019: after first HIT Computer fleet stays 10 (9 INTACT + 1 WOUNDED)."""
    scene = _scene()
    payload = _player_hit(1, 2, 3)
    assert apply_shot_resolved(scene, payload) is True
    assert len(scene.backend_ships) == 10
    statuses = [ship.status for ship in scene.backend_ships]
    assert statuses.count(ShipStatus.INTACT) == 9
    assert statuses.count(ShipStatus.WOUNDED) == 1
    assert statuses.count(ShipStatus.SUNK) == 0


@pytest.mark.parametrize(
    ("sunk_count", "kind"),
    [
        (1, ShipType.BOAT),
        (2, ShipType.DESTROYER),
        (3, ShipType.CRUISER),
        (4, ShipType.BATTLESHIP),
    ],
)
def test_should_reveal_computer_type_when_player_sinks(
    sunk_count: int,
    kind: ShipType,
) -> None:
    """FT-015 / FT-020 / FT-021: all decks SUNK in one frame (boat from first shot)."""
    scene = _scene()
    cells = [
        {"coords": {"column": index, "row": 0}, "mark": "SUNK"}
        for index in range(sunk_count)
    ]
    payload = _resolved(
        shooter="Player",
        seq=1,
        column=sunk_count - 1,
        row=0,
        result="SUNK",
        turn="Player",
        affected=cells,
    )
    assert apply_shot_resolved(scene, payload) is True
    sunk = [ship for ship in scene.backend_ships if ship.status is ShipStatus.SUNK]
    assert len(sunk) == 1
    ship = sunk[0]
    assert ship.type is kind
    assert ship.type_known is True
    assert ship.decks_hit == tuple(True for _ in range(sunk_count))
    assert ship.hide_intact_bars is False
    intact = [item for item in scene.backend_ships if item.status is ShipStatus.INTACT]
    assert len(intact) == 9
    assert len(scene.backend_ships) == 10


def test_should_sink_computer_cruiser_when_hit_hit_sunk_chain() -> None:
    """FT-015 / FT-019 / FT-020 / FT-021: length from HIT|SUNK line, not SUNK count in frame."""
    scene = _scene()
    occupied = ((4, 3), (5, 3), (6, 3))
    assert apply_shot_resolved(scene, _player_hit(1, 4, 3)) is True
    assert apply_shot_resolved(scene, _player_hit(2, 5, 3)) is True
    assert apply_shot_resolved(scene, _player_sunk_last_deck(3, 6, 3, occupied)) is True
    sunk = [ship for ship in scene.backend_ships if ship.status is ShipStatus.SUNK]
    unknown_wounded = [
        ship
        for ship in scene.backend_ships
        if ship.status is ShipStatus.WOUNDED and not ship.type_known
    ]
    intact = [ship for ship in scene.backend_ships if ship.status is ShipStatus.INTACT]
    assert len(sunk) == 1
    assert sunk[0].type is ShipType.CRUISER
    assert sunk[0].type_known is True
    assert sunk[0].decks_hit == (True, True, True)
    assert unknown_wounded == []
    assert len(intact) == 9
    assert all(ship.hide_intact_bars is True for ship in intact)
    assert len(scene.backend_ships) == 10


def test_should_keep_unknown_wounded_when_other_ship_hit_before_sunk() -> None:
    """FT-015 / FT-019 / FT-020: leftover HIT on another ship stays unnamed WOUNDED."""
    scene = _scene()
    occupied = ((4, 3), (5, 3), (6, 3))
    assert apply_shot_resolved(scene, _player_hit(1, 4, 3)) is True
    assert apply_shot_resolved(scene, _player_hit(2, 5, 3)) is True
    assert apply_shot_resolved(scene, _player_hit(3, 0, 8)) is True
    assert apply_shot_resolved(scene, _player_sunk_last_deck(4, 6, 3, occupied)) is True
    sunk = [ship for ship in scene.backend_ships if ship.status is ShipStatus.SUNK]
    unknown_wounded = [
        ship
        for ship in scene.backend_ships
        if ship.status is ShipStatus.WOUNDED and not ship.type_known
    ]
    intact = [ship for ship in scene.backend_ships if ship.status is ShipStatus.INTACT]
    assert len(sunk) == 1
    assert sunk[0].type is ShipType.CRUISER
    assert len(unknown_wounded) == 1
    assert unknown_wounded[0].decks_hit == (True,)
    assert unknown_wounded[0].hide_intact_bars is True
    assert len(intact) == 8
    assert len(scene.backend_ships) == 10


def test_should_leave_fleets_when_player_misses() -> None:
    """FT-018: Player MISS does not change fleet rows."""
    scene = _scene(full_player=True)
    player_before = list(scene.player_ships)
    backend_before = list(scene.backend_ships)
    payload = _resolved(
        shooter="Player",
        seq=1,
        column=9,
        row=9,
        result="MISS",
        turn="Backend",
    )
    assert apply_shot_resolved(scene, payload) is True
    assert scene.player_ships == player_before
    assert scene.backend_ships == backend_before


def test_should_leave_fleets_when_backend_misses() -> None:
    """FT-036: Backend MISS does not change fleet rows."""
    scene = _scene(full_player=True)
    player_before = list(scene.player_ships)
    backend_before = list(scene.backend_ships)
    payload = _resolved(
        shooter="Backend",
        seq=1,
        column=8,
        row=8,
        result="MISS",
        turn="Player",
    )
    assert apply_shot_resolved(scene, payload) is True
    assert scene.player_ships == player_before
    assert scene.backend_ships == backend_before
