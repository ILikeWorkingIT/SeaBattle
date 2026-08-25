from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QRect, QVariantAnimation, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from frontend.domain.types import Language, Mark, glyph_for, letters_for
from frontend.theme import NAVY


@dataclass(slots=True)
class CellView:
    mark: Mark
    has_ship: bool = False
    last_shot: bool = False


class BoardWidget(QWidget):
    cell_clicked = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self.setMouseTracking(True)
        self.language = Language.RU
        self.interactive = False
        self.aiming = False
        self.title = ""
        self._cells: list[list[CellView]] = [
            [CellView(Mark.UNCHECKED) for _ in range(10)] for _ in range(10)
        ]
        self._hover: tuple[int, int] | None = None
        self._pulse = 0.0
        self._scan = 0.0
        self._pulse_anim = QVariantAnimation(self)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setDuration(900)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.valueChanged.connect(self._on_pulse)
        self._scan_anim = QVariantAnimation(self)
        self._scan_anim.setStartValue(0.0)
        self._scan_anim.setEndValue(1.0)
        self._scan_anim.setDuration(720)
        self._scan_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._scan_anim.valueChanged.connect(self._on_scan)

    def set_title(self, title: str) -> None:
        self.title = title
        self.update()

    def set_language(self, language: Language) -> None:
        self.language = language
        self.update()

    def set_cells(self, cells: list[list[CellView]]) -> None:
        self._cells = cells
        self.update()
        if any(cell.last_shot for row in cells for cell in row):
            if self._pulse_anim.state() != QVariantAnimation.State.Running:
                self._pulse_anim.start()
        else:
            self._pulse_anim.stop()
            self._pulse = 0.0

    def set_aiming(self, aiming: bool) -> None:
        self.aiming = aiming
        if aiming:
            self._scan_anim.stop()
            self._scan_anim.start()
        else:
            self._scan_anim.stop()
            self._scan = 0.0
        self.update()

    def _on_pulse(self, value: object) -> None:
        self._pulse = float(value)
        self.update()

    def _on_scan(self, value: object) -> None:
        self._scan = float(value)
        self.update()

    def _geometry(self) -> tuple[float, float, float, QRect]:
        width, height = self.width(), self.height()
        top = 28 if self.title else 8
        size = min((width - 36) / 11, (height - top - 12) / 11)
        origin_x = (width - size * 11) / 2 + size
        origin_y = top + size
        return origin_x, origin_y, size, QRect(int(origin_x), int(origin_y), int(size * 10), int(size * 10))

    def _cell_at(self, x: int, y: int) -> tuple[int, int] | None:
        origin_x, origin_y, size, _ = self._geometry()
        if size <= 0:
            return None
        col = int((x - origin_x) / size)
        row = int((y - origin_y) / size)
        if 0 <= col <= 9 and 0 <= row <= 9:
            return col, row
        return None

    def mouseMoveEvent(self, event) -> None:
        self._hover = self._cell_at(int(event.position().x()), int(event.position().y()))
        self.update()

    def leaveEvent(self, event) -> None:
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        cell = self._cell_at(int(event.position().x()), int(event.position().y()))
        if cell is not None:
            self.cell_clicked.emit(cell[0], cell[1])

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        origin_x, origin_y, size, _ = self._geometry()
        if self.title:
            painter.setPen(QColor(NAVY["muted"]))
            font = QFont(self.font())
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRect(0, 4, self.width(), 22), Qt.AlignmentFlag.AlignHCenter, self.title)

        letters = letters_for(self.language)
        label_font = QFont(self.font())
        label_font.setPointSize(9)
        painter.setFont(label_font)
        painter.setPen(QColor(NAVY["muted"]))
        for index, letter in enumerate(letters):
            rect = QRect(int(origin_x + index * size), int(origin_y - size), int(size), int(size))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, letter)
        for index in range(10):
            rect = QRect(int(origin_x - size), int(origin_y + index * size), int(size), int(size))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(index + 1))

        for row in range(10):
            for col in range(10):
                self._paint_cell(painter, col, row, origin_x, origin_y, size)

        if self.aiming:
            y = origin_y + self._scan * size * 10
            painter.setPen(QPen(QColor(62, 200, 176, 180), 2))
            painter.drawLine(int(origin_x), int(y), int(origin_x + size * 10), int(y))

        painter.end()

    def _paint_cell(
        self,
        painter: QPainter,
        col: int,
        row: int,
        origin_x: float,
        origin_y: float,
        size: float,
    ) -> None:
        view = self._cells[row][col]
        rect = QRect(
            int(origin_x + col * size) + 2,
            int(origin_y + row * size) + 2,
            int(size) - 4,
            int(size) - 4,
        )
        fill = QColor(NAVY["water"])
        if view.has_ship and view.mark is not Mark.SUNK:
            fill = QColor(NAVY["ship"])
        if view.mark is Mark.SUNK:
            fill = QColor("#3A1C20")
        if self._hover == (col, row) and self.interactive and view.mark is Mark.UNCHECKED:
            fill = QColor(NAVY["water_hover"])
        painter.setPen(QPen(QColor(NAVY["border"]), 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 5, 5)
        if view.has_ship and view.mark is not Mark.SUNK:
            painter.setPen(QPen(QColor(NAVY["ship_edge"]), 1.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 4, 4)

        glyph = glyph_for(view.mark)
        if glyph:
            color = {
                Mark.HIT: NAVY["hit"],
                Mark.SUNK: NAVY["sunk"],
                Mark.MISS: NAVY["miss"],
            }.get(view.mark, NAVY["text"])
            font = QFont(self.font())
            font.setBold(True)
            font.setPointSize(max(11, int(size * 0.42)))
            painter.setFont(font)
            painter.setPen(QColor(color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, glyph)

        if view.last_shot:
            alpha = int(80 + 120 * abs(0.5 - self._pulse) * 2)
            painter.setPen(QPen(QColor(224, 177, 74, alpha), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 6, 6)
