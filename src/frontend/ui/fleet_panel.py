from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from frontend.domain.types import ShipStatus, ShipType
from frontend.i18n import I18n
from frontend.mock.static_scene import ShipView
from frontend.theme import NAVY


class FleetPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = QLabel()
        self._title.setObjectName("CardTitle")
        self._rows = QVBoxLayout()
        self._rows.setSpacing(6)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._title)
        layout.addLayout(self._rows)
        layout.addStretch(1)

    def bind(self, i18n: I18n, title: str, ships: list[ShipView]) -> None:
        self._title.setText(title)
        while self._rows.count():
            item = self._rows.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for ship in ships:
            self._rows.addWidget(_ShipRow(i18n, ship))


class _ShipRow(QFrame):
    def __init__(self, i18n: I18n, ship: ShipView) -> None:
        super().__init__()
        gold = NAVY["gold"]
        self.setStyleSheet(
            f"background: #0B1C28; border: 1px solid #1B3A4C; border-radius: 8px; color: {gold};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        name = {
            ShipType.BATTLESHIP: i18n.t("battleship"),
            ShipType.CRUISER: i18n.t("cruiser"),
            ShipType.DESTROYER: i18n.t("destroyer"),
            ShipType.BOAT: i18n.t("boat"),
        }[ship.type]
        status_text = {
            ShipStatus.INTACT: i18n.t("status_intact"),
            ShipStatus.WOUNDED: i18n.t("status_wounded"),
            ShipStatus.SUNK: i18n.t("status_sunk"),
        }[ship.status]
        bars: list[str] = []
        for hit in ship.decks_hit:
            if ship.hide_intact_bars and ship.status is ShipStatus.INTACT:
                bars.append("□")
            elif hit or ship.status is ShipStatus.SUNK:
                bars.append("■")
            else:
                bars.append("□")
        bar_text = "".join(bars)
        left = QLabel(bar_text if not ship.type_known else f"{name}  {bar_text}")
        right = QLabel(status_text)
        color = {
            ShipStatus.INTACT: "#8FAABB",
            ShipStatus.WOUNDED: "#E0B14A",
            ShipStatus.SUNK: "#E05A5A",
        }[ship.status]
        right.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        left.setStyleSheet(f"color: {gold}; border: none; background: transparent;")
        layout.addWidget(left)
        layout.addStretch(1)
        layout.addWidget(right, 0, Qt.AlignmentFlag.AlignRight)
