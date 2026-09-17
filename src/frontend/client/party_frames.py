from __future__ import annotations

from frontend.client.fleet_status import apply_shot_to_fleets
from frontend.domain.types import EndReason, Mark, ShotResult, Side
from frontend.mock.static_scene import BattleScene, GameOverView, ShotView
from frontend.ui.cell_view import CellView

_MARK: dict[str, Mark] = {
    "Unchecked": Mark.UNCHECKED,
    "MISS": Mark.MISS,
    "HIT": Mark.HIT,
    "SUNK": Mark.SUNK,
}
_SHOT: dict[str, ShotResult] = {"MISS": ShotResult.MISS, "HIT": ShotResult.HIT, "SUNK": ShotResult.SUNK}
_SIDE: dict[str, Side] = {"Player": Side.PLAYER, "Backend": Side.BACKEND}
_REASON: dict[str, EndReason] = {
    "FleetLost": EndReason.FLEET_LOST,
    "Surrender": EndReason.SURRENDER,
}


def apply_shot_resolved(scene: BattleScene, payload: dict[str, object]) -> bool:
    """Paint marks from a server shotResolved frame. Returns False if seq is stale."""
    seq = int(payload["seq"])
    if seq <= scene.last_shot_seq:
        return False
    shooter = _SIDE.get(str(payload.get("shooter", "")))
    result = _SHOT.get(str(payload.get("result", "")))
    coords = payload.get("coords")
    if shooter is None or result is None or not isinstance(coords, dict):
        return False
    column = int(coords["column"])
    row = int(coords["row"])
    grid = scene.backend_cells if shooter is Side.PLAYER else scene.player_cells
    _clear_last_shot(scene.player_cells)
    _clear_last_shot(scene.backend_cells)
    affected = payload.get("affectedCells") or []
    if isinstance(affected, list):
        for item in affected:
            if not isinstance(item, dict):
                continue
            cell_coords = item.get("coords")
            if not isinstance(cell_coords, dict):
                continue
            col = int(cell_coords["column"])
            r = int(cell_coords["row"])
            if not (0 <= col <= 9 and 0 <= r <= 9):
                continue
            mark = _MARK.get(str(item.get("mark", "")), Mark.UNCHECKED)
            previous = grid[r][col]
            has_ship = previous.has_ship or mark in {Mark.HIT, Mark.SUNK}
            grid[r][col] = CellView(mark, has_ship, last_shot=False)
    if 0 <= column <= 9 and 0 <= row <= 9:
        current = grid[row][column]
        grid[row][column] = CellView(current.mark, current.has_ship, last_shot=True)
    apply_shot_to_fleets(scene, shooter, result, column, row, affected)
    scene.shots.append(ShotView(seq, shooter, column, row, result))
    scene.last_shot_seq = seq
    scene.player_turn = str(payload.get("turn", "")) == "Player"
    remain = payload.get("remainTtlSeconds")
    if isinstance(remain, int):
        scene.ttl_seconds = remain
    return True


def apply_game_over(scene: BattleScene, payload: dict[str, object]) -> bool:
    """Apply a server gameOver frame. Does not invent shooting rules."""
    winner = _SIDE.get(str(payload.get("winner", "")))
    reason = _REASON.get(str(payload.get("endReason", "")))
    if winner is None or reason is None:
        return False
    shot_count = len(scene.shots)
    seq = payload.get("seq")
    if isinstance(seq, int) and seq > shot_count:
        shot_count = seq
    scene.game_over = GameOverView(
        player_won=winner is Side.PLAYER,
        end_reason=reason,
        shot_count=shot_count,
    )
    scene.match_over = True
    scene.player_turn = False
    return True


def _clear_last_shot(grid: list[list[CellView]]) -> None:
    for row in grid:
        for cell in row:
            cell.last_shot = False
