from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from PySide6.QtGui import QAction, QActionGroup

from frontend.domain.types import Language
from frontend.i18n import I18n
from frontend.mock.static_scene import (
    BATTLE_SCENE,
    LOBBY_SLOTS_USED,
    STATS_SNAPSHOT,
)
from frontend.settings_store import SettingsStore
from frontend.theme import APP_QSS
from frontend.ui.battle_screen import BattleScreen
from frontend.ui.dialogs import GameOverDialog, StatsDialog, SurrenderDialog
from frontend.ui.lobby_screen import LobbyScreen
from frontend.ui.toast import ToastHost


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)
        self.setStyleSheet(APP_QSS)
        self.settings = SettingsStore(self)
        self.i18n = I18n(self.settings.language)
        self._on_battle = False

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.lobby = LobbyScreen()
        self.battle = BattleScreen()
        self.stack.addWidget(self.lobby)
        self.stack.addWidget(self.battle)
        layout.addWidget(self.stack)

        self.toasts = ToastHost(root)
        self.surrender_dialog = SurrenderDialog(self)
        self.game_over_dialog = GameOverDialog(self)
        self.stats_dialog = StatsDialog(self)

        self._build_menu()
        self._connect()
        self.settings.language_changed.connect(self._on_language)
        self._retranslate()
        self._show_lobby()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.toasts.reposition()
        self.toasts.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.stack.setGeometry(self.centralWidget().rect())
        self.toasts.reposition()

    def _build_menu(self) -> None:
        self._act_new = QAction(self)
        self._act_new.triggered.connect(self._show_battle)
        self._act_surrender = QAction(self)
        self._act_surrender.triggered.connect(self._confirm_surrender)
        self._act_exit = QAction(self)
        self._act_exit.triggered.connect(self.close)
        self._act_stats = QAction(self)
        self._act_stats.triggered.connect(self._open_stats)
        self._act_ru = QAction(self)
        self._act_en = QAction(self)
        self._act_ru.setCheckable(True)
        self._act_en.setCheckable(True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self._act_ru)
        group.addAction(self._act_en)
        self._act_ru.triggered.connect(lambda: self.settings.set_language(Language.RU))
        self._act_en.triggered.connect(lambda: self.settings.set_language(Language.EN))

        game = self.menuBar().addMenu("")
        game.addAction(self._act_new)
        game.addAction(self._act_surrender)
        game.addSeparator()
        game.addAction(self._act_exit)
        view = self.menuBar().addMenu("")
        view.addAction(self._act_stats)
        language = self.menuBar().addMenu("")
        language.addAction(self._act_ru)
        language.addAction(self._act_en)
        self._menu_game = game
        self._menu_view = view
        self._menu_language = language

    def _connect(self) -> None:
        self.lobby.start_requested.connect(self._show_battle)
        self.lobby.stats_requested.connect(self._open_stats)
        self.battle.surrender_requested.connect(self._confirm_surrender)
        self.battle.stats_requested.connect(self._open_stats)
        self.battle.copy_session.connect(self._copy_session)
        self.surrender_dialog.confirmed.connect(self._after_surrender)

    def _retranslate(self) -> None:
        i18n = self.i18n
        self.setWindowTitle(i18n.t("app_title"))
        self._menu_game.setTitle(i18n.t("menu_game"))
        self._menu_view.setTitle(i18n.t("menu_view"))
        self._menu_language.setTitle(i18n.t("menu_language"))
        self._act_new.setText(i18n.t("menu_new"))
        self._act_surrender.setText(i18n.t("menu_surrender"))
        self._act_exit.setText(i18n.t("menu_exit"))
        self._act_stats.setText(i18n.t("menu_stats"))
        self._act_ru.setText(i18n.t("lang_ru"))
        self._act_en.setText(i18n.t("lang_en"))
        self._act_ru.setChecked(self.settings.language is Language.RU)
        self._act_en.setChecked(self.settings.language is Language.EN)
        self._act_surrender.setEnabled(self._on_battle)
        self.lobby.bind(i18n, STATS_SNAPSHOT, LOBBY_SLOTS_USED)
        self.surrender_dialog.retranslate(i18n)
        self.stats_dialog.retranslate(i18n)
        if self._on_battle:
            self.battle.bind_scene(i18n, self.settings.language, BATTLE_SCENE)

    def _on_language(self, language: Language) -> None:
        self.i18n = I18n(language)
        self._retranslate()
        self.toasts.show_message(self.i18n.t("toast_lang"), "ok")

    def _show_lobby(self) -> None:
        self._on_battle = False
        self.stack.setCurrentWidget(self.lobby)
        self._act_surrender.setEnabled(False)
        self.lobby.bind(self.i18n, STATS_SNAPSHOT, LOBBY_SLOTS_USED)

    def _show_battle(self) -> None:
        self._on_battle = True
        self.stack.setCurrentWidget(self.battle)
        self._act_surrender.setEnabled(True)
        self.battle.bind_scene(self.i18n, self.settings.language, BATTLE_SCENE)

    def _open_stats(self) -> None:
        self.stats_dialog.bind(self.i18n, STATS_SNAPSHOT)
        self.stats_dialog.exec()

    def _confirm_surrender(self) -> None:
        if not self._on_battle:
            return
        self.surrender_dialog.retranslate(self.i18n)
        self.surrender_dialog.exec()

    def _after_surrender(self) -> None:
        # Navigation only: show game-over appearance, then return to lobby.
        self.game_over_dialog.present(self.i18n, BATTLE_SCENE.game_over)
        self.game_over_dialog.exec()
        action = self.game_over_dialog.next_action
        self._show_lobby()
        if action == "new":
            self._show_battle()
        elif action == "stats":
            self._open_stats()

    def _copy_session(self) -> None:
        QGuiApplication.clipboard().setText(BATTLE_SCENE.session_id)
        self.toasts.show_message(self.i18n.t("copied"), "ok")
