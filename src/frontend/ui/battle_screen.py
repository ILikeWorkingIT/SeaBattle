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

from frontend.domain.session import Session, ShotOutcome
from frontend.domain.types import Language, Mark, Side
from frontend.i18n import I18n
from frontend.ui.board_widget import BoardWidget, CellView
from frontend.ui.fleet_panel import FleetPanel
from frontend.ui.shot_log import ShotLog


class BattleScreen(QWidget):
    player_shot = Signal(int, int)
    own_board_clicked = Signal()
    surrender_requested = Signal()
    stats_requested = Signal()
    copy_session = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._language = Language.RU
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
        self._aiming = QLabel()
        self._aiming.setObjectName("Kicker")
        self._aiming.hide()

        self.player_board = BoardWidget()
        self.backend_board = BoardWidget()
        self.backend_board.interactive = True
        self.player_board.cell_clicked.connect(lambda *_: self.own_board_clicked.emit())
        self.backend_board.cell_clicked.connect(self.player_shot.emit)

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
        top.addWidget(self._aiming)
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

    def retranslate(self, i18n: I18n) -> None:
        self._ttl_caption.setText(i18n.t("ttl"))
        self._stats_btn.setText(i18n.t("open_stats"))
        self._surrender_btn.setText(i18n.t("surrender"))
        self._aiming.setText(i18n.t("aiming"))
        self._legend_hit.setText(i18n.t("legend_hit"))
        self._legend_sunk.setText(i18n.t("legend_sunk"))
        self._legend_miss.setText(i18n.t("legend_miss"))
        self._tabs.setTabText(0, i18n.t("fleet_title"))
        self._tabs.setTabText(1, i18n.t("shots"))
        self.player_board.set_title(i18n.t("board_player"))
        self.backend_board.set_title(i18n.t("board_backend"))

    def bind_session(self, i18n: I18n, language: Language, session: Session, last: ShotOutcome | None) -> None:
        self._language = language
        self.retranslate(i18n)
        self.player_board.set_language(language)
        self.backend_board.set_language(language)
        last_player = last.shot.coords if last and last.shot.shooter is Side.PLAYER else None
        last_backend = last.shot.coords if last and last.shot.shooter is Side.BACKEND else None
        self.player_board.set_cells(_views(session, Side.PLAYER, last_backend, reveal_ships=True))
        self.backend_board.set_cells(_views(session, Side.BACKEND, last_player, reveal_ships=False))
        self.backend_board.interactive = session.turn is Side.PLAYER
        player_turn = session.turn is Side.PLAYER
        self._turn_badge.setText(i18n.t("turn_player" if player_turn else "turn_backend"))
        self._turn_badge.setStyleSheet(
            "color: #E0B14A;" if player_turn else "color: #3EC8B0;"
        )
        self._surrender_btn.setEnabled(True)
        self._session_btn.setText(f"{i18n.t('session')}  {session.id[:8]}")
        self._player_fleet.bind(i18n, i18n.t("fleet_player"), session.player_fleet, False)
        self._backend_fleet.bind(i18n, i18n.t("fleet_backend"), session.backend_fleet, True)
        self._log.bind(i18n, language, session.shots)
        self.update_ttl(session)

    def update_ttl(self, session: Session) -> None:
        remain = session.remain_ttl()
        seconds = int(remain.total_seconds())
        self._ttl_bar.setValue(seconds)
        minutes, secs = divmod(seconds, 60)
        self._ttl_label.setText(f"{minutes:02d}:{secs:02d}")

    def set_aiming(self, aiming: bool) -> None:
        self._aiming.setVisible(aiming)
        self.player_board.set_aiming(aiming)
        self.backend_board.interactive = not aiming


def _views(
    session: Session,
    owner: Side,
    last,
    reveal_ships: bool,
) -> list[list[CellView]]:
    board = session.board_for(owner)
    grid: list[list[CellView]] = []
    for row in range(10):
        line: list[CellView] = []
        for col in range(10):
            cell = board.cell(col, row)
            show_ship = bool(cell.occupancy_ship) and (
                reveal_ships or cell.mark in {Mark.HIT, Mark.SUNK}
            )
            last_shot = last is not None and last.column == col and last.row == row
            line.append(CellView(cell.mark, show_ship, last_shot))
        grid.append(line)
    return grid
