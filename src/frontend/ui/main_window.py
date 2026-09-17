from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QGuiApplication
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from frontend.client.config import (
    PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS,
    PARTY_CHANNEL_TIMEOUT_SECONDS,
    PARTY_RECONNECT_DELAY_SECONDS,
)
from frontend.client.party_channel import PartyChannelWorker
from frontend.client.party_frames import apply_game_over, apply_shot_resolved
from frontend.client.session_start import StartSessionOutcome, session_state_to_scene
from frontend.client.statistics import StatisticsOutcome
from frontend.client.worker import CreateSessionWorker, GetStatisticsWorker
from frontend.domain.types import CellCoordinate, Language, display_coord
from frontend.i18n import I18n
from frontend.mock.static_scene import (
    BATTLE_SCENE,
    LOBBY_SLOTS_USED,
    BattleScene,
    Snapshot,
)
from frontend.settings_store import SettingsStore
from frontend.theme import APP_QSS
from frontend.ui.battle_screen import BattleScreen, ChannelPhase, ShotPhase, SurrenderPhase
from frontend.ui.dialogs import GameOverDialog, StatsDialog, SurrenderDialog
from frontend.ui.lobby_screen import LobbyScreen, StartPhase, StatsPhase
from frontend.ui.toast import ToastHost

_StartPhase = StartPhase
_EMPTY_STATS = Snapshot(0, 0, 0, 0.0, [])


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)
        self.setStyleSheet(APP_QSS)
        self.settings = SettingsStore(self)
        self.i18n = I18n(self.settings.language)
        self._on_battle = False
        self._live_scene: BattleScene | None = None
        self._start_phase: _StartPhase = "idle"
        self._start_error = ""
        self._worker: CreateSessionWorker | None = None
        self._stats_phase: StatsPhase = "idle"
        self._stats_error = ""
        self._stats_snapshot = _EMPTY_STATS
        self._stats_worker: GetStatisticsWorker | None = None
        self._start_outcome: StartSessionOutcome | None = None
        self._stats_outcome: StatisticsOutcome | None = None
        self._channel_error_src: dict[str, object] | None = None
        self._shot_error_src: dict[str, object] | None = None
        self._surrender_error_src: dict[str, object] | None = None
        self._party: PartyChannelWorker | None = None
        self._party_token = 0
        self._party_handshake_resume = False
        self._channel_phase: ChannelPhase = "idle"
        self._channel_error = ""
        self._shot_phase: ShotPhase = "idle"
        self._shot_error = ""
        self._surrender_phase: SurrenderPhase = "idle"
        self._surrender_error = ""
        self._result_shown = False
        self._party_start_timer = QTimer(self)
        self._party_start_timer.setSingleShot(True)
        self._party_start_timer.timeout.connect(self._open_party_current)
        self._party_reconnect_timer = QTimer(self)
        self._party_reconnect_timer.setSingleShot(True)
        self._party_reconnect_timer.timeout.connect(self._open_party_current)

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
        self._request_statistics()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.stack.setGeometry(self.centralWidget().rect())
        self.toasts.reposition()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._stop_party()
        self._stop_worker(self._worker, self._on_start_outcome)
        self._worker = None
        self._stop_worker(self._stats_worker, self._on_stats_outcome)
        self._stats_worker = None
        super().closeEvent(event)

    def _stop_worker(self, worker: CreateSessionWorker | GetStatisticsWorker | None, slot: object) -> None:
        if worker is None:
            return
        try:
            worker.finished_outcome.disconnect(slot)
        except RuntimeError:
            pass
        worker.requestInterruption()
        worker.wait(400)

    def _build_menu(self) -> None:
        self._act_new = QAction(self)
        self._act_new.setObjectName("menu-new-match")
        self._act_new.triggered.connect(self._start_session)
        self._act_surrender = QAction(self)
        self._act_surrender.setObjectName("menu-surrender")
        self._act_surrender.triggered.connect(self._confirm_surrender)
        self._act_exit = QAction(self)
        self._act_exit.triggered.connect(self.close)
        self._act_stats = QAction(self)
        self._act_stats.setObjectName("menu-stats")
        self._act_stats.triggered.connect(self._open_stats)
        self._act_ru = QAction(self)
        self._act_en = QAction(self)
        self._act_ru.setObjectName("menu-language-ru")
        self._act_en.setObjectName("menu-language-en")
        self._act_ru.setCheckable(True)
        self._act_en.setCheckable(True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self._act_ru)
        group.addAction(self._act_en)
        self._act_ru.triggered.connect(self._choose_russian)
        self._act_en.triggered.connect(self._choose_english)

        game = self.menuBar().addMenu("")
        game.addAction(self._act_new)
        game.addAction(self._act_surrender)
        game.addSeparator()
        game.addAction(self._act_exit)
        view = self.menuBar().addMenu("")
        view.addAction(self._act_stats)
        language = self.menuBar().addMenu("")
        language.setObjectName("menu-language")
        language.addAction(self._act_ru)
        language.addAction(self._act_en)
        self._menu_game = game
        self._menu_view = view
        self._menu_language = language

    def _connect(self) -> None:
        self.lobby.start_requested.connect(self._start_session)
        self.lobby.stats_requested.connect(self._open_stats)
        self.battle.surrender_requested.connect(self._confirm_surrender)
        self.battle.stats_requested.connect(self._open_stats)
        self.battle.copy_session.connect(self._copy_session)
        self.battle.player_board.cell_clicked.connect(self._on_player_board_click)
        self.battle.backend_board.cell_clicked.connect(self._on_computer_board_click)
        self.surrender_dialog.confirmed.connect(self._after_surrender)
        self.stats_dialog.refresh_requested.connect(self._request_statistics)

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
        self._act_ru.blockSignals(True)
        self._act_en.blockSignals(True)
        self._act_ru.setChecked(self.settings.language is Language.RU)
        self._act_en.setChecked(self.settings.language is Language.EN)
        self._act_ru.blockSignals(False)
        self._act_en.blockSignals(False)
        self._act_surrender.setEnabled(self._can_surrender())
        self._refresh_error_texts()
        self.lobby.bind(i18n, self._stats_snapshot, LOBBY_SLOTS_USED)
        self.lobby.apply_start_phase(i18n, self._start_phase, self._start_error)
        self.lobby.apply_stats_phase(i18n, self._stats_phase, self._stats_error)
        self.surrender_dialog.retranslate(i18n)
        self.game_over_dialog.retranslate(i18n)
        self.stats_dialog.bind(i18n, self._stats_snapshot)
        self.stats_dialog.apply_stats_phase(i18n, self._stats_phase, self._stats_error)
        if self._on_battle and self._live_scene is not None:
            self.battle.bind_scene(i18n, self.settings.language, self._live_scene)
            self._apply_battle_status()
        else:
            self.battle.retranslate(i18n)

    def _choose_russian(self, checked: bool = True) -> None:
        if checked:
            self.settings.set_language(Language.RU)

    def _choose_english(self, checked: bool = True) -> None:
        if checked:
            self.settings.set_language(Language.EN)

    def _on_language(self, language: Language) -> None:
        self.i18n = I18n(language)
        self._retranslate()
        self.toasts.show_message(self.i18n.t("toast_lang"), "ok")

    def _show_lobby(self) -> None:
        self._on_battle = False
        self._result_shown = False
        self._stop_party()
        self._channel_phase = "idle"
        self._channel_error = ""
        self._channel_error_src = None
        self._shot_phase = "idle"
        self._shot_error = ""
        self._shot_error_src = None
        self._surrender_phase = "idle"
        self._surrender_error = ""
        self._surrender_error_src = None
        self.battle.apply_computer_turn(self.i18n, False)
        if self._start_phase == "success":
            self._start_phase = "idle"
            self._start_error = ""
        self.stack.setCurrentWidget(self.lobby)
        self._act_surrender.setEnabled(False)
        self.battle.set_surrender_enabled(False)
        self.lobby.bind(self.i18n, self._stats_snapshot, LOBBY_SLOTS_USED)
        self.lobby.apply_start_phase(self.i18n, self._start_phase, self._start_error)
        self.lobby.apply_stats_phase(self.i18n, self._stats_phase, self._stats_error)
        if self.isVisible():
            self._request_statistics()

    def _start_session(self) -> None:
        if self._start_phase == "loading":
            return
        if self._on_battle:
            self._stop_party()
        self._start_phase = "loading"
        self._start_error = ""
        self._start_outcome = None
        self._act_new.setEnabled(False)
        self.lobby.apply_start_phase(self.i18n, self._start_phase, self._start_error)
        worker = CreateSessionWorker(self)
        self._worker = worker
        worker.finished_outcome.connect(self._on_start_outcome)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _on_start_outcome(self, outcome: object) -> None:
        self._worker = None
        self._act_new.setEnabled(True)
        if not isinstance(outcome, StartSessionOutcome):
            self._start_outcome = None
            self._start_phase = "error"
            self._start_error = self.i18n.t("err_timeout")
            self.lobby.apply_start_phase(self.i18n, self._start_phase, self._start_error)
            self.toasts.show_message(self._start_error, "error")
            return
        if outcome.kind == "success" and outcome.scene is not None:
            self._start_outcome = None
            self._live_scene = outcome.scene
            self._start_phase = "success"
            self._start_error = ""
            self._show_battle(outcome.scene)
            self.toasts.show_message(self.i18n.t("toast_started"), "ok")
            return
        self._start_outcome = outcome
        self._start_error = self._localize_start_error()
        self._start_phase = "error"
        if not self._on_battle:
            self.lobby.apply_start_phase(self.i18n, self._start_phase, self._start_error)
        self.toasts.show_message(self._start_error, "error")

    def _show_battle(self, scene: BattleScene) -> None:
        self._on_battle = True
        self._live_scene = scene
        self._result_shown = False
        self._channel_phase = "loading"
        self._channel_error = ""
        self._channel_error_src = None
        self._shot_phase = "idle"
        self._shot_error = ""
        self._shot_error_src = None
        self._surrender_phase = "idle"
        self._surrender_error = ""
        self._surrender_error_src = None
        self.stack.setCurrentWidget(self.battle)
        self._act_surrender.setEnabled(self._can_surrender())
        self.battle.set_surrender_enabled(self._can_surrender())
        self.battle.bind_scene(self.i18n, self.settings.language, scene)
        self._apply_battle_status()
        self._party_reconnect_timer.stop()
        self._party_token += 1
        self._party_handshake_resume = False
        self._party_start_timer.start(0)

    def _open_stats(self) -> None:
        self.stats_dialog.bind(self.i18n, self._stats_snapshot)
        self.stats_dialog.apply_stats_phase(self.i18n, self._stats_phase, self._stats_error)
        self._request_statistics()
        self.stats_dialog.exec()

    def _request_statistics(self) -> None:
        if self._stats_phase == "loading":
            return
        self._stats_phase = "loading"
        self._stats_error = ""
        self._stats_outcome = None
        self._apply_stats_ui()
        worker = GetStatisticsWorker(self)
        self._stats_worker = worker
        worker.finished_outcome.connect(self._on_stats_outcome)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _on_stats_outcome(self, outcome: object) -> None:
        self._stats_worker = None
        if not isinstance(outcome, StatisticsOutcome):
            self._stats_outcome = None
            self._stats_phase = "error"
            self._stats_error = self.i18n.t("err_timeout")
            self._apply_stats_ui()
            return
        if outcome.kind == "success" and outcome.snapshot is not None:
            self._stats_outcome = None
            self._stats_snapshot = outcome.snapshot
            self._stats_error = ""
            self._stats_phase = "empty" if outcome.snapshot.games == 0 else "success"
            self._apply_stats_ui()
            if self.stats_dialog.isVisible():
                self.toasts.show_message(self.i18n.t("toast_stats"), "ok")
            return
        self._stats_outcome = outcome
        self._stats_error = self._localize_stats_error()
        self._stats_phase = "error"
        self._apply_stats_ui()

    def _apply_stats_ui(self) -> None:
        self.lobby.bind(self.i18n, self._stats_snapshot, LOBBY_SLOTS_USED)
        self.lobby.apply_start_phase(self.i18n, self._start_phase, self._start_error)
        self.lobby.apply_stats_phase(self.i18n, self._stats_phase, self._stats_error)
        self.stats_dialog.bind(self.i18n, self._stats_snapshot)
        self.stats_dialog.apply_stats_phase(self.i18n, self._stats_phase, self._stats_error)

    def _confirm_surrender(self) -> None:
        if not self._can_surrender():
            return
        self.surrender_dialog.retranslate(self.i18n)
        self.surrender_dialog.exec()

    def _after_surrender(self) -> None:
        if not self._on_battle:
            return
        scene = self._live_scene
        if scene is None or scene.match_over or self._surrender_phase == "loading":
            return
        self._surrender_phase = "loading"
        self._surrender_error = ""
        self._surrender_error_src = None
        self._apply_battle_status()
        if self._channel_phase != "success" or self._party is None:
            self._fail_surrender(self._channel_error_src or {"i18n": "err_surrender"})
            return
        self._party.send_surrender()

    def _open_party_current(self) -> None:
        self._open_party(self._party_token)

    def _open_party(self, token: int) -> None:
        scene = self._live_scene
        if token != self._party_token or not self._party_resume_allowed() or scene is None:
            return
        self._party_reconnect_timer.stop()
        self._stop_party_worker()
        self._channel_phase = "loading"
        self._channel_error = ""
        self._channel_error_src = None
        self._shot_phase = "idle"
        self._shot_error = ""
        self._shot_error_src = None
        self._apply_battle_status()
        handshake_s = (
            PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS
            if self._party_handshake_resume
            else PARTY_CHANNEL_TIMEOUT_SECONDS
        )
        worker = PartyChannelWorker(
            scene.session_id,
            self,
            handshake_timeout_seconds=handshake_s,
            retry_handshake=self._party_handshake_resume,
        )
        self._party = worker
        worker.incoming.connect(self._on_party_frame)
        worker.start()

    def _party_resume_allowed(self) -> bool:
        scene = self._live_scene
        return (
            self._on_battle
            and scene is not None
            and bool(scene.session_id)
            and not scene.match_over
        )

    def _schedule_party_reconnect(self) -> None:
        if not self._party_resume_allowed():
            self._party_reconnect_timer.stop()
            return
        if self._party_reconnect_timer.isActive() or self._party_start_timer.isActive():
            return
        self._party_handshake_resume = True
        delay_ms = int(PARTY_RECONNECT_DELAY_SECONDS * 1000)
        self._party_reconnect_timer.start(delay_ms)

    def _apply_session_snapshot(self, payload: dict[str, object]) -> bool:
        session = payload.get("session")
        if not isinstance(session, dict):
            return False
        try:
            scene = session_state_to_scene(session)
        except (KeyError, TypeError, ValueError):
            return False
        live = self._live_scene
        if live is not None and scene.session_id != live.session_id:
            return False
        self._live_scene = scene
        return True

    def _stop_party(self) -> None:
        self._party_token += 1
        self._party_start_timer.stop()
        self._party_reconnect_timer.stop()
        self._stop_party_worker()

    def _reject_incomplete_snapshot(self) -> None:
        self._stop_party_worker()
        self._shot_phase = "idle"
        self._shot_error = ""
        self._shot_error_src = None
        self._set_channel_error({"code": "TIMEOUT"})
        self._abort_pending_surrender({"i18n": "err_surrender"})
        self._apply_battle_status()
        self._schedule_party_reconnect()

    def _stop_party_worker(self) -> None:
        worker = self._party
        if worker is None:
            return
        try:
            worker.incoming.disconnect(self._on_party_frame)
        except RuntimeError:
            pass
        worker.shutdown()
        worker.deleteLater()
        self._party = None

    def _on_party_frame(self, payload: object) -> None:
        if not isinstance(payload, dict) or not self._on_battle:
            return
        kind = str(payload.get("type", ""))
        if kind == "sessionSnapshot":
            if not self._apply_session_snapshot(payload):
                self._reject_incomplete_snapshot()
                return
            self._party_reconnect_timer.stop()
            self._channel_phase = "success"
            self._channel_error = ""
            self._channel_error_src = None
            self._refresh_shot_phase()
            self._bind_live_battle()
            return
        if kind == "_channel_error":
            self._shot_phase = "idle"
            self._shot_error = ""
            self._shot_error_src = None
            self._set_channel_error(payload)
            self._abort_pending_surrender({"i18n": "err_surrender"})
            self._apply_battle_status()
            retry = payload.get("retry")
            if retry is None:
                retry = str(payload.get("code", "")) == "TIMEOUT"
            if retry:
                self._schedule_party_reconnect()
            else:
                self._party_reconnect_timer.stop()
                self.toasts.show_message(self._channel_error, "error")
            return
        if kind == "_disconnected":
            self._clear_shot_pending()
            self._set_channel_error({"code": "TIMEOUT"})
            self._abort_pending_surrender({"i18n": "err_surrender"})
            self._apply_battle_status()
            self._schedule_party_reconnect()
            return
        if kind == "error":
            self._clear_shot_pending()
            if self._surrender_phase == "loading":
                src = dict(payload)
                if not self._localize_tagged(src):
                    src = {"i18n": "err_surrender"}
                self._abort_pending_surrender(src)
            else:
                self._shot_phase = "error"
                self._shot_error_src = payload
                self._shot_error = self._localize_tagged(payload)
            self._apply_battle_status()
            code = str(payload.get("code", ""))
            self.toasts.show_message(self.i18n.t("toast_rejected", code=code or "error"), "error")
            return
        if kind == "shotResolved":
            scene = self._live_scene
            if scene is None or not apply_shot_resolved(scene, payload):
                return
            self._clear_shot_pending()
            result = str(payload.get("result", ""))
            shooter = str(payload.get("shooter", ""))
            if shooter == "Backend":
                self.toasts.show_message(self._backend_shot_toast(payload, result), "ok")
            else:
                toast_key = {"MISS": "toast_miss", "HIT": "toast_hit", "SUNK": "toast_sunk"}.get(
                    result
                )
                if toast_key:
                    self.toasts.show_message(self.i18n.t(toast_key), "ok")
            self._refresh_shot_phase()
            self._bind_live_battle()
            board = self.battle.player_board if shooter == "Backend" else self.battle.backend_board
            board.pulse_last_shot()
            return
        if kind == "gameOver":
            self._on_game_over_frame(payload)
            return
        if kind == "sessionAborted":
            if self._live_scene is not None:
                self._live_scene.match_over = True
            self._clear_shot_pending()
            self._clear_surrender_pending()
            abort_src = dict(payload)
            abort_src["code"] = "SESSION_ABORTED"
            self._set_channel_error(abort_src)
            self._apply_battle_status()
            self.toasts.show_message(self.i18n.t("toast_abort"), "error")
            self._stop_party()
            return
        if kind == "ttlExpired":
            if self._live_scene is not None:
                self._live_scene.match_over = True
            self._clear_shot_pending()
            self._clear_surrender_pending()
            self._set_channel_error({"code": "TTL_EXPIRED"})
            self._apply_battle_status()
            self.toasts.show_message(self.i18n.t("toast_ttl"), "warn")
            self._stop_party()

    def _on_game_over_frame(self, payload: dict[str, object]) -> None:
        scene = self._live_scene
        if scene is None or not apply_game_over(scene, payload):
            return
        if self._result_shown:
            return
        self._result_shown = True
        self._clear_shot_pending()
        self._clear_surrender_pending()
        self._refresh_shot_phase()
        self._bind_live_battle()
        self._stop_party()
        QTimer.singleShot(0, self._present_match_result)

    def _present_match_result(self) -> None:
        if not self._on_battle:
            return
        scene = self._live_scene
        over = scene.game_over if scene is not None else BATTLE_SCENE.game_over
        self.game_over_dialog.present(self.i18n, over)
        self.game_over_dialog.exec()
        action = self.game_over_dialog.next_action
        self._live_scene = None
        self._show_lobby()
        if action == "new":
            self._start_session()
        elif action == "stats":
            self._open_stats()

    def _can_surrender(self) -> bool:
        scene = self._live_scene
        return (
            self._on_battle
            and scene is not None
            and not scene.match_over
            and self._surrender_phase != "loading"
        )

    def _party_message(self, payload: dict[str, object], russian: bool) -> str:
        raw = payload.get("messageRu" if russian else "message")
        if isinstance(raw, str) and raw:
            return raw
        fallback = payload.get("message")
        return fallback if isinstance(fallback, str) else ""

    def _localize_tagged(self, src: dict[str, object]) -> str:
        key = src.get("i18n")
        if isinstance(key, str) and key:
            return self.i18n.t(key)
        code = str(src.get("code", ""))
        mapped = {
            "TIMEOUT": "err_timeout",
            "SESSION_UNAVAILABLE": "err_session_unavailable",
            "VALIDATION_ERROR": "err_validation",
            "SESSION_ABORTED": "toast_abort",
            "TTL_EXPIRED": "toast_ttl",
        }.get(code)
        if mapped is not None:
            return self.i18n.t(mapped)
        russian = self.settings.language is Language.RU
        return self._party_message(src, russian)

    def _set_channel_error(self, src: dict[str, object]) -> None:
        self._channel_phase = "error"
        self._channel_error_src = src
        self._channel_error = self._localize_tagged(src)

    def _refresh_error_texts(self) -> None:
        if self._start_phase == "error":
            self._start_error = self._localize_start_error()
        if self._stats_phase == "error":
            self._stats_error = self._localize_stats_error()
        if self._channel_error_src is not None and self._channel_phase == "error":
            self._channel_error = self._localize_tagged(self._channel_error_src)
        if self._shot_error_src is not None and self._shot_phase == "error":
            self._shot_error = self._localize_tagged(self._shot_error_src)
        if self._surrender_error_src is not None and self._surrender_phase == "error":
            self._surrender_error = self._localize_tagged(self._surrender_error_src)

    def _localize_start_error(self) -> str:
        outcome = self._start_outcome
        if outcome is None or outcome.kind in {"timeout", "unreachable"}:
            return self.i18n.t("err_timeout")
        return outcome.text_for(self.settings.language is Language.RU)

    def _localize_stats_error(self) -> str:
        outcome = self._stats_outcome
        if outcome is None or outcome.kind in {"timeout", "unreachable"}:
            return self.i18n.t("err_timeout")
        return outcome.text_for(self.settings.language is Language.RU)

    def _clear_shot_pending(self) -> None:
        if self._shot_phase == "loading":
            self._shot_phase = "idle"
            self._shot_error = ""
            self._shot_error_src = None

    def _clear_surrender_pending(self) -> None:
        if self._surrender_phase == "loading":
            self._surrender_phase = "idle"
            self._surrender_error = ""
            self._surrender_error_src = None

    def _abort_pending_surrender(self, src: dict[str, object]) -> None:
        if self._surrender_phase != "loading":
            return
        self._surrender_phase = "error"
        self._surrender_error_src = src
        self._surrender_error = self._localize_tagged(src)

    def _fail_surrender(self, src: dict[str, object]) -> None:
        self._surrender_phase = "error"
        self._surrender_error_src = src
        self._surrender_error = self._localize_tagged(src)
        self._apply_battle_status()
        self.toasts.show_message(self._surrender_error, "error")

    def _refresh_shot_phase(self) -> None:
        if self._channel_phase != "success" or self._shot_phase == "loading":
            if self._channel_phase != "success":
                self._shot_phase = "idle"
            return
        if self._shot_phase == "error":
            return
        scene = self._live_scene
        if scene is None or not scene.shots:
            self._shot_phase = "empty"
            self._shot_error = ""
            return
        self._shot_phase = "success"
        self._shot_error = ""

    def _bind_live_battle(self) -> None:
        if self._live_scene is None:
            return
        self.battle.bind_scene(self.i18n, self.settings.language, self._live_scene)
        self._apply_battle_status()

    def _apply_battle_status(self) -> None:
        self.battle.apply_channel_phase(self.i18n, self._channel_phase, self._channel_error)
        self.battle.apply_shot_phase(self.i18n, self._shot_phase, self._shot_error)
        self.battle.apply_surrender_phase(self.i18n, self._surrender_phase, self._surrender_error)
        scene = self._live_scene
        computer_active = (
            self._on_battle
            and scene is not None
            and not scene.player_turn
            and not scene.match_over
            and self._channel_phase == "success"
            and self._shot_phase != "loading"
            and self._surrender_phase != "loading"
        )
        self.battle.apply_computer_turn(self.i18n, computer_active)
        allowed = self._can_surrender()
        self._act_surrender.setEnabled(allowed)
        self.battle.set_surrender_enabled(allowed)

    def _backend_shot_toast(self, payload: dict[str, object], result: str) -> str:
        coords = payload.get("coords")
        cell = ""
        if isinstance(coords, dict):
            try:
                cell = display_coord(
                    CellCoordinate(int(coords["column"]), int(coords["row"])),
                    self.settings.language,
                ).text()
            except (TypeError, ValueError, KeyError):
                cell = ""
        return self.i18n.t("toast_backend_shot", result=result, cell=cell)

    def _on_player_board_click(self, _column: int, _row: int) -> None:
        if not self._on_battle:
            return
        self.toasts.show_message(self.i18n.t("err_own"), "warn")

    def _on_computer_board_click(self, column: int, row: int) -> None:
        if not self._on_battle or self._live_scene is None:
            return
        if self._channel_phase == "loading":
            self.toasts.show_message(self.i18n.t("channel_connecting"), "info")
            return
        if self._channel_phase != "success" or self._party is None:
            text = self._channel_error or self.i18n.t("err_timeout")
            self.toasts.show_message(text, "error")
            self._schedule_party_reconnect()
            return
        if self._shot_phase == "loading":
            self.toasts.show_message(self.i18n.t("err_pending"), "warn")
            return
        if self._surrender_phase == "loading":
            self.toasts.show_message(self.i18n.t("surrendering"), "warn")
            return
        scene = self._live_scene
        if scene.match_over or not scene.player_turn:
            self.toasts.show_message(self.i18n.t("err_not_turn"), "warn")
            return
        self._shot_phase = "loading"
        self._shot_error = ""
        self._apply_battle_status()
        self._party.send_shot(column, row)

    def _copy_session(self) -> None:
        scene = self._live_scene
        if scene is None:
            return
        QGuiApplication.clipboard().setText(scene.session_id)
        self.toasts.show_message(self.i18n.t("copied"), "ok")
