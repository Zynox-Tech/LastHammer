from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QPushButton,
    QDateEdit, QMessageBox, QFrame, QSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import database, config
from ui.base_module import BaseModule


class ExcavatorModule(BaseModule):
    CHAPTER_TITLE = "Chapter 3 — Excavator Expenditure"
    CHAPTER_COLOR = "#0E6655"
    COLUMNS = ["Details", "Hours", "Rate/Hr", "Total (PKR)",
               "Cash Advance", "Diesel Advance", "Cash Used", "Diesel Used",
               "Balance", "Date"]

    def get_all_rows(self):
        return database.ch3_get_all()

    def row_to_cells(self, row):
        ca  = (row["cash_advance"] if "cash_advance" in row.keys() else 0) or 0
        da  = (row["diesel_advance"] if "diesel_advance" in row.keys() else 0) or 0
        cu  = (row["cash_used"] if "cash_used" in row.keys() else 0) or 0
        du  = (row["diesel_used"] if "diesel_used" in row.keys() else 0) or 0
        bal = (row["balance_due"] if "balance_due" in row.keys() else 0) or 0
        return [
            (row["details"] if "details" in row.keys() else None) or "—",
            str(row["hours_worked"]),
            f"PKR {row['rate_per_hour']:,.0f}",
            f"PKR {row['total_amount']:,.2f}",
            f"PKR {ca:,.0f}" if ca else "—",
            f"PKR {da:,.0f}" if da else "—",
            f"PKR {cu:,.0f}" if cu else "—",
            f"PKR {du:,.0f}" if du else "—",
            f"PKR {bal:,.2f}",
            row["date"],
        ]

    def get_grand_total(self):
        return database.ch3_grand_total()

    def open_add_dialog(self, date_str):
        dlg = ExcavatorDialog(date_str, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_table()

    def open_edit_dialog(self, row_id):
        row = database.ch3_get_by_id(row_id)
        if row:
            dlg = ExcavatorDialog(row["date"], row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.refresh_table()

    def do_delete(self, row_id):
        database.ch3_delete(row_id)


class ExcavatorDialog(QDialog):
    def __init__(self, date_str, row=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit Entry" if row else "Add Entry")
        self.setFixedWidth(560)
        self.setModal(True)
        self._build_ui(date_str)
        if row:
            self._populate(row)

    def _build_ui(self, date_str):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 24, 28, 24)

        lbl = QLabel(f"Chapter 3 — Excavator Expenditure\n"
                     f"{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(f"font-size:16px; font-weight:bold; color:{config.DARK};")
        layout.addWidget(lbl)

        # Info box explaining the logic
        info = QLabel(
            "💡  Give the excavator operator a CASH ADVANCE and/or DIESEL ADVANCE first.\n"
            "     Then record work done (hours). As he works, deduct from the advance.")
        info.setStyleSheet(
            "background:#EBF5FB; color:#1B4F72; border-radius:8px; "
            "padding:10px 14px; font-size:12px; border:1px solid #AED6F1;")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        def L(t):
            l = QLabel(t)
            l.setStyleSheet("font-size:13px; font-weight:bold;")
            return l

        def spin(prefix="PKR ", max_val=9999999, decimals=2, suffix=""):
            s = QDoubleSpinBox()
            s.setRange(0, max_val)
            s.setDecimals(decimals)
            if prefix: s.setPrefix(prefix)
            if suffix: s.setSuffix(suffix)
            s.setMinimumHeight(42)
            s.setStyleSheet(
                "font-size:13px; padding:4px 8px; "
                "border:2px solid #DDDDDD; border-radius:8px;")
            return s

        self.inp_date = QDateEdit()
        d = QDate.fromString(date_str, "yyyy-MM-dd")
        self.inp_date.setDate(d if d.isValid() else QDate.currentDate())
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setMinimumHeight(42)
        self.inp_date.setStyleSheet(
            "font-size:14px; font-weight:bold; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        form.addRow(L("Date:"), self.inp_date)

        self.inp_details = QLineEdit()
        self.inp_details.setPlaceholderText("e.g. Marble extraction — East pit  (optional)")
        self.inp_details.setMinimumHeight(42)
        self.inp_details.setStyleSheet(
            "font-size:13px; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        form.addRow(L("Details:"), self.inp_details)

        # Work done section
        sep1 = QLabel("── WORK DONE ──────────────────────────")
        sep1.setStyleSheet("color:#AAAAAA; font-size:11px;")
        form.addRow("", sep1)

        self.inp_hours = QDoubleSpinBox()
        self.inp_hours.setRange(0, 9999)
        self.inp_hours.setDecimals(1)
        self.inp_hours.setSuffix(" hrs")
        self.inp_hours.setMinimumHeight(42)
        self.inp_hours.setStyleSheet(
            "font-size:13px; padding:4px 8px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        self.inp_hours.valueChanged.connect(self._recalc)
        form.addRow(L("Hours Worked:"), self.inp_hours)

        self.inp_rate = spin("PKR ", 99999, 0)
        self.inp_rate.setValue(2200)
        self.inp_rate.setSuffix("/hr")
        self.inp_rate.valueChanged.connect(self._recalc)
        form.addRow(L("Rate per Hour:"), self.inp_rate)

        self.lbl_total = QLabel("PKR 0")
        self.lbl_total.setStyleSheet(
            f"font-size:18px; font-weight:bold; color:{config.DARK};")
        form.addRow(L("Work Total:"), self.lbl_total)

        # Advance section
        sep2 = QLabel("── ADVANCES GIVEN ──────────────────────")
        sep2.setStyleSheet("color:#AAAAAA; font-size:11px;")
        form.addRow("", sep2)

        self.inp_cash_adv = spin()
        self.inp_cash_adv.valueChanged.connect(self._recalc)
        form.addRow(L("Cash Advance:"), self.inp_cash_adv)

        self.inp_diesel_adv = spin()
        self.inp_diesel_adv.valueChanged.connect(self._recalc)
        form.addRow(L("Diesel Advance\n(PKR value):"), self.inp_diesel_adv)

        # Used section
        sep3 = QLabel("── DEDUCTED / USED ─────────────────────")
        sep3.setStyleSheet("color:#AAAAAA; font-size:11px;")
        form.addRow("", sep3)

        self.inp_cash_used = spin()
        self.inp_cash_used.valueChanged.connect(self._recalc)
        form.addRow(L("Cash Used/Deducted:"), self.inp_cash_used)

        self.inp_diesel_used = spin()
        self.inp_diesel_used.valueChanged.connect(self._recalc)
        form.addRow(L("Diesel Used/Deducted\n(PKR value):"), self.inp_diesel_used)

        # Balance
        sep4 = QLabel("────────────────────────────────────────")
        sep4.setStyleSheet("color:#AAAAAA; font-size:11px;")
        form.addRow("", sep4)

        self.lbl_balance = QLabel("PKR 0")
        self.lbl_balance.setStyleSheet(
            f"font-size:18px; font-weight:bold; color:{config.RED};")
        form.addRow(L("Balance Due:"), self.lbl_balance)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        btn_c = QPushButton("Cancel")
        btn_c.setMinimumHeight(46)
        btn_c.setStyleSheet(
            "QPushButton{background:#555;color:white;border-radius:8px;"
            "border:none;font-size:15px;font-weight:bold;}"
            "QPushButton:hover{background:#888;}")
        btn_c.clicked.connect(self.reject)
        btn_s = QPushButton("💾  Save Entry")
        btn_s.setMinimumHeight(46)
        btn_s.setMinimumWidth(160)
        btn_s.setStyleSheet(
            "QPushButton{background:#0E6655;color:white;border-radius:8px;"
            "border:none;font-size:15px;font-weight:bold;}"
            "QPushButton:hover{background:#17A589;}")
        btn_s.clicked.connect(self._save)
        btn_row.addWidget(btn_c)
        btn_row.addStretch()
        btn_row.addWidget(btn_s)
        layout.addLayout(btn_row)

    def _recalc(self):
        total   = self.inp_hours.value() * self.inp_rate.value()
        balance = (self.inp_cash_adv.value() + self.inp_diesel_adv.value()) - \
                  (self.inp_cash_used.value() + self.inp_diesel_used.value())
        self.lbl_total.setText(f"PKR {total:,.2f}")
        color = config.RED if balance > 0 else "#1E8449"
        self.lbl_balance.setText(f"PKR {balance:,.2f}")
        self.lbl_balance.setStyleSheet(
            f"font-size:18px; font-weight:bold; color:{color};")

    def _populate(self, row):
        d = QDate.fromString(row["date"], "yyyy-MM-dd")
        if d.isValid():
            self.inp_date.setDate(d)
        self.inp_details.setText((row["details"] if "details" in row.keys() else None) or "")
        self.inp_hours.setValue(float(row["hours_worked"]))
        self.inp_rate.setValue(float(row["rate_per_hour"]))
        self.inp_cash_adv.setValue(float((row["cash_advance"] if "cash_advance" in row.keys() else None) or (row["paid_cash"] if "paid_cash" in row.keys() else None) or 0))
        self.inp_diesel_adv.setValue(float((row["diesel_advance"] if "diesel_advance" in row.keys() else None) or (row["paid_diesel"] if "paid_diesel" in row.keys() else None) or 0))
        self.inp_cash_used.setValue(float((row["cash_used"] if "cash_used" in row.keys() else None) or 0))
        self.inp_diesel_used.setValue(float((row["diesel_used"] if "diesel_used" in row.keys() else None) or 0))
        self._recalc()

    def _save(self):
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        conn = database.get_connection()
        total   = self.inp_hours.value() * self.inp_rate.value()
        balance = (self.inp_cash_adv.value() + self.inp_diesel_adv.value()) - \
                  (self.inp_cash_used.value() + self.inp_diesel_used.value())
        if self.row:
            conn.execute(
                "UPDATE excavator_expenditure SET date=?, details=?, hours_worked=?, "
                "rate_per_hour=?, total_amount=?, paid_cash=?, paid_diesel=?, "
                "balance_due=?, cash_advance=?, diesel_advance=?, cash_used=?, diesel_used=? "
                "WHERE id=?",
                (date_str, self.inp_details.text().strip(),
                 self.inp_hours.value(), self.inp_rate.value(), total,
                 self.inp_cash_adv.value(), self.inp_diesel_adv.value(), balance,
                 self.inp_cash_adv.value(), self.inp_diesel_adv.value(),
                 self.inp_cash_used.value(), self.inp_diesel_used.value(),
                 self.row["id"]))
        else:
            conn.execute(
                "INSERT INTO excavator_expenditure "
                "(date, details, hours_worked, rate_per_hour, total_amount, "
                " paid_cash, paid_diesel, balance_due, "
                " cash_advance, diesel_advance, cash_used, diesel_used) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (date_str, self.inp_details.text().strip(),
                 self.inp_hours.value(), self.inp_rate.value(), total,
                 self.inp_cash_adv.value(), self.inp_diesel_adv.value(), balance,
                 self.inp_cash_adv.value(), self.inp_diesel_adv.value(),
                 self.inp_cash_used.value(), self.inp_diesel_used.value()))
        conn.commit(); conn.close()
        self.accept()