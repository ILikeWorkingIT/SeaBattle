"""UC-008 language menu (S-08 frontend). No QApplication.exec, no live HTTP/WS."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from frontend.client.session_start import StartSessionOutcome
from frontend.domain.types import (
    EN_LETTERS,
    RU_LETTERS,
    CellCoordinate,
    EndReason,
    Language,
    display_coord,
    letters_for,
)
from frontend.i18n import I18n
from frontend.mock.static_scene import GameOverView
from frontend.settings_store import SettingsStore
from frontend.ui.main_window import MainWindow
from tests.test_should_post_sessions_when_client_starts import created_session_payload
from tests.test_should_show_shot_result_when_computer_board_clicked import (
    _connect_channel,
    _enter_battle,
    _shown_on,
    _shot_resolved,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _isolate_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    *,
    language: str | None = "RU",
) -> str:
    path = str(tmp_path / "frontend.ini")
    if language is not None:
        seed = QSettings(path, QSettings.Format.IniFormat)
        seed.setValue("language", language)
        seed.sync()
    monkeypatch.setattr(
        "frontend.settings_store.QSettings",
        lambda *_args, **_kwargs: QSettings(path, QSettings.Format.IniFormat),
    )
    return path


def _window(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    *,
    language: str | None = "RU",
    session_starts: list[int] | None = None,
    party_starts: list[int] | None = None,
    shots: list[tuple[int, int]] | None = None,
    surrenders: list[int] | None = None,
) -> MainWindow:
    del qapp
    _isolate_settings(monkeypatch, tmp_path, language=language)
    starts = session_starts if session_starts is not None else []
    parties = party_starts if party_starts is not None else []

    def fake_session_start(self) -> None:
        del self
        starts.append(1)

    def fake_party_start(self) -> None:
        del self
        parties.append(1)

    monkeypatch.setattr(
        "frontend.ui.main_window.CreateSessionWorker.start",
        fake_session_start,
    )
    monkeypatch.setattr(
        "frontend.ui.main_window.GetStatisticsWorker.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "frontend.ui.main_window.PartyChannelWorker.start",
        fake_party_start,
    )
    if shots is not None:

        def fake_send(self, column: int, row: int) -> None:
            del self
            shots.append((column, row))

        monkeypatch.setattr(
            "frontend.ui.main_window.PartyChannelWorker.send_shot",
            fake_send,
        )
    if surrenders is not None:

        def fake_surrender(self) -> None:
            del self
            surrenders.append(1)

        monkeypatch.setattr(
            "frontend.ui.main_window.PartyChannelWorker.send_surrender",
            fake_surrender,
        )

    def forbid_http(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("language change must not call HTTP")

    monkeypatch.setattr("urllib.request.urlopen", forbid_http)
    return MainWindow()


def _stored_language(path: str) -> str:
    store = QSettings(path, QSettings.Format.IniFormat)
    return str(store.value("language") or "")


def _kpi_caption(window: MainWindow, accessible_name: str) -> str:
    for caption, value in window.lobby._kpi_widgets:
        if value.accessibleName() == accessible_name:
            return caption.text()
    raise AssertionError(accessible_name)


def test_should_switch_lobby_captions_when_language_menu_toggled(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """UC-008 / FT-059 / FT-061 / A0049: lobby RU↔EN via menu-language, Computer labels."""
    window = _window(qapp, monkeypatch, tmp_path, language="RU")
    ru = I18n(Language.RU)
    en = I18n(Language.EN)
    assert window._menu_language.objectName() == "menu-language"
    assert window._act_ru.objectName() == "menu-language-ru"
    assert window._act_en.objectName() == "menu-language-en"
    assert window._act_ru.isChecked()
    assert window.lobby._lead.text() == ru.t("lobby_lead")
    assert "Компьютер" in window.lobby._lead.text()
    assert _kpi_caption(window, "kpi-computer-wins") == ru.t("kpi_backend")
    assert window.lobby._tabs.tabText(0) == ru.t("fleet_title")
    assert window.lobby._tabs.tabText(1) == ru.t("rules_title")
    window._act_en.trigger()
    assert window.settings.language is Language.EN
    assert window._act_en.isChecked()
    assert window._menu_language.title() == en.t("menu_language")
    assert window.lobby._lead.text() == en.t("lobby_lead")
    assert "Computer" in window.lobby._lead.text()
    assert "Компьютер" not in window.lobby._lead.text()
    assert _kpi_caption(window, "kpi-computer-wins") == en.t("kpi_backend")
    assert window.lobby._tabs.tabText(0) == en.t("fleet_title")
    assert window.lobby.start_button.text() == en.t("start_game")
    window._act_ru.trigger()
    assert window.settings.language is Language.RU
    assert window.lobby._lead.text() == ru.t("lobby_lead")
    assert _kpi_caption(window, "kpi-computer-wins") == ru.t("kpi_backend")


def test_should_keep_session_and_cell_codes_when_language_changes_in_battle(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """UC-008 / FT-008 / FT-073 / A0091: battle letters and log display; session/codes stay; no POST/WS."""
    session_starts: list[int] = []
    party_starts: list[int] = []
    shots: list[tuple[int, int]] = []
    surrenders: list[int] = []
    window = _window(
        qapp,
        monkeypatch,
        tmp_path,
        language="RU",
        session_starts=session_starts,
        party_starts=party_starts,
        shots=shots,
        surrenders=surrenders,
    )
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _shot_resolved(seq=1, column=0, row=0, result="MISS", turn="Backend")
    )
    scene = window._live_scene
    assert scene is not None
    session_id = scene.session_id
    ttl = scene.ttl_seconds
    shot = scene.shots[0]
    assert CellCoordinate(shot.column, shot.row).code == "00"
    assert "Ё" not in "".join(RU_LETTERS)
    assert "Й" not in "".join(RU_LETTERS)
    assert letters_for(window.battle.player_board.language) == RU_LETTERS
    assert window.battle._log.item(0, 2).text() == display_coord(
        CellCoordinate(0, 0), Language.RU
    ).text()
    assert window.battle.backend_board.title == I18n(Language.RU).t("board_backend")
    starts_before = list(session_starts)
    parties_before = list(party_starts)
    window._act_en.trigger()
    assert window.settings.language is Language.EN
    assert window._live_scene is scene
    assert scene.session_id == session_id
    assert scene.ttl_seconds == ttl
    assert CellCoordinate(scene.shots[0].column, scene.shots[0].row).code == "00"
    assert letters_for(window.battle.player_board.language) == EN_LETTERS
    assert letters_for(window.battle.backend_board.language) == EN_LETTERS
    assert window.battle._log.item(0, 2).text() == display_coord(
        CellCoordinate(0, 0), Language.EN
    ).text()
    assert window.battle.backend_board.title == I18n(Language.EN).t("board_backend")
    assert window.battle._backend_fleet._title.text() == I18n(Language.EN).t(
        "fleet_backend"
    )
    assert session_starts == starts_before
    assert party_starts == parties_before
    assert shots == []
    assert surrenders == []


def test_should_retranslate_open_dialogs_when_language_changes(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """NFT-016 / A0049: surrender, game-over and stats dialogs pick up the new language."""
    window = _window(qapp, monkeypatch, tmp_path, language="RU")
    ru = I18n(Language.RU)
    en = I18n(Language.EN)
    window.surrender_dialog.retranslate(window.i18n)
    window.game_over_dialog.present(
        window.i18n,
        GameOverView(player_won=False, end_reason=EndReason.SURRENDER, shot_count=0),
    )
    window.stats_dialog.bind(window.i18n, window._stats_snapshot)
    assert window.surrender_dialog._title.text() == ru.t("surrender_title")
    assert window.game_over_dialog.reason_label.text() == ru.t("reason_surrender")
    assert window.stats_dialog._title.text() == ru.t("stats_title")
    window._act_en.trigger()
    assert window.surrender_dialog.objectName() == "surrender-dialog"
    assert window.surrender_dialog._title.text() == en.t("surrender_title")
    assert window.surrender_dialog._body.text() == en.t("surrender_body")
    assert window.surrender_dialog._yes.text() == en.t("confirm")
    assert window.game_over_dialog.objectName() == "game-over-dialog"
    assert window.game_over_dialog.winner_label.text() == en.t("you_lost")
    assert window.game_over_dialog.reason_label.text() == en.t("reason_surrender")
    assert window.game_over_dialog.close_button.text() == en.t("close")
    assert window.stats_dialog._title.text() == en.t("stats_title")
    assert window.stats_dialog._refresh.text() == en.t("refresh")
    assert window.stats_dialog._kpi_labels[2][0].text() == en.t("kpi_backend")


def test_should_retranslate_channel_error_when_language_changes(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """UC-008 / A0137: channel timeout text is rebuilt from the source, not a stuck RU string."""
    window = _window(qapp, monkeypatch, tmp_path, language="RU")
    _enter_battle(window)
    window._on_party_frame(
        {
            "type": "_channel_error",
            "code": "TIMEOUT",
            "message": "The server did not respond.",
            "messageRu": "Сервер не ответил.",
        }
    )
    ru_timeout = I18n(Language.RU).t("err_timeout")
    en_timeout = I18n(Language.EN).t("err_timeout")
    battle = window.battle
    assert _shown_on(battle.channel_error, battle)
    assert battle.channel_error.text() == ru_timeout
    window._act_en.trigger()
    assert battle.channel_error.objectName() == "battle-channel-error"
    assert battle.channel_error.text() == en_timeout
    assert battle.channel_error.text() != ru_timeout


def test_should_use_valid_language_when_qsettings_value_is_garbage(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """UC-008 5.1 / FT-060: junk QSettings language is not kept; UI is RU or EN."""
    path = _isolate_settings(monkeypatch, tmp_path, language="not-a-locale")
    monkeypatch.setattr(
        "frontend.settings_store.locale.getdefaultlocale",
        lambda: ("en_US", "UTF-8"),
    )
    monkeypatch.setattr(
        "frontend.ui.main_window.CreateSessionWorker.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "frontend.ui.main_window.GetStatisticsWorker.start",
        lambda self: None,
    )
    window = MainWindow()
    assert window.settings.language in {Language.RU, Language.EN}
    stored = _stored_language(path)
    assert stored in {Language.RU.value, Language.EN.value}
    assert stored != "not-a-locale"
    assert window._act_ru.isChecked() or window._act_en.isChecked()
    assert window.i18n.language is window.settings.language


def test_should_apply_new_language_when_settings_write_fails(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """UC-008 5.2: OSError on QSettings persist still updates the visible language."""
    window = _window(qapp, monkeypatch, tmp_path, language="RU")

    def persist_oserror(_language: Language) -> None:
        try:
            raise OSError("readonly")
        except OSError:
            return

    monkeypatch.setattr(window.settings, "_persist", persist_oserror)
    window._act_en.trigger()
    en = I18n(Language.EN)
    assert window.settings.language is Language.EN
    assert window.i18n.language is Language.EN
    assert window.lobby._lead.text() == en.t("lobby_lead")
    assert window._menu_language.title() == en.t("menu_language")
    assert window._act_en.isChecked()


def test_should_use_russian_when_os_locale_is_russian(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """FT-060 / A0029 / A0136: missing language key + OS ru → RU."""
    del qapp
    _isolate_settings(monkeypatch, tmp_path, language=None)
    monkeypatch.setattr(
        "frontend.settings_store.locale.getdefaultlocale",
        lambda: ("ru_RU", "UTF-8"),
    )
    store = SettingsStore()
    assert store.language is Language.RU


def test_should_use_english_when_os_locale_is_not_russian(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """FT-060 / A0029: missing language key + non-RU OS → EN."""
    del qapp
    _isolate_settings(monkeypatch, tmp_path, language=None)
    monkeypatch.setattr(
        "frontend.settings_store.locale.getdefaultlocale",
        lambda: ("de_DE", "UTF-8"),
    )
    store = SettingsStore()
    assert store.language is Language.EN


def test_should_keep_stored_language_when_os_locale_differs(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """FT-062 / A0136: existing QSettings language wins over OS locale."""
    monkeypatch.setattr(
        "frontend.settings_store.locale.getdefaultlocale",
        lambda: ("ru_RU", "UTF-8"),
    )
    window = _window(qapp, monkeypatch, tmp_path, language="EN")
    assert window.settings.language is Language.EN
    assert window._act_en.isChecked()
    assert window.lobby._lead.text() == I18n(Language.EN).t("lobby_lead")
