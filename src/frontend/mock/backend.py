from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import QObject, QTimer, Signal

from frontend.domain.fleet import generate_fleet
from frontend.domain.session import IllegalShot, Session
from frontend.domain.types import CellCoordinate, EndReason, SessionStatus, Side
from frontend.mock.heatmap import AimOutcome, aim
from frontend.mock.ledger import Record, Snapshot, seed_ledger, snapshot_from


SLOT_LIMIT = 3


class MockBackend(QObject):
    session_started = Signal(object)
    start_failed = Signal(str)
    shot_resolved = Signal(object)
    shot_rejected = Signal(str)
    backend_aiming = Signal()
    backend_shot = Signal(object)
    game_over = Signal(object)
    session_aborted = Signal()
    ttl_expired = Signal()
    stats_ready = Signal(object)
    stats_failed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session: Session | None = None
        self._records = seed_ledger()
        self._occupied_slots = 0
        self._shot_pending = False
        self._surrender_pending = False
        self._backend_generation = 0
        self._ttl_timer = QTimer(self)
        self._ttl_timer.setInterval(1000)
        self._ttl_timer.timeout.connect(self._check_ttl)

    @property
    def session(self) -> Session | None:
        return self._session

    @property
    def shot_pending(self) -> bool:
        return self._shot_pending

    def start_session(self) -> None:
        if self._occupied_slots >= SLOT_LIMIT:
            QTimer.singleShot(280, lambda: self.start_failed.emit("FT-049"))
            return
        QTimer.singleShot(420, self._finish_start)

    def _finish_start(self) -> None:
        try:
            player_fleet, player_board = generate_fleet(Side.PLAYER)
            backend_fleet, backend_board = generate_fleet(Side.BACKEND)
        except RuntimeError:
            self.start_failed.emit("FT-010")
            return
        self._cancel_backend()
        self._session = Session.create(player_board, backend_board, player_fleet, backend_fleet)
        self._occupied_slots = 1
        self._shot_pending = False
        self._surrender_pending = False
        self._ttl_timer.start()
        self.session_started.emit(self._session)

    def player_shot(self, column: int, row: int) -> None:
        session = self._session
        if session is None:
            self.shot_rejected.emit("FT-069")
            return
        if self._shot_pending:
            self.shot_rejected.emit("FT-051")
            return
        try:
            coords = CellCoordinate(column, row)
        except ValueError:
            self.shot_rejected.emit("FT-070")
            return
        self._shot_pending = True
        QTimer.singleShot(160, lambda: self._resolve_player_shot(coords))

    def _resolve_player_shot(self, coords: CellCoordinate) -> None:
        session = self._session
        if session is None:
            self._shot_pending = False
            self.shot_rejected.emit("FT-069")
            return
        try:
            outcome = session.apply_shot(Side.PLAYER, coords)
        except IllegalShot as error:
            self._shot_pending = False
            self.shot_rejected.emit(error.code)
            return
        self._shot_pending = False
        self.shot_resolved.emit(outcome)
        if outcome.game_over:
            self._finish_game(session)
            return
        if outcome.turn is Side.BACKEND:
            self._schedule_backend(180)

    def surrender(self) -> None:
        session = self._session
        if session is None or self._surrender_pending:
            return
        self._surrender_pending = True
        self._cancel_backend()
        QTimer.singleShot(140, self._finish_surrender)

    def _finish_surrender(self) -> None:
        session = self._session
        self._surrender_pending = False
        if session is None:
            return
        session.surrender()
        self._finish_game(session)

    def request_stats(self) -> None:
        QTimer.singleShot(220, lambda: self.stats_ready.emit(snapshot_from(self._records)))

    def snapshot(self) -> Snapshot:
        return snapshot_from(self._records)

    def occupied_slots(self) -> int:
        return self._occupied_slots

    def _schedule_backend(self, delay_ms: int) -> None:
        generation = self._backend_generation
        QTimer.singleShot(delay_ms, lambda: self._run_backend(generation))

    def _run_backend(self, generation: int) -> None:
        if generation != self._backend_generation:
            return
        session = self._session
        if session is None or session.turn is not Side.BACKEND:
            return
        self.backend_aiming.emit()
        QTimer.singleShot(720, lambda: self._fire_backend(generation))

    def _fire_backend(self, generation: int) -> None:
        if generation != self._backend_generation:
            return
        session = self._session
        if session is None or session.turn is not Side.BACKEND:
            return
        decision = aim(session.player_board, session.player_fleet, session.target_ship_id)
        if decision.outcome is AimOutcome.EMPTY:
            if session.player_fleet.all_sunk():
                session.winner = Side.BACKEND
                session.end_reason = EndReason.FLEET_LOST
                session.status = SessionStatus.GAME_OVER
                self._finish_game(session)
                return
            self._abort_session()
            return
        assert decision.pick is not None
        try:
            outcome = session.apply_shot(Side.BACKEND, decision.pick)
        except IllegalShot:
            self._abort_session()
            return
        self.backend_shot.emit(outcome)
        if outcome.game_over:
            self._finish_game(session)
            return
        if outcome.turn is Side.BACKEND:
            self._schedule_backend(420)

    def _finish_game(self, session: Session) -> None:
        self._cancel_backend()
        self._ttl_timer.stop()
        if session.winner is not None and session.end_reason is not None:
            self._records.append(
                Record(
                    id=str(uuid4()),
                    session_id=session.id,
                    winner=session.winner,
                    shots=len(session.shots),
                    end_reason=session.end_reason,
                )
            )
        self._occupied_slots = 0
        self.game_over.emit(session)

    def _abort_session(self) -> None:
        self._cancel_backend()
        self._ttl_timer.stop()
        self._session = None
        self._occupied_slots = 0
        self.session_aborted.emit()

    def _check_ttl(self) -> None:
        session = self._session
        if session is None:
            return
        if session.remain_ttl().total_seconds() <= 0:
            self._cancel_backend()
            self._ttl_timer.stop()
            self._session = None
            self._occupied_slots = 0
            self.ttl_expired.emit()

    def _cancel_backend(self) -> None:
        self._backend_generation += 1

    def clear_session(self) -> None:
        self._cancel_backend()
        self._ttl_timer.stop()
        self._session = None
        self._shot_pending = False
        self._surrender_pending = False
