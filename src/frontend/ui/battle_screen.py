from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
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
from frontend.theme import NAVY
from frontend.ui.board_widget import BoardWidget
from frontend.ui.fleet_panel import FleetPanel
from frontend.ui.shot_log import ShotLog

ChannelPhase = Literal["idle", "loading", "error", "success"]
ShotPhase = Literal["idle", "loading", "error", "empty", "success"]
SurrenderPhase = Literal["idle", "loading", "error"]


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
        self._stats_btn.setAccessibleName("battle-open-stats")
        self._stats_btn.clicked.connect(self.stats_requested.emit)
        self._surrender_btn = QPushButton()
        self._surrender_btn.setObjectName("Danger")
        self._surrender_btn.setAccessibleName("battle-surrender")
        self._surrender_btn.clicked.connect(self.surrender_requested.emit)

        self.player_board = BoardWidget()
        self.player_board.setObjectName("player-board")
        self.backend_board = BoardWidget()
        self.backend_board.setObjectName("computer-board")
        self.channel_loading = QLabel()
        self.channel_loading.setObjectName("battle-channel-loading")
        self.channel_error = QLabel()
        self.channel_error.setObjectName("battle-channel-error")
        self.shot_loading = QLabel()
        self.shot_loading.setObjectName("battle-shot-loading")
        self.shot_error = QLabel()
        self.shot_error.setObjectName("battle-shot-error")
        self.shot_empty = QLabel()
        self.shot_empty.setObjectName("battle-shot-empty")
        self.surrender_loading = QLabel()
        self.surrender_loading.setObjectName("battle-surrender-loading")
        self.surrender_error = QLabel()
        self.surrender_error.setObjectName("battle-surrender-error")
        self.computer_turn = QLabel()
        self.computer_turn.setObjectName("battle-computer-turn")
        self._aim_effect = QGraphicsOpacityEffect(self.computer_turn)
        self.computer_turn.setGraphicsEffect(self._aim_effect)
        self._aim_anim = QPropertyAnimation(self._aim_effect, b"opacity", self)
        self._aim_anim.setDuration(700)
        self._aim_anim.setStartValue(0.4)
        self._aim_anim.setEndValue(1.0)
        self._aim_anim.setLoopCount(-1)
        self._aim_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        for status in (
            self.channel_loading,
            self.channel_error,
            self.shot_loading,
            self.shot_error,
            self.shot_empty,
            self.surrender_loading,
            self.surrender_error,
            self.computer_turn,
        ):
            status.setWordWrap(True)
            status.setVisible(False)

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

        status_row = QVBoxLayout()
        status_row.addWidget(self.channel_loading)
        status_row.addWidget(self.channel_error)
        status_row.addWidget(self.shot_loading)
        status_row.addWidget(self.shot_error)
        status_row.addWidget(self.shot_empty)
        status_row.addWidget(self.surrender_loading)
        status_row.addWidget(self.surrender_error)
        status_row.addWidget(self.computer_turn)

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
        layout.addLayout(status_row)
        layout.addLayout(body, 1)

    def bind_scene(self, i18n: I18n, language: Language, scene: BattleScene) -> None:
        self.retranslate(i18n)
        self.player_board.set_language(language)
        self.backend_board.set_language(language)
        self.player_board.set_cells(scene.player_cells)
        self.backend_board.set_cells(scene.backend_cells)
        player_turn = scene.player_turn
        self._turn_badge.setText(i18n.t("turn_player" if player_turn else "turn_backend"))
        accent = NAVY["gold"] if player_turn else NAVY["teal"]
        self._turn_badge.setStyleSheet(f"color: {accent};")
        self._session_btn.setText(f"{i18n.t('session')}  {scene.session_id[:8]}")
        self._player_fleet.bind(i18n, i18n.t("fleet_player"), scene.player_ships)
        self._backend_fleet.bind(i18n, i18n.t("fleet_backend"), scene.backend_ships)
        self._log.bind(i18n, language, scene.shots)
        seconds = scene.ttl_seconds
        self._ttl_bar.setValue(seconds)
        minutes, secs = divmod(seconds, 60)
        self._ttl_label.setText(f"{minutes:02d}:{secs:02d}")
        self.set_surrender_enabled(not scene.match_over)

    def apply_channel_phase(self, i18n: I18n, phase: ChannelPhase, error: str) -> None:
        self.channel_loading.setText(i18n.t("channel_connecting"))
        self.channel_error.setText(error)
        self.channel_loading.setVisible(phase == "loading")
        self.channel_error.setVisible(phase == "error")

    def apply_shot_phase(self, i18n: I18n, phase: ShotPhase, error: str) -> None:
        self.shot_loading.setText(i18n.t("busy"))
        self.shot_empty.setText(i18n.t("shot_empty"))
        self.shot_error.setText(error)
        self.shot_loading.setVisible(phase == "loading")
        self.shot_error.setVisible(phase == "error")
        self.shot_empty.setVisible(phase == "empty")

    def apply_surrender_phase(self, i18n: I18n, phase: SurrenderPhase, error: str) -> None:
        self.surrender_loading.setText(i18n.t("surrendering"))
        self.surrender_error.setText(error)
        self.surrender_loading.setVisible(phase == "loading")
        self.surrender_error.setVisible(phase == "error")

    def set_surrender_enabled(self, enabled: bool) -> None:
        self._surrender_btn.setEnabled(enabled)

    def apply_computer_turn(self, i18n: I18n, active: bool) -> None:
        self.computer_turn.setText(i18n.t("aiming"))
        self.computer_turn.setVisible(active)
        running = self._aim_anim.state() == QAbstractAnimation.State.Running
        if active and not running:
            self._aim_anim.start()
        if not active and running:
            self._aim_anim.stop()
            self._aim_effect.setOpacity(1.0)

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
        self.channel_loading.setText(i18n.t("channel_connecting"))
        self.shot_loading.setText(i18n.t("busy"))
        self.shot_empty.setText(i18n.t("shot_empty"))
        self.surrender_loading.setText(i18n.t("surrendering"))
        self.computer_turn.setText(i18n.t("aiming"))
