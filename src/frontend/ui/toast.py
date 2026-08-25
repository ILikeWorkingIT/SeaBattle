from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget


class ToastHost(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._cards: list[QWidget] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._column = QWidget(self)
        self._column_layout = QVBoxLayout(self._column)
        self._column_layout.setContentsMargins(0, 0, 0, 0)
        self._column_layout.setSpacing(8)
        layout.addWidget(self._column, 0, Qt.AlignmentFlag.AlignHCenter)

    def reposition(self) -> None:
        if self.parentWidget() is None:
            return
        self.setGeometry(0, 0, self.parentWidget().width(), 220)

    def show_message(self, text: str, kind: str = "info") -> None:
        card = _ToastCard(text, kind, self._column)
        self._column_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        self._cards.append(card)
        card.fade_in()
        QTimer.singleShot(3200, lambda: self._dismiss(card))
        self.reposition()
        self.raise_()

    def _dismiss(self, card: QWidget) -> None:
        if card not in self._cards:
            return
        self._cards.remove(card)
        card.fade_out(lambda: card.deleteLater())


class _ToastCard(QWidget):
    def __init__(self, text: str, kind: str, parent: QWidget) -> None:
        super().__init__(parent)
        palette = {
            "info": ("#163044", "#3EC8B0"),
            "ok": ("#1A3A2A", "#3EC8B0"),
            "warn": ("#3A3018", "#E0B14A"),
            "error": ("#3A1C20", "#E05A5A"),
        }
        background, accent = palette.get(kind, palette["info"])
        self.setFixedWidth(460)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        self.setStyleSheet(
            f"background: {background}; border: 1px solid {accent}; border-radius: 12px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: #E8F3F8; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(label)
        self._anim: QPropertyAnimation | None = None

    def fade_in(self) -> None:
        self._animate(0.0, 1.0, 220)

    def fade_out(self, done) -> None:
        anim = self._animate(self._effect.opacity(), 0.0, 180)
        anim.finished.connect(done)

    def _animate(self, start: float, end: float, duration: int) -> QPropertyAnimation:
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim = anim
        return anim
