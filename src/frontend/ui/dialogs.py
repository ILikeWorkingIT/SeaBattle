from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.client.statistics import format_avg_shots
from frontend.domain.types import EndReason, Side
from frontend.i18n import I18n
from frontend.mock.static_scene import GameOverView, Snapshot
from frontend.ui.lobby_screen import StatsPhase
from frontend.ui.stats_chart import StatsChart


class SurrenderDialog(QDialog):
    confirmed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setObjectName("surrender-dialog")
        self._title = QLabel()
        self._title.setObjectName("Hero")
        self._title.setStyleSheet("font-size: 22px;")
        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setObjectName("Lead")
        self._yes = QPushButton()
        self._yes.setObjectName("Danger")
        self._yes.setAccessibleName("surrender-confirm")
        self._no = QPushButton()
        self._no.setObjectName("Ghost")
        self._no.setAccessibleName("surrender-cancel")
        self._yes.clicked.connect(self._accept)
        self._no.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(self._title)
        layout.addWidget(self._body)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self._no)
        row.addWidget(self._yes)
        layout.addLayout(row)

    def retranslate(self, i18n: I18n) -> None:
        self.setWindowTitle(i18n.t("surrender_title"))
        self._title.setText(i18n.t("surrender_title"))
        self._body.setText(i18n.t("surrender_body"))
        self._yes.setText(i18n.t("confirm"))
        self._no.setText(i18n.t("cancel"))

    def _accept(self) -> None:
        self.confirmed.emit()
        self.accept()


class GameOverDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.next_action: str | None = None
        self._view: GameOverView | None = None
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setObjectName("game-over-dialog")
        self._kicker = QLabel()
        self._kicker.setObjectName("Kicker")
        self.winner_label = QLabel()
        self.winner_label.setObjectName("Hero")
        self.winner_label.setAccessibleName("game-over-winner")
        self.winner_label.setStyleSheet("font-size: 28px;")
        self.reason_label = QLabel()
        self.reason_label.setObjectName("game-over-reason")
        self.shots_label = QLabel()
        self.shots_label.setObjectName("game-over-shots")
        self.new_button = QPushButton()
        self.new_button.setObjectName("Primary")
        self.new_button.setAccessibleName("game-over-new-match")
        self.stats_button = QPushButton()
        self.stats_button.setObjectName("Ghost")
        self.stats_button.setAccessibleName("game-over-open-stats")
        self.close_button = QPushButton()
        self.close_button.setObjectName("Ghost")
        self.close_button.setAccessibleName("game-over-close")
        self.new_button.clicked.connect(self._emit_new)
        self.stats_button.clicked.connect(self._emit_stats)
        self.close_button.clicked.connect(self._emit_close)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.addWidget(self._kicker)
        layout.addWidget(self.winner_label)
        layout.addWidget(self.reason_label)
        layout.addWidget(self.shots_label)
        row = QHBoxLayout()
        row.addWidget(self.new_button)
        row.addWidget(self.stats_button)
        row.addWidget(self.close_button)
        layout.addLayout(row)

    def present(self, i18n: I18n, view: GameOverView) -> None:
        self.next_action = None
        self._view = view
        self.retranslate(i18n)

    def retranslate(self, i18n: I18n) -> None:
        view = self._view
        if view is None:
            self.setWindowTitle(i18n.t("game_over"))
            self._kicker.setText(i18n.t("game_over"))
            self.new_button.setText(i18n.t("new_game"))
            self.stats_button.setText(i18n.t("open_stats"))
            self.close_button.setText(i18n.t("close"))
            return
        self.setWindowTitle(i18n.t("game_over"))
        self._kicker.setText(i18n.t("game_over"))
        self.winner_label.setText(i18n.t("you_won" if view.player_won else "you_lost"))
        reason = (
            i18n.t("reason_surrender")
            if view.end_reason is EndReason.SURRENDER
            else i18n.t("reason_fleet")
        )
        self.reason_label.setText(reason)
        self.shots_label.setText(i18n.t("shots_count", n=view.shot_count))
        self.new_button.setText(i18n.t("new_game"))
        self.stats_button.setText(i18n.t("open_stats"))
        self.close_button.setText(i18n.t("close"))

    def _emit_new(self) -> None:
        self.next_action = "new"
        self.accept()

    def _emit_stats(self) -> None:
        self.next_action = "stats"
        self.accept()

    def _emit_close(self) -> None:
        self.next_action = None
        self.accept()


class StatsDialog(QDialog):
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.resize(720, 560)
        self._title = QLabel()
        self._title.setObjectName("Hero")
        self._title.setStyleSheet("font-size: 24px;")
        self._hint = QLabel()
        self._hint.setObjectName("Lead")
        self._hint.setWordWrap(True)
        self._empty = QLabel()
        self._empty.setObjectName("stats-empty")
        self._empty.setWordWrap(True)
        self._empty.setVisible(False)
        self._loading = QLabel()
        self._loading.setObjectName("stats-loading")
        self._loading.setWordWrap(True)
        self._loading.setVisible(False)
        self._error = QLabel()
        self._error.setObjectName("stats-error")
        self._error.setWordWrap(True)
        self._error.setVisible(False)
        self._kpis = QHBoxLayout()
        self._kpi_cards: list[QFrame] = []
        self._kpi_labels: list[tuple[QLabel, QLabel]] = []
        names = ("dialog-kpi-games", "dialog-kpi-player-wins", "dialog-kpi-computer-wins", "dialog-kpi-avg-shots")
        for name in names:
            card, caption, value = _kpi_card(name)
            self._kpis.addWidget(card)
            self._kpi_cards.append(card)
            self._kpi_labels.append((caption, value))
        self._chart = StatsChart()
        self._table_title = QLabel()
        self._table = QTableWidget(0, 4)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._refresh = QPushButton()
        self._refresh.setObjectName("Ghost")
        self._refresh.setAccessibleName("stats-refresh")
        self._refresh.clicked.connect(self.refresh_requested.emit)
        self.refresh_button = self._refresh
        self._close = QPushButton()
        self._close.setObjectName("Ghost")
        self._close.setAccessibleName("stats-close")
        self._close.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._empty)
        layout.addWidget(self._loading)
        layout.addWidget(self._error)
        layout.addLayout(self._kpis)
        layout.addWidget(self._chart)
        layout.addWidget(self._table_title)
        layout.addWidget(self._table, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self._refresh)
        row.addWidget(self._close)
        layout.addLayout(row)

    def retranslate(self, i18n: I18n) -> None:
        self.setWindowTitle(i18n.t("stats_title"))
        self._title.setText(i18n.t("stats_title"))
        self._hint.setText(i18n.t("stats_hint"))
        self._empty.setText(i18n.t("stats_empty"))
        self._loading.setText(i18n.t("stats_loading"))
        self._table_title.setText(i18n.t("stats_table"))
        self._table.setHorizontalHeaderLabels(
            [i18n.t("col_id"), i18n.t("col_winner"), i18n.t("col_shots"), i18n.t("col_reason")]
        )
        self._refresh.setText(i18n.t("refresh"))
        self._close.setText(i18n.t("close"))

    def apply_stats_phase(self, i18n: I18n, phase: StatsPhase, error_text: str) -> None:
        self.retranslate(i18n)
        self._error.setText(error_text)
        self._empty.setVisible(phase == "empty")
        self._loading.setVisible(phase == "loading")
        self._error.setVisible(phase == "error")
        show_data = phase in {"idle", "empty", "success"}
        for card in self._kpi_cards:
            card.setVisible(show_data)
        self._chart.setVisible(show_data)
        self._table_title.setVisible(show_data)
        self._table.setVisible(show_data)
        self._refresh.setEnabled(phase != "loading")

    def bind(self, i18n: I18n, snapshot: Snapshot) -> None:
        self.retranslate(i18n)
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
            format_avg_shots(snapshot.avg_shots),
        )
        for (caption, value_label), text, amount in zip(self._kpi_labels, captions, values):
            caption.setText(text)
            value_label.setText(amount)
        self._chart.bind(snapshot, i18n.t("side_player"), i18n.t("side_backend"))
        recent = list(reversed(snapshot.records[-12:]))
        self._table.setRowCount(len(recent))
        for row, record in enumerate(recent):
            winner = i18n.t("side_player" if record.winner is Side.PLAYER else "side_backend")
            reason = (
                i18n.t("reason_surrender")
                if record.end_reason is EndReason.SURRENDER
                else i18n.t("reason_fleet")
            )
            cells = (record.session_id[:8], winner, str(record.shots), reason)
            for column, text in enumerate(cells):
                self._table.setItem(row, column, QTableWidgetItem(text))


def _kpi_card(value_name: str) -> tuple[QFrame, QLabel, QLabel]:
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    caption = QLabel()
    caption.setObjectName("CardTitle")
    value = QLabel("0")
    value.setObjectName("CardValue")
    value.setAccessibleName(value_name)
    layout.addWidget(caption)
    layout.addWidget(value)
    return card, caption, value
