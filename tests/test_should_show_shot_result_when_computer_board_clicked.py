"""Battle UI shot / party channel (UC-002). No QApplication.exec, WS start patched."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from frontend.client.session_start import StartSessionOutcome, session_state_to_scene
from frontend.domain.types import Mark
from frontend.ui.main_window import MainWindow
from tests.test_should_post_sessions_when_client_starts import created_session_payload


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _window(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    *,
    shots: list[tuple[int, int]] | None = None,
) -> MainWindow:
    del qapp
    monkeypatch.setattr(
        "frontend.ui.main_window.CreateSessionWorker.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "frontend.ui.main_window.GetStatisticsWorker.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "frontend.ui.main_window.PartyChannelWorker.start",
        lambda self: None,
    )
    if shots is not None:

        def fake_send(self, column: int, row: int) -> None:
            shots.append((column, row))

        monkeypatch.setattr(
            "frontend.ui.main_window.PartyChannelWorker.send_shot",
            fake_send,
        )

    def forbid_http(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("REST must not be used for shots")

    monkeypatch.setattr("urllib.request.urlopen", forbid_http)
    return MainWindow()


def _shown_on(widget: QWidget, ancestor: QWidget) -> bool:
    """Local setVisible flag. QWidget.isVisible() is False until ancestors are shown."""
    return widget.isVisibleTo(ancestor)


def _enter_battle(window: MainWindow) -> None:
    window.lobby.start_button.click()
    scene = session_state_to_scene(created_session_payload())
    window._on_start_outcome(
        StartSessionOutcome(kind="success", scene=scene, http_status=201)
    )
    window._party_start_timer.stop()


def _connect_channel(window: MainWindow) -> None:
    window._open_party(window._party_token)
    window._on_party_frame(
        {"type": "sessionSnapshot", "session": created_session_payload()}
    )


def _shot_resolved(
    *,
    seq: int,
    column: int,
    row: int,
    result: str,
    turn: str,
    affected: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    cells = affected or [
        {"coords": {"column": column, "row": row}, "mark": result},
    ]
    return {
        "type": "shotResolved",
        "seq": seq,
        "shooter": "Player",
        "coords": {"column": column, "row": row},
        "result": result,
        "affectedCells": cells,
        "turn": turn,
        "remainTtlSeconds": 1800,
    }


def test_should_show_channel_loading_when_battle_opens(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-002: after start, party channel is loading before snapshot."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    battle = window.battle
    assert battle.backend_board.objectName() == "computer-board"
    assert battle.channel_loading.objectName() == "battle-channel-loading"
    assert window._channel_phase == "loading"
    assert _shown_on(battle.channel_loading, battle)
    assert not _shown_on(battle.channel_error, battle)
    assert not _shown_on(battle.shot_error, battle)


def test_should_show_shot_empty_when_snapshot_has_no_shots(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-002: empty shot log is not an error after a successful snapshot."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    _connect_channel(window)
    battle = window.battle
    assert window._channel_phase == "success"
    assert window._shot_phase == "empty"
    assert battle.shot_empty.objectName() == "battle-shot-empty"
    assert _shown_on(battle.shot_empty, battle)
    assert not _shown_on(battle.shot_error, battle)
    assert not _shown_on(battle.channel_error, battle)
    assert not _shown_on(battle.channel_loading, battle)
    assert battle.shot_empty.text() == window.i18n.t("shot_empty")


def test_should_send_ws_shot_when_computer_board_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-017 / FT-055: Computer board click sends WS shot, not REST /shots."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    assert window.battle.backend_board.objectName() == "computer-board"
    window.battle.backend_board.cell_clicked.emit(3, 5)
    assert shots == [(3, 5)]
    assert window._party is not None
    assert window._party._url.endswith(
        f"/sessions/{window._live_scene.session_id}/ws"
    )
    assert "/shots" not in window._party._url


def test_should_show_shot_loading_when_cell_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0116 / UC-002: pending shot shows battle-shot-loading until a frame arrives."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    battle = window.battle
    window.battle.backend_board.cell_clicked.emit(1, 2)
    assert window._shot_phase == "loading"
    assert battle.shot_loading.objectName() == "battle-shot-loading"
    assert _shown_on(battle.shot_loading, battle)
    assert not _shown_on(battle.shot_empty, battle)
    assert not _shown_on(battle.shot_error, battle)


def test_should_ignore_second_click_when_shot_pending(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A0116: second Computer board click while loading does not send another shot."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    board = window.battle.backend_board
    board.cell_clicked.emit(0, 0)
    board.cell_clicked.emit(1, 1)
    assert shots == [(0, 0)]


def test_should_not_send_shot_when_channel_still_loading(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-002: click before snapshot does not send a shot command."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    window.battle.backend_board.cell_clicked.emit(4, 4)
    assert shots == []
    assert window._shot_phase != "loading"


def test_should_not_send_shot_when_player_board_clicked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-048: click on player-board does not send a party shot."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    assert window.battle.player_board.objectName() == "player-board"
    window.battle.player_board.cell_clicked.emit(0, 0)
    assert shots == []
    assert window._shot_phase == "empty"


def test_should_show_miss_when_shot_resolved_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-018: MISS frame paints Computer cell and leaves shot success, not error."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    window.battle.backend_board.cell_clicked.emit(9, 9)
    window._on_party_frame(
        _shot_resolved(seq=1, column=9, row=9, result="MISS", turn="Backend")
    )
    battle = window.battle
    assert battle.backend_board._cells[9][9].mark is Mark.MISS
    assert window._shot_phase == "success"
    assert not _shown_on(battle.shot_error, battle)
    assert not _shown_on(battle.shot_loading, battle)
    assert not _shown_on(battle.shot_empty, battle)


def test_should_show_hit_when_shot_resolved_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-019: HIT frame paints Computer cell; Player still to move."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    window.battle.backend_board.cell_clicked.emit(2, 3)
    window._on_party_frame(
        _shot_resolved(seq=1, column=2, row=3, result="HIT", turn="Player")
    )
    assert window.battle.backend_board._cells[3][2].mark is Mark.HIT
    assert window._live_scene is not None
    assert window._live_scene.player_turn is True
    assert window._shot_phase == "success"


def test_should_show_sunk_when_shot_resolved_arrives(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-020 / FT-021: SUNK plus perimeter MISS on Computer board."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    window.battle.backend_board.cell_clicked.emit(0, 2)
    window._on_party_frame(
        _shot_resolved(
            seq=1,
            column=0,
            row=2,
            result="SUNK",
            turn="Player",
            affected=[
                {"coords": {"column": 0, "row": 2}, "mark": "SUNK"},
                {"coords": {"column": 0, "row": 1}, "mark": "MISS"},
                {"coords": {"column": 1, "row": 2}, "mark": "MISS"},
            ],
        )
    )
    cells = window.battle.backend_board._cells
    assert cells[2][0].mark is Mark.SUNK
    assert cells[1][0].mark is Mark.MISS
    assert cells[2][1].mark is Mark.MISS
    assert window._shot_phase == "success"


def test_should_show_shot_error_when_cell_already_checked(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FT-044: server error frame → battle-shot-error; Computer cell stays Unchecked."""
    shots: list[tuple[int, int]] = []
    window = _window(qapp, monkeypatch, shots=shots)
    _enter_battle(window)
    _connect_channel(window)
    window.battle.backend_board.cell_clicked.emit(4, 4)
    window._on_party_frame(
        {
            "type": "error",
            "code": "SHOT_CELL_CHECKED",
            "message": "Cell already checked.",
            "messageRu": "Клетка уже проверена.",
        }
    )
    battle = window.battle
    assert window._shot_phase == "error"
    assert battle.shot_error.objectName() == "battle-shot-error"
    assert _shown_on(battle.shot_error, battle)
    assert not _shown_on(battle.shot_empty, battle)
    assert not _shown_on(battle.shot_loading, battle)
    assert battle.shot_error.text() == "Клетка уже проверена."
    assert battle.backend_board._cells[4][4].mark is Mark.UNCHECKED


def test_should_show_channel_error_when_handshake_times_out(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UC-002 5.2: channel TIMEOUT is channel error, not shot-empty."""
    window = _window(qapp, monkeypatch)
    _enter_battle(window)
    window._on_party_frame(
        {
            "type": "_channel_error",
            "code": "TIMEOUT",
            "message": "The server did not respond.",
            "messageRu": "Сервер не ответил.",
        }
    )
    battle = window.battle
    assert window._channel_phase == "error"
    assert battle.channel_error.objectName() == "battle-channel-error"
    assert _shown_on(battle.channel_error, battle)
    assert not _shown_on(battle.channel_loading, battle)
    assert not _shown_on(battle.shot_empty, battle)
    assert battle.channel_error.text() == window.i18n.t("err_timeout")
