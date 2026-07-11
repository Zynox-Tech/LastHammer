import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QFrame, QDateEdit, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QMessageBox
)
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtCore import Qt, QDate
import config
import database


class LedgerModule(QMainWindow):
    CHAPTER_TITLE = "Chapter 7 — Debit / Credit Ledger"
    CHAPTER_COLOR = config.RED

    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle(f"Last Hammer  —  {self.CHAPTER_TITLE}")
        self.setMinimumSize(1280, 800)
        self._build_ui()
        self.refresh_table()

    # ─────────────────────────────────────────────────────────
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
        frame.setFixedHeight(100)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(36, 10, 36, 10)

        if os.path.exists(config.LOGO_PATH):
            lbl_logo = QLabel()
            pix = QPixmap(config.LOGO_PATH).scaled(
                72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            layout.addWidget(lbl_logo)
            layout.addSpacing(14)

        accent = QFrame()
        accent.setFixedWidth(7)
        accent.setFixedHeight(56)
        accent.setStyleSheet(
            f"background-color: {self.CHAPTER_COLOR}; border-radius: 4px;")
        layout.addWidget(accent)
        layout.addSpacing(16)

        lbl = QLabel(self.CHAPTER_TITLE)
        lbl.setStyleSheet(
            f"color: {config.WHITE}; font-size: 26px; font-weight: bold;")
        layout.addWidget(lbl)
        layout.addStretch()

        btn_back = QPushButton("←   Back to Dashboard")
        btn_back.setMinimumHeight(46)
        btn_back.setMinimumWidth(210)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #555555; color: white;
                border-radius: 8px; border: none;
                font-size: 15px; font-weight: bold; padding: 10px 20px;
            }
            QPushButton:hover { background-color: #888888; }
        """)
        btn_back.clicked.connect(self._go_back)
        layout.addWidget(btn_back)
        return frame

    # ── Toolbar ───────────────────────────────────────────────
    def _make_toolbar(self):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-bottom: 2px solid #DDDDDD;")
        frame.setFixedHeight(82)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(36, 0, 36, 0)
        layout.setSpacing(18)

        lbl_bal_title = QLabel("Current Balance:")
        lbl_bal_title.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #333333;")
        layout.addWidget(lbl_bal_title)

        self.lbl_balance = QLabel("PKR 0.00")
        self.lbl_balance.setStyleSheet(
            f"color: {config.BLUE}; font-size: 26px; font-weight: bold;")
        layout.addWidget(self.lbl_balance)

        layout.addStretch()

        btn_add = QPushButton("＋   Add Entry")
        btn_add.setMinimumHeight(52)
        btn_add.setMinimumWidth(210)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: #1E8449;
                color: white; border-radius: 10px; border: none;
                font-size: 17px; font-weight: bold; padding: 12px 28px;
            }}
            QPushButton:hover {{ background-color: #27AE60; }}
            QPushButton:pressed {{ background-color: {config.DARK}; }}
        """)
        btn_add.clicked.connect(self._on_add)
        layout.addWidget(btn_add)
        return frame

    # ── Table ─────────────────────────────────────────────────
    def _make_table_area(self):
        frame = QWidget()
        frame.setStyleSheet("background-color: #F2F2F2;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(28, 22, 28, 22)

        cols = ["S.No", "Date", "Description", "Party Name",
                "Debit (PKR)", "Credit (PKR)", "Balance (PKR)", "Actions"]

        self.table = QTableWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)

        self.table.setFont(QFont("Arial", 14))
        hdr_font = QFont("Arial", 14)
        hdr_font.setBold(True)
        self.table.horizontalHeader().setFont(hdr_font)
        self.table.horizontalHeader().setMinimumHeight(52)

        self.table.setColumnWidth(0, 80)    # S.No
        self.table.setColumnWidth(1, 130)   # Date
        self.table.setColumnWidth(7, 220)   # Actions
        for i in [2, 3, 4, 5, 6]:
            self.table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.Stretch)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #F7F7F7;
                gridline-color: #DDDDDD;
                border: 1px solid #CCCCCC;
                border-radius: 8px; font-size: 14px;
            }
            QTableWidget::item { padding: 10px 12px; font-size: 14px; }
            QTableWidget::item:selected {
                background-color: #D6EAF8; color: #1A1A2E; }
            QHeaderView::section {
                background-color: #1A1A2E; color: white;
                font-size: 14px; font-weight: bold;
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
            f"background-color: {config.DARK}; "
            f"border-top: 5px solid {self.CHAPTER_COLOR};")
        frame.setFixedHeight(64)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(36, 0, 36, 0)

        lbl = QLabel("All ledger entries — newest at bottom. "
                     "Edit updates balances automatically.")
        lbl.setStyleSheet("color: #AAAAAA; font-size: 14px;")
        layout.addWidget(lbl)
        layout.addStretch()

        lbl_hint = QLabel("Click  ✏ Edit  (blue)  or  ✕ Delete  (red)  on any row")
        lbl_hint.setStyleSheet("color: #AAAAAA; font-size: 14px;")
        layout.addWidget(lbl_hint)
        return frame

    # ─────────────────────────────────────────────────────────
    def refresh_table(self):
        rows = database.ch7_get_all_entries()
        balance = database.ch7_get_current_balance()
        self.lbl_balance.setText(f"PKR {balance:,.2f}")

        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            ri = self.table.rowCount()
            self.table.insertRow(ri)

            def cell(val, align=Qt.AlignCenter):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(align)
                return item

            self.table.setItem(ri, 0, cell(str(i + 1)))
            self.table.setItem(ri, 1, cell(row["date"]))
            self.table.setItem(
                ri, 2, cell(row["description"],
                            Qt.AlignLeft | Qt.AlignVCenter))
            self.table.setItem(ri, 3, cell(row["party_name"] or "—"))

            # Debit — red text
            d_item = cell(f"{row['debit']:,.2f}" if row["debit"] else "—")
            if row["debit"]:
                d_item.setForeground(QColor(config.RED))
                d_item.setFont(QFont("Arial", 14, QFont.Bold))
            self.table.setItem(ri, 4, d_item)

            # Credit — green text
            c_item = cell(f"{row['credit']:,.2f}" if row["credit"] else "—")
            if row["credit"]:
                c_item.setForeground(QColor("#1E8449"))
                c_item.setFont(QFont("Arial", 14, QFont.Bold))
            self.table.setItem(ri, 5, c_item)

            # Balance — blue text
            b_item = cell(f"PKR {row['balance']:,.2f}")
            b_item.setForeground(QColor(config.BLUE))
            b_item.setFont(QFont("Arial", 14, QFont.Bold))
            self.table.setItem(ri, 6, b_item)

            # Action buttons
            row_id = row["id"]
            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(8, 6, 8, 6)
            al.setSpacing(10)

            btn_edit = QPushButton("✏  Edit")
            btn_edit.setMinimumHeight(40)
            btn_edit.setMinimumWidth(88)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #1B6CA8;
                    color: white; border-radius: 7px; border: none;
                    font-size: 14px; font-weight: bold;
                }
                QPushButton:hover { background-color: #2E86C1; }
                QPushButton:pressed { background-color: #154360; }
            """)
            btn_edit.clicked.connect(
                lambda _, rid=row_id: self._on_edit(rid))

            btn_del = QPushButton("✕  Delete")
            btn_del.setMinimumHeight(40)
            btn_del.setMinimumWidth(96)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #C0392B;
                    color: white; border-radius: 7px; border: none;
                    font-size: 14px; font-weight: bold;
                }
                QPushButton:hover { background-color: #E74C3C; }
                QPushButton:pressed { background-color: #922B21; }
            """)
            btn_del.clicked.connect(
                lambda _, rid=row_id: self._on_delete(rid))

            al.addWidget(btn_edit)
            al.addWidget(btn_del)
            self.table.setCellWidget(ri, 7, aw)
            self.table.setRowHeight(ri, 60)

        self.table.scrollToBottom()
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()

    def _on_add(self):
        dlg = LedgerDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_table()

    def _on_edit(self, row_id):
        rows = database.ch7_get_all_entries()
        row = next((r for r in rows if r["id"] == row_id), None)
        if row:
            dlg = LedgerDialog(row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.refresh_table()

    def _on_delete(self, row_id):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this ledger entry?\n"
            "All balances below it will be automatically recalculated.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.ch7_delete(row_id)
            self.refresh_table()

    def _go_back(self):
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()
            self.parent_dashboard.showMaximized()
        self.close()


# ══════════════════════════════════════════════════════════════
#  ADD / EDIT DIALOG
# ══════════════════════════════════════════════════════════════
class LedgerDialog(QDialog):
    def __init__(self, row=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit Ledger Entry" if row else "Add Ledger Entry")
        self.setFixedWidth(500)
        self.setModal(True)
        self._build_ui()
        if row:
            self._populate(row)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(28, 28, 28, 28)

        lbl = QLabel(
            f"Chapter 7 — Debit / Credit Ledger\n"
            f"{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {config.DARK};")
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        # Larger label font
        def lbl_style(): return "font-size: 14px; font-weight: bold;"

        self.inp_date = QDateEdit()
        self.inp_date.setDate(QDate.currentDate())
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setMinimumHeight(42)
        self.inp_date.setStyleSheet("font-size: 14px; padding: 6px 10px;")
        lbl_d = QLabel("Date:"); lbl_d.setStyleSheet(lbl_style())
        form.addRow(lbl_d, self.inp_date)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText(
            "e.g. Labour payment, Received from buyer...")
        self.inp_desc.setMinimumHeight(42)
        self.inp_desc.setStyleSheet("font-size: 14px; padding: 6px 10px;")
        lbl_de = QLabel("Description:"); lbl_de.setStyleSheet(lbl_style())
        form.addRow(lbl_de, self.inp_desc)

        self.inp_party = QLineEdit()
        self.inp_party.setPlaceholderText("Person / company name (optional)")
        self.inp_party.setMinimumHeight(42)
        self.inp_party.setStyleSheet("font-size: 14px; padding: 6px 10px;")
        lbl_p = QLabel("Party Name:"); lbl_p.setStyleSheet(lbl_style())
        form.addRow(lbl_p, self.inp_party)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #CCCCCC;")
        form.addRow(sep)

        hint = QLabel("Enter EITHER Debit OR Credit — not both.")
        hint.setStyleSheet(
            "color: #888888; font-size: 13px; font-style: italic;")
        form.addRow("", hint)

        self.inp_debit = QDoubleSpinBox()
        self.inp_debit.setRange(0, 99_999_999)
        self.inp_debit.setDecimals(2)
        self.inp_debit.setPrefix("PKR ")
        self.inp_debit.setMinimumHeight(42)
        self.inp_debit.setStyleSheet("font-size: 14px; padding: 6px 10px;")
        lbl_db = QLabel("Debit (Money Out):")
        lbl_db.setStyleSheet("font-size: 14px; font-weight: bold; color: #C0392B;")
        form.addRow(lbl_db, self.inp_debit)

        self.inp_credit = QDoubleSpinBox()
        self.inp_credit.setRange(0, 99_999_999)
        self.inp_credit.setDecimals(2)
        self.inp_credit.setPrefix("PKR ")
        self.inp_credit.setMinimumHeight(42)
        self.inp_credit.setStyleSheet("font-size: 14px; padding: 6px 10px;")
        lbl_cr = QLabel("Credit (Money In):")
        lbl_cr.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E8449;")
        form.addRow(lbl_cr, self.inp_credit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setMinimumHeight(46)
        btn_cancel.setMinimumWidth(120)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #555555; color: white;
                border-radius: 8px; border: none;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #888888; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Entry")
        btn_save.setMinimumHeight(46)
        btn_save.setMinimumWidth(160)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: #1E8449; color: white;
                border-radius: 8px; border: none;
                font-size: 15px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #27AE60; }}
        """)
        btn_save.clicked.connect(self._save)

        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"], "yyyy-MM-dd")
        if d.isValid():
            self.inp_date.setDate(d)
        self.inp_desc.setText(row["description"])
        self.inp_party.setText(row["party_name"] or "")
        self.inp_debit.setValue(float(row["debit"]))
        self.inp_credit.setValue(float(row["credit"]))

    def _save(self):
        desc   = self.inp_desc.text().strip()
        debit  = self.inp_debit.value()
        credit = self.inp_credit.value()

        if not desc:
            QMessageBox.warning(self, "Missing Field",
                                "Please enter a description.")
            return
        if debit > 0 and credit > 0:
            QMessageBox.warning(self, "Invalid Entry",
                "Please enter either Debit OR Credit — not both in one entry.")
            return

        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        party    = self.inp_party.text().strip()

        if self.row:
            database.ch7_edit(
                self.row["id"], date_str, desc, party, debit, credit)
        else:
            database.ch7_add(date_str, desc, party, debit, credit)
        self.accept()