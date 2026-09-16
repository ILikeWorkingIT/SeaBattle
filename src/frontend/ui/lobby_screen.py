from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from frontend.domain.types import SHIP_LENGTH, FLEET_SPEC, ShipType
from frontend.i18n import I18n
from frontend.mock.static_scene import Snapshot


class LobbyScreen(QWidget):
    start_requested = Signal()
    stats_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._kicker = QLabel()
        self._kicker.setObjectName("Kicker")
        self._title = QLabel()
        self._title.setObjectName("Hero")
        self._lead = QLabel()
        self._lead.setObjectName("Lead")
        self._lead.setWordWrap(True)
        self._mode = QLabel()
        self._mode.setObjectName("Kicker")
        self._start = QPushButton()
        self._start.setObjectName("Primary")
        self._start.clicked.connect(self.start_requested.emit)
        self._stats = QPushButton()
        self._stats.setObjectName("Ghost")
        self._stats.clicked.connect(self.stats_requested.emit)
        self._slots = QLabel()
        self._slots.setObjectName("Muted")
        self._kpis = QHBoxLayout()
        self._kpi_widgets: list[tuple[QLabel, QLabel]] = []
        for _ in range(4):
            card, caption, value = _metric_card()
            self._kpis.addWidget(card)
            self._kpi_widgets.append((caption, value))

        self._tabs = QTabWidget()
        self._fleet_tab = QWidget()
        self._rules_tab = QWidget()
        self._fleet_grid = QGridLayout(self._fleet_tab)
        self._fleet_grid.setContentsMargins(16, 16, 16, 16)
        self._fleet_caption = QLabel()
        self._fleet_caption.setObjectName("Muted")
        self._fleet_caption.setWordWrap(True)
        self._rules_layout = QVBoxLayout(self._rules_tab)
        self._rules_layout.setContentsMargins(16, 16, 16, 16)
        self._rule_labels = [QLabel() for _ in range(3)]
        for label in self._rule_labels:
            label.setWordWrap(True)
            self._rules_layout.addWidget(label)
        self._rules_layout.addStretch(1)
        self._tabs.addTab(self._fleet_tab, "")
        self._tabs.addTab(self._rules_tab, "")

        header = QVBoxLayout()
        header.addWidget(self._kicker)
        header.addWidget(self._title)
        header.addWidget(self._lead)
        badge_row = QHBoxLayout()
        badge_row.addWidget(self._mode)
        badge_row.addStretch(1)
        header.addLayout(badge_row)

        actions = QHBoxLayout()
        actions.addWidget(self._start)
        actions.addWidget(self._stats)
        actions.addStretch(1)
        actions.addWidget(self._slots, 0, Qt.AlignmentFlag.AlignVCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.addLayout(header)
        layout.addLayout(actions)
        layout.addLayout(self._kpis)
        layout.addWidget(self._tabs, 1)

        self._fleet_rows: list[tuple[QLabel, QLabel]] = []

    def set_busy(self, busy: bool, i18n: I18n) -> None:
        self._start.setEnabled(not busy)
        self._start.setText(i18n.t("starting") if busy else i18n.t("start_game"))

    def bind(self, i18n: I18n, snapshot: Snapshot, used_slots: int) -> None:
        self._kicker.setText(i18n.t("lobby_kicker"))
        self._title.setText(i18n.t("lobby_title"))
        self._lead.setText(i18n.t("lobby_lead"))
        self._mode.setText(i18n.t("mode_pve"))
        self._start.setText(i18n.t("start_game"))
        self._stats.setText(i18n.t("open_stats"))
        self._slots.setText(i18n.t("slots_value", used=used_slots, limit=3))
        captions = (
            i18n.t("kpi_games"),
            i18n.t("kpi_player"),
            i18n.t("kpi_backend"),
            i18n.t("kpi_avg"),
        )
        values = (
            str(snapshot.games),
            str(snapshot.player_wins),
            str(snapshot.backend_wins),
            f"{snapshot.avg_shots:.1f}",
        )
        for (caption, value), text, amount in zip(self._kpi_widgets, captions, values):
            caption.setText(text)
            value.setText(amount)
        self._tabs.setTabText(0, i18n.t("fleet_title"))
        self._tabs.setTabText(1, i18n.t("rules_title"))
        self._fleet_caption.setText(i18n.t("fleet_rule"))
        self._bind_fleet(i18n)
        for label, key in zip(
            self._rule_labels,
            ("rule_1", "rule_2", "rule_3"),
        ):
            label.setText("• " + i18n.t(key))

    def _bind_fleet(self, i18n: I18n) -> None:
        leftover: list = []
        while self._fleet_grid.count():
            item = self._fleet_grid.takeAt(0)
            widget = item.widget()
            if widget is None or widget is self._fleet_caption:
                continue
            leftover.append(widget)
        for widget in leftover:
            widget.deleteLater()
        self._fleet_grid.addWidget(self._fleet_caption, 0, 0, 1, 2)
        counts = {
            ShipType.BATTLESHIP: FLEET_SPEC.count(ShipType.BATTLESHIP),
            ShipType.CRUISER: FLEET_SPEC.count(ShipType.CRUISER),
            ShipType.DESTROYER: FLEET_SPEC.count(ShipType.DESTROYER),
            ShipType.BOAT: FLEET_SPEC.count(ShipType.BOAT),
        }
        names = {
            ShipType.BATTLESHIP: i18n.t("battleship"),
            ShipType.CRUISER: i18n.t("cruiser"),
            ShipType.DESTROYER: i18n.t("destroyer"),
            ShipType.BOAT: i18n.t("boat"),
        }
        for row, ship_type in enumerate(counts, start=1):
            name = QLabel(names[ship_type])
            bars = "█" * SHIP_LENGTH[ship_type]
            meta = QLabel(f"{counts[ship_type]} × {bars}  ({SHIP_LENGTH[ship_type]})")
            meta.setObjectName("Muted")
            self._fleet_grid.addWidget(name, row, 0)
            self._fleet_grid.addWidget(meta, row, 1)


def _metric_card() -> tuple[QFrame, QLabel, QLabel]:
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    caption = QLabel()
    caption.setObjectName("CardTitle")
    value = QLabel("0")
    value.setObjectName("CardValue")
    layout.addWidget(caption)
    layout.addWidget(value)
    return card, caption, value
