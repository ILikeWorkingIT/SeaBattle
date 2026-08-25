from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from frontend.mock.ledger import Snapshot
from frontend.theme import NAVY


class StatsChart(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(160)
        self._player = 0
        self._backend = 0
        self._player_label = "Player"
        self._backend_label = "Backend"

    def bind(self, snapshot: Snapshot, player_label: str, backend_label: str) -> None:
        self._player = snapshot.player_wins
        self._backend = snapshot.backend_wins
        self._player_label = player_label
        self._backend_label = backend_label
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        maximum = max(self._player, self._backend, 1)
        gap = 48
        bar_width = min(90, (width - gap * 3) / 2)
        base = height - 28
        max_h = height - 56
        bars = (
            (self._player, NAVY["gold"], self._player_label, width / 2 - bar_width - gap / 2),
            (self._backend, NAVY["teal"], self._backend_label, width / 2 + gap / 2),
        )
        for value, color, label, x in bars:
            bar_h = (value / maximum) * max_h
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), int(base - bar_h), int(bar_width), int(bar_h), 8, 8)
            painter.setPen(QColor(NAVY["text"]))
            painter.drawText(
                int(x),
                int(base - bar_h - 20),
                int(bar_width),
                18,
                Qt.AlignmentFlag.AlignCenter,
                str(value),
            )
            painter.setPen(QColor(NAVY["muted"]))
            painter.drawText(
                int(x),
                int(base + 4),
                int(bar_width),
                20,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )
        painter.end()
