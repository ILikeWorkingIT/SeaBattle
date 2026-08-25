from __future__ import annotations

import locale

from PySide6.QtCore import QObject, QSettings, Signal

from frontend.domain.types import Language


class SettingsStore(QObject):
    language_changed = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings("SeaBattle", "Frontend")
        stored = self._settings.value("language", "", type=str)
        if stored in {Language.RU.value, Language.EN.value}:
            self._language = Language(stored)
        else:
            self._language = _detect_os_language()
            self._settings.setValue("language", self._language.value)

    @property
    def language(self) -> Language:
        return self._language

    def set_language(self, language: Language) -> None:
        if language is self._language:
            return
        self._language = language
        self._settings.setValue("language", language.value)
        self.language_changed.emit(language)


def _detect_os_language() -> Language:
    raw = (locale.getdefaultlocale()[0] or "").lower()
    if raw.startswith("ru"):
        return Language.RU
    return Language.EN
