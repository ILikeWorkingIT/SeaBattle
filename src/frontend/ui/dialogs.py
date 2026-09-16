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

from frontend.domain.types import EndReason, Side
from frontend.i18n import I18n
from frontend.mock.static_scene import GameOverView, Snapshot
from frontend.ui.stats_chart import StatsChart


class SurrenderDialog(QDialog):
    confirmed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(420)
        self._title = QLabel()
        self._title.setObjectName("Hero")
        self._title.setStyleSheet("font-size: 22px;")
        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setObjectName("Lead")
        self._yes = QPushButton()
        self._yes.setObjectName("Danger")
        self._no = QPushButton()
        self._no.setObjectName("Ghost")
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
        self.setModal(True)
        self.setMinimumWidth(440)
        self._kicker = QLabel()
        self._kicker.setObjectName("Kicker")
        self._title = QLabel()
        self._title.setObjectName("Hero")
        self._title.setStyleSheet("font-size: 28px;")
        self._reason = QLabel()
        self._shots = QLabel()
        self._new = QPushButton()
        self._new.setObjectName("Primary")
        self._stats = QPushButton()
        self._close = QPushButton()
        self._close.setObjectName("Ghost")
        self._new.clicked.connect(self._emit_new)
        self._stats.clicked.connect(self._emit_stats)
        self._close.clicked.connect(self._emit_close)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.addWidget(self._kicker)
        layout.addWidget(self._title)
        layout.addWidget(self._reason)
        layout.addWidget(self._shots)
        row = QHBoxLayout()
        row.addWidget(self._new)
        row.addWidget(self._stats)
        row.addWidget(self._close)
        layout.addLayout(row)

    def present(self, i18n: I18n, view: GameOverView) -> None:
        self.next_action = None
        self.setWindowTitle(i18n.t("game_over"))
        self._kicker.setText(i18n.t("game_over"))
        self._title.setText(i18n.t("you_won" if view.player_won else "you_lost"))
        reason = (
            i18n.t("reason_surrender")
            if view.end_reason is EndReason.SURRENDER
            else i18n.t("reason_fleet")
        )
        self._reason.setText(reason)
        self._shots.setText(i18n.t("shots_count", n=view.shot_count))
        self._new.setText(i18n.t("new_game"))
        self._stats.setText(i18n.t("open_stats"))
        self._close.setText(i18n.t("close"))

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
        self._kpis = QHBoxLayout()
        self._kpi_labels: list[tuple[QLabel, QLabel]] = []
        for _ in range(4):
            card, caption, value = _kpi_card()
            self._kpis.addWidget(card)
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
        self._refresh.clicked.connect(lambda: None)
        self._close = QPushButton()
        self._close.setObjectName("Ghost")
        self._close.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
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
        self._table_title.setText(i18n.t("stats_table"))
        self._table.setHorizontalHeaderLabels(
            [i18n.t("col_id"), i18n.t("col_winner"), i18n.t("col_shots"), i18n.t("col_reason")]
        )
        self._refresh.setText(i18n.t("refresh"))
        self._close.setText(i18n.t("close"))

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
            f"{snapshot.avg_shots:.1f}",
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


def _kpi_card() -> tuple[QFrame, QLabel, QLabel]:
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    caption = QLabel()
    caption.setObjectName("CardTitle")
    value = QLabel("0")
    value.setObjectName("CardValue")
    layout.addWidget(caption)
    layout.addWidget(value)
    return card, caption, value
