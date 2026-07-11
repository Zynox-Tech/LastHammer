# config.py  —  App-wide constants and PyQt5 stylesheet

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

APP_NAME    = "Last Hammer — Expenditure Management System"
APP_VERSION = "1.0"

# ─── COLORS ───────────────────────────────────────────────────
RED    = "#C0392B"
DARK   = "#1A1A2E"
WHITE  = "#FFFFFF"
LIGHT  = "#F8F9FA"
GRAY   = "#EEEEEE"
MID    = "#CCCCCC"
GREEN  = "#1E8449"
ORANGE = "#CA6F1E"
BLUE   = "#1B4F72"

# ─── GLOBAL STYLESHEET ────────────────────────────────────────
STYLESHEET = """
/* ── Main Window & Backgrounds ── */
QMainWindow, QDialog {
    background-color: #F8F9FA;
}
QWidget {
    font-family: Arial;
    font-size: 13px;
    color: #1A1A2E;
}

/* ── Buttons ── */
QPushButton {
    background-color: #1A1A2E;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2C2C4E;
}
QPushButton:pressed {
    background-color: #C0392B;
}
QPushButton#btn_add {
    background-color: #1E8449;
}
QPushButton#btn_add:hover {
    background-color: #27AE60;
}
QPushButton#btn_edit {
    background-color: #1B4F72;
    padding: 4px 12px;
    font-size: 12px;
}
QPushButton#btn_edit:hover {
    background-color: #2E86C1;
}
QPushButton#btn_delete {
    background-color: #C0392B;
    padding: 4px 12px;
    font-size: 12px;
}
QPushButton#btn_delete:hover {
    background-color: #E74C3C;
}
QPushButton#btn_back {
    background-color: #555555;
}
QPushButton#btn_back:hover {
    background-color: #777777;
}
QPushButton#btn_email {
    background-color: #1B4F72;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#btn_email:hover {
    background-color: #2E86C1;
}
QPushButton#btn_report {
    background-color: #C0392B;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#btn_report:hover {
    background-color: #E74C3C;
}

/* ── Input Fields ── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background-color: white;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus,
QSpinBox:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #C0392B;
}

/* ── Table ── */
QTableWidget {
    background-color: white;
    gridline-color: #EEEEEE;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    font-size: 13px;
}
QTableWidget::item {
    padding: 6px 8px;
}
QTableWidget::item:selected {
    background-color: #D6EAF8;
    color: #1A1A2E;
}
QHeaderView::section {
    background-color: #1A1A2E;
    color: white;
    font-weight: bold;
    font-size: 13px;
    padding: 8px;
    border: none;
    border-right: 1px solid #2C2C4E;
}

/* ── Labels ── */
QLabel#lbl_title {
    font-size: 22px;
    font-weight: bold;
    color: #1A1A2E;
}
QLabel#lbl_total {
    font-size: 15px;
    font-weight: bold;
    color: #C0392B;
}
QLabel#lbl_section {
    font-size: 13px;
    font-weight: bold;
    color: #1B4F72;
}

/* ── Date Picker ── */
QDateEdit::drop-down {
    border: none;
    width: 20px;
}

/* ── Scroll bars ── */
QScrollBar:vertical {
    width: 10px;
    background: #F8F9FA;
}
QScrollBar::handle:vertical {
    background: #CCCCCC;
    border-radius: 5px;
    min-height: 30px;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    margin-top: 12px;
    font-weight: bold;
    color: #1A1A2E;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* ── Message Box ── */
QMessageBox {
    background-color: #F8F9FA;
}
"""