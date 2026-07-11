import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QFrame, QDateEdit, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QDate
import config


class BaseModule(QMainWindow):
    CHAPTER_TITLE = "Module"
    CHAPTER_COLOR = config.DARK
    COLUMNS = []

    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setMinimumSize(1280, 800)
        self.setWindowTitle(f"Last Hammer  —  {self.CHAPTER_TITLE}")
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_header())
        root.addWidget(self._make_toolbar())
        root.addWidget(self._make_table_area(), 1)
        root.addWidget(self._make_footer())

    # ── Header ────────────────────────────────────────────────
    def _make_header(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {config.DARK};")
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)

        if os.path.exists(config.LOGO_PATH):
            lbl_logo = QLabel()
            pix = QPixmap(config.LOGO_PATH).scaled(
                64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            layout.addWidget(lbl_logo)
            layout.addSpacing(12)

        accent = QFrame()
        accent.setFixedWidth(6)
        accent.setFixedHeight(52)
        accent.setStyleSheet(
            f"background-color: {self.CHAPTER_COLOR}; border-radius: 3px;")
        layout.addWidget(accent)
        layout.addSpacing(14)

        lbl = QLabel(self.CHAPTER_TITLE)
        lbl.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(lbl)
        layout.addStretch()

        btn_back = QPushButton("←  Back to Dashboard")
        btn_back.setFixedHeight(44)
        btn_back.setMinimumWidth(200)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #444455; color: white;
                border-radius: 8px; border: none;
                font-size: 14px; font-weight: bold; padding: 0 20px;
            }
            QPushButton:hover { background-color: #6666AA; }
        """)
        btn_back.clicked.connect(self._go_back)
        layout.addWidget(btn_back)
        return frame

    # ── Toolbar ───────────────────────────────────────────────
    def _make_toolbar(self):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-bottom: 2px solid #DDDDDD;")
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(20)

        # Date section
        date_col = QVBoxLayout()
        date_col.setSpacing(3)
        lbl_hint = QLabel("DATE FOR NEW ENTRIES")
        lbl_hint.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #AAAAAA; letter-spacing: 1px;")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(46)
        self.date_edit.setFixedWidth(210)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                font-size: 16px; font-weight: bold;
                padding: 6px 12px; border: 2px solid #DDDDDD;
                border-radius: 8px; background: white; color: #1A1A2E;
            }
            QDateEdit:focus { border: 2px solid #C0392B; }
        """)
        date_col.addWidget(lbl_hint)
        date_col.addWidget(self.date_edit)
        layout.addLayout(date_col)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #EEEEEE;")
        layout.addWidget(div)

        # Total section
        total_col = QVBoxLayout()
        total_col.setSpacing(3)
        lbl_total_hint = QLabel("GRAND TOTAL (ALL ENTRIES)")
        lbl_total_hint.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #AAAAAA; letter-spacing: 1px;")
        self.lbl_total = QLabel("PKR 0")
        self.lbl_total.setStyleSheet(
            f"color: {self.CHAPTER_COLOR}; font-size: 26px; font-weight: bold;")
        total_col.addWidget(lbl_total_hint)
        total_col.addWidget(self.lbl_total)
        layout.addLayout(total_col)

        layout.addStretch()

        # BIG green Add button
        btn_add = QPushButton("  ＋   ADD NEW ENTRY")
        btn_add.setFixedHeight(62)
        btn_add.setMinimumWidth(270)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ECC71, stop:1 #1E8449);
                color: white; border-radius: 12px; border: none;
                font-size: 19px; font-weight: bold; letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #58D68D, stop:1 #27AE60);
            }}
            QPushButton:pressed {{ background: {config.DARK}; }}
        """)
        btn_add.clicked.connect(self._on_add)
        layout.addWidget(btn_add)
        return frame

    # ── Table ─────────────────────────────────────────────────
    def _make_table_area(self):
        frame = QWidget()
        frame.setStyleSheet("background-color: #EFEFEF;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 18, 24, 18)

        all_cols = ["S.No"] + self.COLUMNS + ["Actions"]

        self.table = QTableWidget()
        self.table.setColumnCount(len(all_cols))
        self.table.setHorizontalHeaderLabels(all_cols)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(True)

        self.table.setFont(QFont("Arial", 14))
        hdr = QFont("Arial", 13)
        hdr.setBold(True)
        self.table.horizontalHeader().setFont(hdr)
        self.table.horizontalHeader().setMinimumHeight(50)

        n = len(all_cols)
        self.table.setColumnWidth(0, 75)
        self.table.setColumnWidth(n - 1, 240)
        for i in range(1, n - 1):
            self.table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.Stretch)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #F0F4FF;
                gridline-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-radius: 10px; font-size: 14px;
            }
            QTableWidget::item { padding: 10px 14px; }
            QTableWidget::item:selected {
                background-color: #D6EAF8; color: #1A1A2E; }
            QHeaderView::section {
                background-color: #1A1A2E; color: white;
                font-size: 13px; font-weight: bold;
                padding: 12px 10px; border: none;
                border-right: 1px solid #2C2C4E;
            }
        """)

        layout.addWidget(self.table)
        return frame

    # ── Footer ────────────────────────────────────────────────
    def _make_footer(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {config.DARK};"
            f"border-top: 4px solid {self.CHAPTER_COLOR};")
        frame.setFixedHeight(60)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)

        self.lbl_footer_total = QLabel("Grand Total (All Entries):   PKR 0")
        self.lbl_footer_total.setStyleSheet(
            f"color: {self.CHAPTER_COLOR}; font-size: 17px; font-weight: bold;")
        layout.addWidget(self.lbl_footer_total)
        layout.addStretch()

        hint = QLabel("✏  Edit = Blue       ✕  Delete = Red")
        hint.setStyleSheet("color: #888888; font-size: 13px;")
        layout.addWidget(hint)
        return frame

    # ─────────────────────────────────────────────────────────
    def current_date_str(self):
        return self.date_edit.date().toString("yyyy-MM-dd")

    def refresh_table(self):
        rows  = self.get_all_rows()
        total = self.get_grand_total()
        self._populate_table(rows)
        self.lbl_total.setText(f"PKR {total:,.0f}")
        self.lbl_footer_total.setText(
            f"Grand Total (All Entries):   PKR {total:,.0f}")
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()

    def _populate_table(self, rows):
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            cells = self.row_to_cells(row)
            ri = self.table.rowCount()
            self.table.insertRow(ri)

            sno = QTableWidgetItem(str(i + 1))
            sno.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(ri, 0, sno)

            for j, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                # Date column styling (last data column)
                if j == len(cells) - 1:
                    item.setForeground(QColor("#1B4F72"))
                    item.setFont(QFont("Arial", 13, QFont.Bold))
                self.table.setItem(ri, j + 1, item)

            # Action buttons
            act_col = len(cells) + 1
            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(10, 8, 10, 8)
            al.setSpacing(10)
            row_id = row["id"]

            btn_edit = QPushButton("  ✏  Edit")
            btn_edit.setMinimumHeight(44)
            btn_edit.setMinimumWidth(104)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3498DB, stop:1 #1B6CA8);
                    color: white; border-radius: 8px; border: none;
                    font-size: 14px; font-weight: bold;
                }
                QPushButton:hover { background: #2980B9; }
                QPushButton:pressed { background: #154360; }
            """)
            btn_edit.clicked.connect(lambda _, rid=row_id: self._on_edit(rid))

            btn_del = QPushButton("  ✕  Delete")
            btn_del.setMinimumHeight(44)
            btn_del.setMinimumWidth(112)
            btn_del.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #E74C3C, stop:1 #C0392B);
                    color: white; border-radius: 8px; border: none;
                    font-size: 14px; font-weight: bold;
                }
                QPushButton:hover { background: #E74C3C; }
                QPushButton:pressed { background: #922B21; }
            """)
            btn_del.clicked.connect(lambda _, rid=row_id: self._on_delete(rid))

            al.addWidget(btn_edit)
            al.addWidget(btn_del)
            self.table.setCellWidget(ri, act_col, aw)
            self.table.setRowHeight(ri, 64)

    def _on_add(self):
        self.open_add_dialog(self.current_date_str())

    def _on_edit(self, row_id):
        self.open_edit_dialog(row_id)

    def _on_delete(self, row_id):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this entry?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.do_delete(row_id)
            self.refresh_table()

    def _go_back(self):
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()
            self.parent_dashboard.showMaximized()
        self.close()

    def get_all_rows(self):              return []
    def row_to_cells(self, row):         return []
    def get_grand_total(self):           return 0.0
    def open_add_dialog(self, date_str): pass
    def open_edit_dialog(self, row_id):  pass
    def do_delete(self, row_id):         pass