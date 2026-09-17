from __future__ import annotations

import locale

from PySide6.QtCore import QObject, QSettings, Signal

from frontend.domain.types import Language


class SettingsStore(QObject):
    language_changed = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings("SeaBattle", "Frontend")
        stored = _parse_stored_language(self._settings.value("language"))
        if stored is not None:
            self._language = stored
        else:
            self._language = _detect_os_language()
            self._persist(self._language)

    @property
    def language(self) -> Language:
        return self._language

    def set_language(self, language: Language) -> None:
        if language not in {Language.RU, Language.EN}:
            return
        if language is self._language:
            return
        self._language = language
        self._persist(language)
        self.language_changed.emit(language)

    def _persist(self, language: Language) -> None:
        try:
            self._settings.setValue("language", language.value)
            self._settings.sync()
        except OSError:
            return


def _parse_stored_language(stored: object) -> Language | None:
    if stored is None:
        return None
    text = str(stored).strip()
    if text in {Language.RU.value, Language.EN.value}:
        return Language(text)
    return None


def _detect_os_language() -> Language:
    raw = (locale.getdefaultlocale()[0] or "").lower()
    if raw.startswith("ru"):
        return Language.RU
    return Language.EN
