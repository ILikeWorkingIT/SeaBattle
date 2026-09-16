from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from frontend.domain.types import Language
from frontend.i18n import I18n
from frontend.mock.static_scene import BattleScene
from frontend.ui.board_widget import BoardWidget
from frontend.ui.fleet_panel import FleetPanel
from frontend.ui.shot_log import ShotLog


class BattleScreen(QWidget):
    surrender_requested = Signal()
    stats_requested = Signal()
    copy_session = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._turn_badge = QLabel()
        self._turn_badge.setObjectName("Kicker")
        self._ttl_label = QLabel()
        self._ttl_bar = QProgressBar()
        self._ttl_bar.setRange(0, 30 * 60)
        self._ttl_bar.setTextVisible(False)
        self._ttl_bar.setFixedWidth(140)
        self._ttl_bar.setFixedHeight(8)
        self._session_btn = QPushButton()
        self._session_btn.setObjectName("Ghost")
        self._session_btn.clicked.connect(self.copy_session.emit)
        self._stats_btn = QPushButton()
        self._stats_btn.setObjectName("Ghost")
        self._stats_btn.clicked.connect(self.stats_requested.emit)
        self._surrender_btn = QPushButton()
        self._surrender_btn.setObjectName("Danger")
        self._surrender_btn.clicked.connect(self.surrender_requested.emit)

        self.player_board = BoardWidget()
        self.backend_board = BoardWidget()

        self._legend_hit = QLabel()
        self._legend_sunk = QLabel()
        self._legend_miss = QLabel()
        for label in (self._legend_hit, self._legend_sunk, self._legend_miss):
            label.setObjectName("Muted")

        self._tabs = QTabWidget()
        self._player_fleet = FleetPanel()
        self._backend_fleet = FleetPanel()
        fleet_wrap = QWidget()
        fleet_layout = QVBoxLayout(fleet_wrap)
        fleet_layout.addWidget(self._player_fleet)
        fleet_layout.addWidget(self._backend_fleet)
        self._log = ShotLog()
        self._tabs.addTab(fleet_wrap, "")
        self._tabs.addTab(self._log, "")

        top = QHBoxLayout()
        ttl_box = QVBoxLayout()
        ttl_caption = QHBoxLayout()
        self._ttl_caption = QLabel()
        self._ttl_caption.setObjectName("Muted")
        ttl_caption.addWidget(self._ttl_caption)
        ttl_caption.addWidget(self._ttl_label)
        ttl_box.addLayout(ttl_caption)
        ttl_box.addWidget(self._ttl_bar)
        top.addWidget(self._turn_badge)
        top.addStretch(1)
        top.addLayout(ttl_box)
        top.addWidget(self._session_btn)
        top.addWidget(self._stats_btn)
        top.addWidget(self._surrender_btn)

        boards = QHBoxLayout()
        boards.addWidget(self.player_board, 1)
        boards.addWidget(self.backend_board, 1)

        legend = QHBoxLayout()
        legend.addWidget(self._legend_hit)
        legend.addWidget(self._legend_sunk)
        legend.addWidget(self._legend_miss)
        legend.addStretch(1)

        side = QFrame()
        side.setObjectName("Panel")
        side.setFixedWidth(320)
        side_layout = QVBoxLayout(side)
        side_layout.addWidget(self._tabs)

        body = QHBoxLayout()
        left = QVBoxLayout()
        left.addLayout(boards, 1)
        left.addLayout(legend)
        body.addLayout(left, 1)
        body.addWidget(side)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.addLayout(top)
        layout.addLayout(body, 1)

    def bind_scene(self, i18n: I18n, language: Language, scene: BattleScene) -> None:
        self.retranslate(i18n)
        self.player_board.set_language(language)
        self.backend_board.set_language(language)
        self.player_board.set_cells(scene.player_cells)
        self.backend_board.set_cells(scene.backend_cells)
        player_turn = scene.player_turn
        self._turn_badge.setText(i18n.t("turn_player" if player_turn else "turn_backend"))
        self._turn_badge.setStyleSheet(
            "color: #E0B14A;" if player_turn else "color: #3EC8B0;"
        )
        self._session_btn.setText(f"{i18n.t('session')}  {scene.session_id[:8]}")
        self._player_fleet.bind(i18n, i18n.t("fleet_player"), scene.player_ships)
        self._backend_fleet.bind(i18n, i18n.t("fleet_backend"), scene.backend_ships)
        self._log.bind(i18n, language, scene.shots)
        seconds = scene.ttl_seconds
        self._ttl_bar.setValue(seconds)
        minutes, secs = divmod(seconds, 60)
        self._ttl_label.setText(f"{minutes:02d}:{secs:02d}")

    def retranslate(self, i18n: I18n) -> None:
        self._ttl_caption.setText(i18n.t("ttl"))
        self._stats_btn.setText(i18n.t("open_stats"))
        self._surrender_btn.setText(i18n.t("surrender"))
        self._legend_hit.setText(i18n.t("legend_hit"))
        self._legend_sunk.setText(i18n.t("legend_sunk"))
        self._legend_miss.setText(i18n.t("legend_miss"))
        self._tabs.setTabText(0, i18n.t("fleet_title"))
        self._tabs.setTabText(1, i18n.t("shots"))
        self.player_board.set_title(i18n.t("board_player"))
        self.backend_board.set_title(i18n.t("board_backend"))
