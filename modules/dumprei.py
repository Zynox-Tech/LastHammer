from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox,
    QPushButton, QDateEdit, QMessageBox, QCompleter
)
from PyQt5.QtCore import Qt, QDate
import database, config
from ui.base_module import BaseModule


class DumpreiModule(BaseModule):
    CHAPTER_TITLE = "Chapter 4 — Dumprei Expenditure"
    CHAPTER_COLOR = config.ORANGE
    COLUMNS = ["Reg. No.", "Owner", "Trips",
               "Paid Cash", "Paid Diesel", "Total Paid", "Balance Due", "Date"]

    def get_all_rows(self):
        return database.ch4_get_all_v2()

    def row_to_cells(self, row):
        paid_cash    = (row["paid_cash"] if "paid_cash" in row.keys() else None) or 0
        paid_diesel  = (row["paid_diesel_worth"] if "paid_diesel_worth" in row.keys() else None) or 0
        total_paid   = (row["payment_received"] if "payment_received" in row.keys() else None) or (paid_cash + paid_diesel)
        balance      = (row["balance_due"] if "balance_due" in row.keys() else None) or 0
        trips        = (row["total_trips"] if "total_trips" in row.keys() else None) or 0
        return [
            row["reg_number"],
            row["owner_name"],
            str(trips) if trips else "—",
            f"PKR {paid_cash:,.0f}" if paid_cash else "—",
            f"PKR {paid_diesel:,.0f}" if paid_diesel else "—",
            f"PKR {total_paid:,.2f}",
            f"PKR {balance:,.2f}",
            row["date"],
        ]

    def get_grand_total(self):
        return database.ch4_grand_total()

    def open_add_dialog(self, date_str):
        dlg = DumpreiDialog(date_str, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_table()

    def open_edit_dialog(self, row_id):
        row = database.ch4_get_by_id(row_id)
        if row:
            dlg = DumpreiDialog(row["date"], row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.refresh_table()

    def do_delete(self, row_id):
        database.ch4_delete(row_id)


class DumpreiDialog(QDialog):
    def __init__(self, date_str, row=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit Entry" if row else "Add New Entry")
        self.setFixedWidth(520)
        self.setModal(True)
        self._build_ui(date_str)
        if row:
            self._populate(row)

    def _build_ui(self, date_str):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 24, 28, 24)

        lbl = QLabel(f"Chapter 4 — Dumprei Expenditure\n"
                     f"{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(f"font-size:16px; font-weight:bold; color:{config.DARK};")
        layout.addWidget(lbl)

        info = QLabel(
            "💡  Give cash and/or diesel in advance. Record trips completed.\n"
            "     Leave any field blank / zero if not applicable.")
        info.setStyleSheet(
            "background:#FEF9E7; color:#7D6608; border-radius:8px; "
            "padding:10px 14px; font-size:12px; border:1px solid #F9E79F;")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        def L(t):
            l = QLabel(t)
            l.setStyleSheet("font-size:13px; font-weight:bold;")
            return l

        def inp(ph=""):
            f = QLineEdit()
            f.setPlaceholderText(ph)
            f.setMinimumHeight(42)
            f.setStyleSheet(
                "font-size:13px; padding:6px 12px; "
                "border:2px solid #DDDDDD; border-radius:8px;")
            return f

        def spin(prefix="PKR ", max_val=9999999, decimals=2):
            s = QDoubleSpinBox()
            s.setRange(0, max_val)
            s.setDecimals(decimals)
            if prefix: s.setPrefix(prefix)
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

        self.inp_reg = inp("e.g. LEA-2341")
        self.inp_reg.setStyleSheet(
            "font-size:14px; font-weight:bold; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        try:
            known = database.ch4_get_known_vehicles()
            comp = QCompleter(known)
            comp.setCaseSensitivity(Qt.CaseInsensitive)
            self.inp_reg.setCompleter(comp)
        except:
            pass
        form.addRow(L("Reg. Number:"), self.inp_reg)

        self.inp_owner = inp("Owner / driver name")
        form.addRow(L("Owner Name:"), self.inp_owner)

        self.inp_trips = QSpinBox()
        self.inp_trips.setRange(0, 9999)
        self.inp_trips.setSuffix(" trips")
        self.inp_trips.setMinimumHeight(42)
        self.inp_trips.setStyleSheet(
            "font-size:13px; padding:4px 8px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        form.addRow(L("Trips Made:"), self.inp_trips)

        sep = QLabel("── PAYMENT ─────────────────────────────")
        sep.setStyleSheet("color:#AAAAAA; font-size:11px;")
        form.addRow("", sep)

        self.inp_cash = spin()
        form.addRow(L("Paid in Cash:"), self.inp_cash)

        self.inp_diesel = spin()
        form.addRow(L("Paid in Diesel\n(PKR value):"), self.inp_diesel)

        sep2 = QLabel("────────────────────────────────────────")
        sep2.setStyleSheet("color:#AAAAAA; font-size:11px;")
        form.addRow("", sep2)

        self.inp_balance = spin()
        lbl_b = L("Balance Due:")
        lbl_b.setStyleSheet("font-size:13px; font-weight:bold; color:#C0392B;")
        form.addRow(lbl_b, self.inp_balance)

        self.inp_details = inp("Optional notes")
        form.addRow(L("Notes:"), self.inp_details)

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
            f"QPushButton{{background:{config.ORANGE};color:white;border-radius:8px;"
            f"border:none;font-size:15px;font-weight:bold;}}"
            f"QPushButton:hover{{background:#E59866;}}")
        btn_s.clicked.connect(self._save)
        btn_row.addWidget(btn_c)
        btn_row.addStretch()
        btn_row.addWidget(btn_s)
        layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"], "yyyy-MM-dd")
        if d.isValid():
            self.inp_date.setDate(d)
        self.inp_reg.setText(row["reg_number"])
        self.inp_owner.setText(row["owner_name"])
        self.inp_trips.setValue(int((row["total_trips"] if "total_trips" in row.keys() else None) or 0))
        self.inp_cash.setValue(float((row["paid_cash"] if "paid_cash" in row.keys() else None) or 0))
        self.inp_diesel.setValue(float((row["paid_diesel_worth"] if "paid_diesel_worth" in row.keys() else None) or 0))
        self.inp_balance.setValue(float((row["balance_due"] if "balance_due" in row.keys() else None) or 0))
        self.inp_details.setText((row["details"] if "details" in row.keys() else None) or "")

    def _save(self):
        reg = self.inp_reg.text().strip().upper()
        owner = self.inp_owner.text().strip()
        if not reg:
            QMessageBox.warning(self, "Missing", "Please enter registration number.")
            return
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        conn = database.get_connection()
        total = self.inp_cash.value() + self.inp_diesel.value()
        if self.row:
            conn.execute(
                "UPDATE dumprei_expenditure SET date=?, reg_number=?, owner_name=?, "
                "total_trips=?, payment_received=?, balance_due=?, details=?, "
                "paid_cash=?, paid_diesel_worth=? WHERE id=?",
                (date_str, reg, owner,
                 self.inp_trips.value(), total,
                 self.inp_balance.value(), self.inp_details.text().strip(),
                 self.inp_cash.value(), self.inp_diesel.value(),
                 self.row["id"]))
        else:
            conn.execute(
                "INSERT INTO dumprei_expenditure "
                "(date, reg_number, owner_name, total_trips, payment_received, "
                " balance_due, details, paid_cash, paid_diesel_worth) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (date_str, reg, owner,
                 self.inp_trips.value(), total,
                 self.inp_balance.value(), self.inp_details.text().strip(),
                 self.inp_cash.value(), self.inp_diesel.value()))
        conn.commit(); conn.close()
        self.accept()