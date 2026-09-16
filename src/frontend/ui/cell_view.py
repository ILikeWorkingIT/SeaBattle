from __future__ import annotations

from dataclasses import dataclass

from frontend.domain.types import Mark


@dataclass(slots=True)
class CellView:
    mark: Mark
    has_ship: bool = False
    last_shot: bool = False
