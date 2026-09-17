"""Battle fleet tab (S-04-1). QApplication without exec / live window."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from frontend.client.party_frames import apply_shot_resolved
from frontend.client.session_start import session_state_to_scene
from frontend.domain.types import Language, ShipStatus
from frontend.i18n import I18n
from frontend.ui.battle_screen import BattleScreen
from frontend.ui.fleet_panel import FleetPanel
from frontend.ui.main_window import MainWindow
from tests.test_should_fill_computer_fleet_when_session_starts import full_start_payload
from tests.test_should_show_shot_result_when_computer_board_clicked import (
    _connect_channel,
    _enter_battle,
    _shot_resolved,
    _window,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _stop_aim_effects(window: MainWindow) -> None:
    window.battle._aim_anim.stop()
    window.battle.player_board._pulse_timer.stop()
    window.battle.backend_board._pulse_timer.stop()


def _row_texts(panel: FleetPanel) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for index in range(panel._rows.count()):
        widget = panel._rows.itemAt(index).widget()
        if widget is None:
            continue
        labels = widget.findChildren(QLabel)
        assert len(labels) >= 2
        pairs.append((labels[0].text(), labels[1].text()))
    return pairs


def _bound_screen(qapp: QApplication) -> tuple[BattleScreen, I18n]:
    del qapp
    screen = BattleScreen()
    i18n = I18n(Language.RU)
    scene = session_state_to_scene(full_start_payload())
    screen.bind_scene(i18n, Language.RU, scene)
    return screen, i18n


def test_should_show_fleet_tab_when_battle_opens(qapp: QApplication) -> None:
    """FT-009: first battle tab is fleet composition (fleet_title)."""
    screen, i18n = _bound_screen(qapp)
    assert screen._tabs.tabText(0) == i18n.t("fleet_title")


def test_should_show_fleet_headings_when_battle_opens(qapp: QApplication) -> None:
    """FT-009: headings use fleet_player / fleet_backend."""
    screen, i18n = _bound_screen(qapp)
    assert screen._player_fleet._title.objectName() == "CardTitle"
    assert screen._player_fleet._title.text() == i18n.t("fleet_player")
    assert screen._backend_fleet._title.text() == i18n.t("fleet_backend")


def test_should_show_ten_rows_per_side_when_battle_opens(qapp: QApplication) -> None:
    """FT-009: both panels list 10 ships after a complete start payload."""
    screen, _i18n = _bound_screen(qapp)
    assert len(_row_texts(screen._player_fleet)) == 10
    assert len(_row_texts(screen._backend_fleet)) == 10


def test_should_hide_intact_enemy_decks_when_battle_opens(qapp: QApplication) -> None:
    """FT-015: intact Computer bars are empty squares, status INTACT, no hit glyphs."""
    screen, i18n = _bound_screen(qapp)
    intact = i18n.t("status_intact")
    for left, right in _row_texts(screen._backend_fleet):
        assert right == intact
        assert "■" not in left
        assert "□" in left


def test_should_show_player_type_and_intact_when_battle_opens(qapp: QApplication) -> None:
    """FT-009: Player rows show ship type and INTACT at start."""
    screen, i18n = _bound_screen(qapp)
    left, right = _row_texts(screen._player_fleet)[0]
    assert i18n.t("battleship") in left
    assert right == i18n.t("status_intact")


def test_should_show_wounded_without_type_when_player_hits(qapp: QApplication) -> None:
    """FT-015 / FT-019: Computer WOUNDED row is bars only; fleet still 10 rows."""
    screen, i18n = _bound_screen(qapp)
    scene = session_state_to_scene(full_start_payload())
    apply_shot_resolved(
        scene,
        {
            "type": "shotResolved",
            "seq": 1,
            "shooter": "Player",
            "coords": {"column": 2, "row": 3},
            "result": "HIT",
            "affectedCells": [{"coords": {"column": 2, "row": 3}, "mark": "HIT"}],
            "turn": "Player",
            "remainTtlSeconds": 1800,
        },
    )
    screen.bind_scene(i18n, Language.RU, scene)
    rows = _row_texts(screen._backend_fleet)
    assert len(rows) == 10
    left, right = rows[-1]
    assert right == i18n.t("status_wounded")
    assert i18n.t("battleship") not in left
    assert i18n.t("cruiser") not in left
    assert i18n.t("destroyer") not in left
    assert i18n.t("boat") not in left
    assert "■" in left


def test_should_show_computer_type_when_player_sinks(qapp: QApplication) -> None:
    """FT-015 / FT-020: after SUNK the Computer row may show type (boat = 1 SUNK cell)."""
    screen, i18n = _bound_screen(qapp)
    scene = session_state_to_scene(full_start_payload())
    apply_shot_resolved(
        scene,
        {
            "type": "shotResolved",
            "seq": 1,
            "shooter": "Player",
            "coords": {"column": 0, "row": 0},
            "result": "SUNK",
            "affectedCells": [{"coords": {"column": 0, "row": 0}, "mark": "SUNK"}],
            "turn": "Player",
            "remainTtlSeconds": 1800,
        },
    )
    screen.bind_scene(i18n, Language.RU, scene)
    rows = _row_texts(screen._backend_fleet)
    assert len(rows) == 10
    sunk_rows = [
        (left, right)
        for left, right in rows
        if right == i18n.t("status_sunk")
    ]
    assert len(sunk_rows) == 1
    left, _right = sunk_rows[0]
    assert i18n.t("boat") in left
    assert "■" in left


def test_should_show_player_wounded_when_backend_hits(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-019 / FT-036: Backend shotResolved rebinds Player fleet to WOUNDED."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        {
            "type": "shotResolved",
            "seq": 1,
            "shooter": "Backend",
            "coords": {"column": 0, "row": 0},
            "result": "HIT",
            "affectedCells": [{"coords": {"column": 0, "row": 0}, "mark": "HIT"}],
            "turn": "Backend",
            "remainTtlSeconds": 1800,
        }
    )
    left, right = _row_texts(window.battle._player_fleet)[0]
    assert right == window.i18n.t("status_wounded")
    assert window.i18n.t("battleship") in left
    assert window._live_scene is not None
    assert window._live_scene.player_ships[0].status is ShipStatus.WOUNDED
    _stop_aim_effects(window)


def test_should_show_computer_wounded_when_player_hit_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-015 / FT-019: Player HIT frame occupies a typeless WOUNDED Computer slot (10 rows)."""
    window = _window(qapp, monkeypatch, shots=[])
    _enter_battle(window)
    _connect_channel(window)
    window._on_party_frame(
        _shot_resolved(seq=1, column=2, row=3, result="HIT", turn="Player")
    )
    rows = _row_texts(window.battle._backend_fleet)
    assert len(rows) == 10
    left, right = rows[-1]
    assert right == window.i18n.t("status_wounded")
    assert window.i18n.t("battleship") not in left
    assert window.i18n.t("boat") not in left
    _stop_aim_effects(window)
