from __future__ import annotations

NAVY = {
    "bg": "#07131C",
    "bg_soft": "#0B1C28",
    "panel": "#102433",
    "panel_alt": "#163044",
    "border": "#24556C",
    "text": "#E8F3F8",
    "muted": "#8FAABB",
    "gold": "#E0B14A",
    "teal": "#3EC8B0",
    "danger": "#E05A5A",
    "miss": "#7B93A3",
    "water": "#0A2433",
    "water_hover": "#14435A",
    "ship": "#1E5A72",
    "ship_edge": "#8ED7EC",
    "hit": "#F0C35A",
    "sunk": "#E24B4B",
}


APP_QSS = """
QMainWindow, QDialog, QWidget#Root {
    background: #07131C;
    color: #E8F3F8;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QLabel {
    color: #E8F3F8;
}
QMenuBar {
    background: #0B1C28;
    color: #E8F3F8;
    padding: 4px 8px;
    border-bottom: 1px solid #24556C;
}
QMenuBar::item:selected { background: #163044; }
QMenu {
    background: #102433;
    color: #E8F3F8;
    border: 1px solid #24556C;
}
QMenu::item:selected { background: #1B3D52; }
QPushButton {
    background: #163044;
    color: #E8F3F8;
    border: 1px solid #2A617A;
    border-radius: 10px;
    padding: 8px 16px;
    min-height: 18px;
}
QPushButton:hover { background: #1C3D54; border-color: #3EC8B0; }
QPushButton:pressed { background: #122A3A; }
QPushButton:disabled { color: #6E8796; border-color: #1B3A4C; }
QPushButton#Primary {
    background: #E0B14A;
    color: #1A1408;
    border: none;
    font-weight: 600;
    padding: 12px 22px;
    font-size: 15px;
}
QPushButton#Primary:hover { background: #F0C35A; }
QPushButton#Danger {
    background: #5A2428;
    color: #FFD4D4;
    border: 1px solid #E05A5A;
}
QPushButton#Danger:hover { background: #6E2C32; }
QPushButton#Ghost {
    background: transparent;
    border: 1px solid #2A617A;
}
QLabel#Kicker {
    color: #3EC8B0;
    letter-spacing: 2px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#Hero {
    font-size: 42px;
    font-weight: 700;
    color: #E8F3F8;
}
QLabel#Lead { color: #8FAABB; font-size: 14px; }
QLabel#Muted { color: #8FAABB; }
QLabel#lobby-empty { color: #8FAABB; }
QLabel#lobby-loading { color: #E0B14A; }
QLabel#battle-computer-turn { color: #3EC8B0; font-weight: 600; }
QLabel#lobby-error { color: #E05A5A; }
QLabel#lobby-stats-empty, QLabel#stats-empty { color: #8FAABB; }
QLabel#lobby-stats-loading, QLabel#stats-loading { color: #E0B14A; }
QLabel#lobby-stats-error, QLabel#stats-error { color: #E05A5A; }
QLabel#CardTitle { color: #8FAABB; font-size: 11px; }
QLabel#CardValue { font-size: 26px; font-weight: 700; color: #E0B14A; }
QFrame#Card, QFrame#Panel {
    background: #102433;
    border: 1px solid #24556C;
    border-radius: 16px;
}
QTableWidget {
    background: #0B1C28;
    alternate-background-color: #102433;
    color: #E8F3F8;
    gridline-color: #1B3A4C;
    border: 1px solid #24556C;
    border-radius: 10px;
}
QHeaderView::section {
    background: #163044;
    color: #8FAABB;
    padding: 8px;
    border: none;
    border-right: 1px solid #1B3A4C;
    font-weight: 600;
}
QScrollBar:vertical {
    background: #0B1C28;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2A617A;
    border-radius: 4px;
    min-height: 24px;
}
QProgressBar {
    background: #0B1C28;
    border: 1px solid #24556C;
    border-radius: 6px;
    text-align: center;
    color: #E8F3F8;
    height: 12px;
}
QProgressBar::chunk { background: #3EC8B0; border-radius: 5px; }
QTabWidget::pane {
    border: 1px solid #24556C;
    border-radius: 12px;
    background: #102433;
    top: -1px;
}
QTabBar::tab {
    background: #0B1C28;
    color: #8FAABB;
    padding: 8px 16px;
    border: 1px solid #24556C;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
}
QTabBar::tab:selected { background: #102433; color: #E8F3F8; }
QTabWidget QLabel { color: #E8F3F8; }
QTabWidget QLabel#Muted { color: #E8F3F8; }
QLineEdit {
    background: #0B1C28;
    border: 1px solid #24556C;
    border-radius: 8px;
    padding: 6px 10px;
    color: #E8F3F8;
    selection-background-color: #2A617A;
}
"""
