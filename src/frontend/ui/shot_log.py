from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from frontend.domain.session import Shot
from frontend.domain.types import Language, Side, display_coord
from frontend.i18n import I18n


class ShotLog(QTableWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 4, parent)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def retranslate(self, i18n: I18n) -> None:
        self.setHorizontalHeaderLabels(
            [i18n.t("log_seq"), i18n.t("log_shooter"), i18n.t("log_cell"), i18n.t("log_result")]
        )

    def bind(self, i18n: I18n, language: Language, shots: list[Shot]) -> None:
        self.retranslate(i18n)
        self.setRowCount(len(shots))
        for index, shot in enumerate(reversed(shots)):
            shooter = i18n.t("side_player" if shot.shooter is Side.PLAYER else "side_backend")
            cell = display_coord(shot.coords, language).text()
            values = (str(shot.seq), shooter, cell, shot.result.value)
            for column, value in enumerate(values):
                self.setItem(index, column, QTableWidgetItem(value))
        if shots:
            self.scrollToTop()
