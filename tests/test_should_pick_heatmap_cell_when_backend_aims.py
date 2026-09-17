"""Domain tests for HeatmapBot Hunt/Target (UC-003)."""

from __future__ import annotations

import random
from datetime import datetime, timezone

from backend.domain.heatmap import (
    AimOutcome,
    compute_aim,
    hunt_weights,
    remaining_lengths,
    target_area,
    wounded_ships,
)
from backend.domain.session import (
    Board,
    Cell,
    Deck,
    Fleet,
    Occupancy,
    Session,
    Ship,
    empty_board,
    new_session,
)
from backend.domain.types import (
    BOARD_SIZE,
    CellCoordinate,
    Facing,
    HeatmapMode,
    Mark,
    OccupancyKind,
    ShipStatus,
    ShipType,
    Side,
    TargetAreaKind,
)


def _set_mark(board: Board, column: int, row: int, mark: Mark) -> None:
    index = row * BOARD_SIZE + column
    old = board.cells[index]
    board.cells[index] = Cell(
        coords=old.coords, occupancy=old.occupancy, mark=mark
    )


def _place_deck(board: Board, coords: CellCoordinate, ship_id: str) -> None:
    index = coords.row * BOARD_SIZE + coords.column
    old = board.cells[index]
    board.cells[index] = Cell(
        coords=old.coords,
        occupancy=Occupancy(kind=OccupancyKind.DECK, ship=ship_id),
        mark=old.mark,
    )


def _sunk_boat(ship_id: str, column: int, row: int) -> Ship:
    coords = CellCoordinate(column=column, row=row)
    return Ship(
        id=ship_id,
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.SUNK,
        decks=[Deck(coords=coords, destroyed=True)],
    )


def _session(player_board: Board, player_fleet: Fleet) -> Session:
    session = new_session(
        "h" * 32,
        player_board,
        empty_board(Side.BACKEND),
        player_fleet,
        Fleet(owner=Side.BACKEND, ships=[]),
        ttl_anchor=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )
    session.turn = Side.BACKEND
    return session


def test_should_pick_max_weight_cell_when_hunt_mode() -> None:
    """FT-030 / FT-064: Hunt density prefers the cell with the most placements."""
    board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if row == 0 and column in (0, 1, 2):
                continue
            _set_mark(board, column, row, Mark.MISS)
    destroyer = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0)),
            Deck(coords=CellCoordinate(column=1, row=0)),
        ],
    )
    fleet = Fleet(
        owner=Side.PLAYER,
        ships=[destroyer, _sunk_boat("p-s", 9, 9)],
    )
    session = _session(board, fleet)
    weights = hunt_weights(board, remaining_lengths(session))
    assert weights[0][1] > weights[0][0]
    assert weights[0][1] > weights[0][2]
    aim = compute_aim(session, random.Random(0))
    assert aim.outcome is AimOutcome.PICKED
    assert aim.mode is HeatmapMode.HUNT
    assert aim.pick == CellCoordinate(column=1, row=0)


def test_should_zero_cells_outside_cross_when_one_hit() -> None:
    """FT-031 / FT-032 / FT-058: Target Mode cross around a single HIT."""
    board = empty_board(Side.PLAYER)
    hit = CellCoordinate(column=5, row=5)
    cruiser = Ship(
        id="p-c",
        type=ShipType.CRUISER,
        length=3,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=hit, destroyed=True),
            Deck(coords=CellCoordinate(column=6, row=5), destroyed=False),
            Deck(coords=CellCoordinate(column=7, row=5), destroyed=False),
        ],
    )
    _place_deck(board, hit, cruiser.id)
    _set_mark(board, hit.column, hit.row, Mark.HIT)
    fleet = Fleet(owner=Side.PLAYER, ships=[cruiser])
    session = _session(board, fleet)
    kind, area = target_area(board, cruiser)
    assert kind is TargetAreaKind.CROSS
    area_set = set(area)
    assert CellCoordinate(column=4, row=5) in area_set
    assert CellCoordinate(column=6, row=5) in area_set
    assert CellCoordinate(column=5, row=4) in area_set
    assert CellCoordinate(column=5, row=6) in area_set
    aim = compute_aim(session, random.Random(1))
    assert aim.outcome is AimOutcome.PICKED
    assert aim.mode is HeatmapMode.TARGET
    assert aim.target_ship == cruiser.id
    assert aim.pick in area_set


def test_should_restrict_axis_when_two_hits_on_line() -> None:
    """FT-058: two HITs on a line → only axis extensions."""
    board = empty_board(Side.PLAYER)
    hits = (
        CellCoordinate(column=2, row=5),
        CellCoordinate(column=3, row=5),
    )
    destroyer = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=hits[0], destroyed=True),
            Deck(coords=hits[1], destroyed=True),
        ],
    )
    for coords in hits:
        _place_deck(board, coords, destroyer.id)
        _set_mark(board, coords.column, coords.row, Mark.HIT)
    kind, area = target_area(board, destroyer)
    assert kind is TargetAreaKind.AXIS
    area_set = set(area)
    assert CellCoordinate(column=1, row=5) in area_set
    assert CellCoordinate(column=4, row=5) in area_set
    assert CellCoordinate(column=2, row=4) not in area_set
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[destroyer]))
    aim = compute_aim(session, random.Random(2))
    assert aim.pick in area_set


def test_should_finish_first_wounded_when_two_ships_hit() -> None:
    """FT-079: finish one wounded ship before switching to another."""
    board = empty_board(Side.PLAYER)
    first = Ship(
        id="p-a",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=CellCoordinate(column=1, row=1), destroyed=True),
            Deck(coords=CellCoordinate(column=2, row=1), destroyed=False),
        ],
    )
    second = Ship(
        id="p-b",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=CellCoordinate(column=8, row=8), destroyed=True),
            Deck(coords=CellCoordinate(column=7, row=8), destroyed=False),
        ],
    )
    _place_deck(board, CellCoordinate(column=1, row=1), first.id)
    _set_mark(board, 1, 1, Mark.HIT)
    _place_deck(board, CellCoordinate(column=8, row=8), second.id)
    _set_mark(board, 8, 8, Mark.HIT)
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[first, second]))
    assert wounded_ships(session)[0].id == first.id
    aim = compute_aim(session, random.Random(3))
    assert aim.target_ship == first.id
    assert aim.pick is not None
    assert abs(aim.pick.column - 1) + abs(aim.pick.row - 1) == 1


def test_should_return_empty_aim_when_no_length_two_fit() -> None:
    """FT-065: empty heatmap — no free cell with weight > 0."""
    board = empty_board(Side.PLAYER)
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if (column + row) % 2 == 0:
                continue
            _set_mark(board, column, row, Mark.MISS)
    destroyer = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0)),
            Deck(coords=CellCoordinate(column=0, row=1)),
        ],
    )
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[destroyer]))
    aim = compute_aim(session, random.Random(4))
    assert aim.outcome is AimOutcome.EMPTY
    assert aim.pick is None


def test_should_not_use_hidden_decks_when_computing_hunt() -> None:
    """Hunt counts placements from marks only, not occupancy (FT-050)."""
    board = empty_board(Side.PLAYER)
    _place_deck(board, CellCoordinate(column=0, row=0), "hidden")
    weights = hunt_weights(board, (1,))
    assert weights[0][0] == 1
    assert weights[5][5] == 1


def test_should_omit_sunk_lengths_when_listing_remaining() -> None:
    """FT-029: heatmap uses unsunk ship lengths, including wounded."""
    board = empty_board(Side.PLAYER)
    wounded = Ship(
        id="p-d",
        type=ShipType.DESTROYER,
        length=2,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=CellCoordinate(column=0, row=0), destroyed=True),
            Deck(coords=CellCoordinate(column=1, row=0), destroyed=False),
        ],
    )
    fleet = Fleet(
        owner=Side.PLAYER,
        ships=[wounded, _sunk_boat("p-s", 9, 9)],
    )
    session = _session(board, fleet)
    assert remaining_lengths(session) == (2,)


def test_should_change_hunt_density_when_remaining_lengths_differ() -> None:
    """FT-029 / FT-028: Hunt weights depend on remaining lengths, not occupancy."""
    board = empty_board(Side.PLAYER)
    one = hunt_weights(board, (1,))
    four = hunt_weights(board, (4,))
    assert four[5][5] > one[5][5]
    assert four[0][0] < four[5][5]


def test_should_assign_equal_max_inside_cross_when_target_mode() -> None:
    """FT-033: Target Mode gives the max weight to every cell in the area."""
    board = empty_board(Side.PLAYER)
    hit = CellCoordinate(column=5, row=5)
    cruiser = Ship(
        id="p-c",
        type=ShipType.CRUISER,
        length=3,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=hit, destroyed=True),
            Deck(coords=CellCoordinate(column=6, row=5), destroyed=False),
            Deck(coords=CellCoordinate(column=7, row=5), destroyed=False),
        ],
    )
    _place_deck(board, hit, cruiser.id)
    _set_mark(board, hit.column, hit.row, Mark.HIT)
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[cruiser]))
    _kind, area = target_area(board, cruiser)
    picks = {compute_aim(session, random.Random(seed)).pick for seed in range(20)}
    assert picks <= set(area)
    assert len(picks) > 1


def test_should_pick_random_leader_when_hunt_weights_tie() -> None:
    """FT-034: equal max Hunt weights → random cell among leaders."""
    board = empty_board(Side.PLAYER)
    fleet = Fleet(
        owner=Side.PLAYER,
        ships=[
            Ship(
                id="p-b",
                type=ShipType.BOAT,
                length=1,
                facing=Facing.HORIZONTAL,
                status=ShipStatus.INTACT,
                decks=[Deck(coords=CellCoordinate(column=0, row=0))],
            )
        ],
    )
    session = _session(board, fleet)
    weights = hunt_weights(board, remaining_lengths(session))
    max_weight = max(max(row) for row in weights)
    leaders = {
        CellCoordinate(column=column, row=row)
        for row in range(BOARD_SIZE)
        for column in range(BOARD_SIZE)
        if weights[row][column] == max_weight
    }
    picks = {compute_aim(session, random.Random(seed)).pick for seed in range(30)}
    assert picks <= leaders
    assert len(picks) > 1


def test_should_return_empty_aim_when_turn_is_player() -> None:
    """UC-003: aim runs only while the Backend holds the turn."""
    board = empty_board(Side.PLAYER)
    boat = Ship(
        id="p-b",
        type=ShipType.BOAT,
        length=1,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.INTACT,
        decks=[Deck(coords=CellCoordinate(column=0, row=0))],
    )
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[boat]))
    session.turn = Side.PLAYER
    aim = compute_aim(session, random.Random(0))
    assert aim.outcome is AimOutcome.EMPTY
    assert aim.pick is None


def test_should_include_gap_on_axis_when_two_hits_skip_decks() -> None:
    """FT-058 / A0026: UNCHECKED cells between HITs stay in Target (not EMPTY)."""
    board = empty_board(Side.PLAYER)
    decks = (
        CellCoordinate(column=2, row=4),
        CellCoordinate(column=3, row=4),
        CellCoordinate(column=4, row=4),
        CellCoordinate(column=5, row=4),
    )
    battleship = Ship(
        id="p-b",
        type=ShipType.BATTLESHIP,
        length=4,
        facing=Facing.HORIZONTAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=decks[0], destroyed=True),
            Deck(coords=decks[1], destroyed=False),
            Deck(coords=decks[2], destroyed=False),
            Deck(coords=decks[3], destroyed=True),
        ],
    )
    for coords in decks:
        _place_deck(board, coords, battleship.id)
    _set_mark(board, 2, 4, Mark.HIT)
    _set_mark(board, 5, 4, Mark.HIT)
    _set_mark(board, 1, 4, Mark.MISS)
    _set_mark(board, 6, 4, Mark.MISS)
    kind, area = target_area(board, battleship)
    assert kind is TargetAreaKind.AXIS
    area_set = set(area)
    assert CellCoordinate(column=3, row=4) in area_set
    assert CellCoordinate(column=4, row=4) in area_set
    assert CellCoordinate(column=1, row=4) not in area_set
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[battleship]))
    aim = compute_aim(session, random.Random(5))
    assert aim.outcome is AimOutcome.PICKED
    assert aim.mode is HeatmapMode.TARGET
    assert aim.pick in area_set
    assert aim.pick in (
        CellCoordinate(column=3, row=4),
        CellCoordinate(column=4, row=4),
    )


def test_should_include_cells_past_inner_hit_when_axis_has_gaps() -> None:
    """FT-058: a HIT on the axis must not hide UNCHECKED cells further along the span."""
    board = empty_board(Side.PLAYER)
    decks = (
        CellCoordinate(column=1, row=1),
        CellCoordinate(column=1, row=2),
        CellCoordinate(column=1, row=3),
        CellCoordinate(column=1, row=4),
    )
    battleship = Ship(
        id="p-b",
        type=ShipType.BATTLESHIP,
        length=4,
        facing=Facing.VERTICAL,
        status=ShipStatus.WOUNDED,
        decks=[
            Deck(coords=decks[0], destroyed=True),
            Deck(coords=decks[1], destroyed=False),
            Deck(coords=decks[2], destroyed=True),
            Deck(coords=decks[3], destroyed=False),
        ],
    )
    for coords in decks:
        _place_deck(board, coords, battleship.id)
    _set_mark(board, 1, 1, Mark.HIT)
    _set_mark(board, 1, 3, Mark.HIT)
    _set_mark(board, 1, 0, Mark.MISS)
    _set_mark(board, 1, 5, Mark.MISS)
    kind, area = target_area(board, battleship)
    assert kind is TargetAreaKind.AXIS
    area_set = set(area)
    assert CellCoordinate(column=1, row=2) in area_set
    assert CellCoordinate(column=1, row=4) in area_set
    session = _session(board, Fleet(owner=Side.PLAYER, ships=[battleship]))
    aim = compute_aim(session, random.Random(6))
    assert aim.outcome is AimOutcome.PICKED
    assert aim.mode is HeatmapMode.TARGET
    assert aim.pick in area_set
