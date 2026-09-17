from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from frontend.client.session_start import StartSessionOutcome, create_session
from frontend.client.statistics import StatisticsOutcome, get_statistics


class CreateSessionWorker(QThread):
    finished_outcome = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        outcome: StartSessionOutcome = create_session()
        self.finished_outcome.emit(outcome)


class GetStatisticsWorker(QThread):
    finished_outcome = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        outcome: StatisticsOutcome = get_statistics()
        self.finished_outcome.emit(outcome)
