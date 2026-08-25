from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from frontend.domain.session import Session, ShotOutcome
from frontend.domain.types import Language, Mark, ShotResult, Side
from frontend.i18n import I18n
from frontend.mock.backend import MockBackend
from frontend.mock.ledger import Snapshot
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
        self.backend = MockBackend(self)
        self._last_outcome: ShotOutcome | None = None
        self._busy_start = False

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
        self._refresh_lobby()
        self._ttl_ui = QTimer(self)
        self._ttl_ui.setInterval(1000)
        self._ttl_ui.timeout.connect(self._tick_ttl)

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
        self._act_new.triggered.connect(self._request_new_from_menu)
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
        self.lobby.start_requested.connect(self._start_session)
        self.lobby.stats_requested.connect(self._open_stats)
        self.battle.player_shot.connect(self._on_player_shot)
        self.battle.own_board_clicked.connect(
            lambda: self.toasts.show_message(self.i18n.t("err_own"), "warn")
        )
        self.battle.surrender_requested.connect(self._confirm_surrender)
        self.battle.stats_requested.connect(self._open_stats)
        self.battle.copy_session.connect(self._copy_session)
        self.surrender_dialog.confirmed.connect(self.backend.surrender)
        self.stats_dialog.refresh_requested.connect(self.backend.request_stats)

        self.backend.session_started.connect(self._on_started)
        self.backend.start_failed.connect(self._on_start_failed)
        self.backend.shot_resolved.connect(self._on_shot_resolved)
        self.backend.shot_rejected.connect(self._on_shot_rejected)
        self.backend.backend_aiming.connect(self._on_aiming)
        self.backend.backend_shot.connect(self._on_backend_shot)
        self.backend.game_over.connect(self._on_game_over)
        self.backend.session_aborted.connect(self._on_aborted)
        self.backend.ttl_expired.connect(self._on_ttl_expired)
        self.backend.stats_ready.connect(self._on_stats_ready)

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
        in_battle = self.stack.currentWidget() is self.battle
        self._act_surrender.setEnabled(in_battle)
        self.lobby.bind(i18n, self.backend.snapshot(), self.backend.occupied_slots())
        self.surrender_dialog.retranslate(i18n)
        self.stats_dialog.retranslate(i18n)
        if in_battle and self.backend.session is not None:
            self.battle.bind_session(i18n, self.settings.language, self.backend.session, self._last_outcome)

    def _on_language(self, language: Language) -> None:
        self.i18n = I18n(language)
        self._retranslate()
        self.toasts.show_message(self.i18n.t("toast_lang"), "ok")

    def _refresh_lobby(self) -> None:
        self.lobby.bind(self.i18n, self.backend.snapshot(), self.backend.occupied_slots())

    def _start_session(self) -> None:
        if self._busy_start:
            return
        self._busy_start = True
        self.lobby.set_busy(True, self.i18n)
        self.backend.start_session()

    def _request_new_from_menu(self) -> None:
        if self.backend.session is not None:
            self._confirm_surrender()
            return
        self._start_session()

    def _on_started(self, session: Session) -> None:
        self._busy_start = False
        self.lobby.set_busy(False, self.i18n)
        self._last_outcome = None
        self.stack.setCurrentWidget(self.battle)
        self.battle.bind_session(self.i18n, self.settings.language, session, None)
        self._act_surrender.setEnabled(True)
        self._ttl_ui.start()
        self.toasts.show_message(self.i18n.t("toast_started"), "ok")

    def _on_start_failed(self, code: str) -> None:
        self._busy_start = False
        self.lobby.set_busy(False, self.i18n)
        if code == "FT-049":
            self.toasts.show_message(self.i18n.t("toast_limit"), "error")
            return
        self.toasts.show_message(self.i18n.t("toast_start_fail", code=code), "error")

    def _on_player_shot(self, column: int, row: int) -> None:
        session = self.backend.session
        if session is None:
            return
        if session.turn is not Side.PLAYER:
            self.toasts.show_message(self.i18n.t("err_not_turn"), "warn")
            return
        if self.backend.shot_pending:
            self.toasts.show_message(self.i18n.t("err_pending"), "warn")
            return
        mark = session.backend_board.mark_at(column, row)
        if mark is not Mark.UNCHECKED:
            self.toasts.show_message(self.i18n.t("err_checked"), "warn")
            return
        self.backend.player_shot(column, row)

    def _on_shot_resolved(self, outcome: ShotOutcome) -> None:
        self._last_outcome = outcome
        self._refresh_battle()
        self._toast_result(outcome, player=True)

    def _on_shot_rejected(self, code: str) -> None:
        self.toasts.show_message(self.i18n.t("toast_rejected", code=code), "error")

    def _on_aiming(self) -> None:
        self.battle.set_aiming(True)

    def _on_backend_shot(self, outcome: ShotOutcome) -> None:
        self.battle.set_aiming(False)
        self._last_outcome = outcome
        self._refresh_battle()
        cell = self._cell_text(outcome)
        self.toasts.show_message(
            self.i18n.t("toast_backend_shot", result=outcome.shot.result.value, cell=cell),
            "info",
        )

    def _on_game_over(self, session: Session) -> None:
        self.battle.set_aiming(False)
        self._ttl_ui.stop()
        self._refresh_battle()
        self._act_surrender.setEnabled(False)
        self.game_over_dialog.present(self.i18n, session)
        self.game_over_dialog.exec()
        action = self.game_over_dialog.next_action
        self.backend.clear_session()
        self.stack.setCurrentWidget(self.lobby)
        self._act_surrender.setEnabled(False)
        self._refresh_lobby()
        if action == "new":
            self._start_session()
        elif action == "stats":
            self._open_stats()

    def _on_aborted(self) -> None:
        self._ttl_ui.stop()
        self.battle.set_aiming(False)
        self.stack.setCurrentWidget(self.lobby)
        self._refresh_lobby()
        self.toasts.show_message(self.i18n.t("toast_abort"), "error")

    def _on_ttl_expired(self) -> None:
        self._ttl_ui.stop()
        self.stack.setCurrentWidget(self.lobby)
        self._refresh_lobby()
        self.toasts.show_message(self.i18n.t("toast_ttl"), "warn")

    def _open_stats(self) -> None:
        self.stats_dialog.bind(self.i18n, self.backend.snapshot())
        self.backend.request_stats()
        self.stats_dialog.exec()

    def _on_stats_ready(self, snapshot: Snapshot) -> None:
        self.stats_dialog.bind(self.i18n, snapshot)
        self.lobby.bind(self.i18n, snapshot, self.backend.occupied_slots())
        if self.stats_dialog.isVisible():
            self.toasts.show_message(self.i18n.t("toast_stats"), "ok")

    def _confirm_surrender(self) -> None:
        if self.backend.session is None:
            return
        self.surrender_dialog.retranslate(self.i18n)
        self.surrender_dialog.exec()

    def _copy_session(self) -> None:
        session = self.backend.session
        if session is None:
            return
        QGuiApplication.clipboard().setText(session.id)
        self.toasts.show_message(self.i18n.t("copied"), "ok")

    def _refresh_battle(self) -> None:
        session = self.backend.session
        if session is None:
            return
        self.battle.bind_session(self.i18n, self.settings.language, session, self._last_outcome)

    def _tick_ttl(self) -> None:
        session = self.backend.session
        if session is None:
            return
        self.battle.update_ttl(session)

    def _toast_result(self, outcome: ShotOutcome, player: bool) -> None:
        match outcome.shot.result:
            case ShotResult.MISS:
                self.toasts.show_message(self.i18n.t("toast_miss"), "info")
            case ShotResult.HIT:
                self.toasts.show_message(self.i18n.t("toast_hit"), "ok")
            case ShotResult.SUNK:
                self.toasts.show_message(self.i18n.t("toast_sunk"), "ok")
            case _:
                never: ShotResult = outcome.shot.result
                raise ValueError(f"Unhandled shot result: {never}")

    def _cell_text(self, outcome: ShotOutcome) -> str:
        from frontend.domain.types import display_coord

        return display_coord(outcome.shot.coords, self.settings.language).text()
