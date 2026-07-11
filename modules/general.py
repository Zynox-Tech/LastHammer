from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDateEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
import database, config
from ui.base_module import BaseModule


class GeneralModule(BaseModule):
    CHAPTER_TITLE = "Chapter 1 — General Expenditures"
    CHAPTER_COLOR = config.RED
    COLUMNS = ["Details / Description", "Amount (PKR)", "Date"]

    def get_all_rows(self):
        return database.ch1_get_all()

    def row_to_cells(self, row):
        amt = row["amount"]
        return [row["details"], f"PKR {amt:,.2f}" if amt else "—", row["date"]]

    def get_grand_total(self):
        return database.ch1_grand_total()

    def open_add_dialog(self, date_str):
        dlg = GeneralDialog(date_str, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_table()

    def open_edit_dialog(self, row_id):
        row = database.ch1_get_by_id(row_id)
        if row:
            dlg = GeneralDialog(row["date"], row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.refresh_table()

    def do_delete(self, row_id):
        database.ch1_delete(row_id)


class GeneralDialog(QDialog):
    def __init__(self, date_str, row=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit Entry" if row else "Add New Entry")
        self.setFixedWidth(480)
        self.setModal(True)
        self._build_ui(date_str)
        if row:
            self._populate(row)

    def _build_ui(self, date_str):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 28, 28, 28)

        lbl = QLabel(f"Chapter 1 — General Expenditures\n"
                     f"{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(f"font-size:16px; font-weight:bold; color:{config.DARK};")
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        def L(t):
            l = QLabel(t)
            l.setStyleSheet("font-size:14px; font-weight:bold;")
            return l

        def inp(ph=""):
            f = QLineEdit()
            f.setPlaceholderText(ph)
            f.setMinimumHeight(44)
            f.setStyleSheet(
                "font-size:14px; padding:6px 12px; "
                "border:2px solid #DDDDDD; border-radius:8px; background:white;")
            return f

        self.inp_date = QDateEdit()
        d = QDate.fromString(date_str, "yyyy-MM-dd")
        self.inp_date.setDate(d if d.isValid() else QDate.currentDate())
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setMinimumHeight(44)
        self.inp_date.setStyleSheet(
            "font-size:15px; font-weight:bold; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        form.addRow(L("Date:"), self.inp_date)

        self.inp_details = inp("e.g. Labour wages, tools purchased, maintenance")
        form.addRow(L("Details:"), self.inp_details)

        self.inp_amount = inp("e.g. 5000   (optional — leave blank if none)")
        lbl_amt = QLabel("Amount:")
        lbl_amt.setStyleSheet("font-size:14px; font-weight:bold;")
        hint_amt = QLabel("Numbers only, no PKR. Optional.")
        hint_amt.setStyleSheet("font-size:11px; color:#AAAAAA;")
        amt_box = QVBoxLayout()
        amt_box.setSpacing(3)
        amt_box.addWidget(self.inp_amount)
        amt_box.addWidget(hint_amt)
        from PyQt5.QtWidgets import QWidget
        amt_w = QWidget()
        amt_w.setLayout(amt_box)
        form.addRow(lbl_amt, amt_w)

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
            f"QPushButton{{background:{config.RED};color:white;border-radius:8px;"
            f"border:none;font-size:15px;font-weight:bold;}}"
            f"QPushButton:hover{{background:#E74C3C;}}")
        btn_s.clicked.connect(self._save)
        btn_row.addWidget(btn_c)
        btn_row.addStretch()
        btn_row.addWidget(btn_s)
        layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"], "yyyy-MM-dd")
        if d.isValid():
            self.inp_date.setDate(d)
        self.inp_details.setText(row["details"] or "")
        amt = row["amount"]
        if amt:
            try:
                self.inp_amount.setText(str(int(amt)) if float(amt) == int(float(amt)) else str(amt))
            except:
                self.inp_amount.setText(str(amt))

    def _save(self):
        details = self.inp_details.text().strip()
        if not details:
            QMessageBox.warning(self, "Missing", "Please enter details.")
            return
        amt_text = self.inp_amount.text().strip().replace(",", "").replace("PKR", "").strip()
        try:
            amount = float(amt_text) if amt_text else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount",
                "Amount must be a plain number.\nExample: 5000\nLeave blank if no amount.")
            return
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        conn = database.get_connection()
        if self.row:
            conn.execute(
                "UPDATE general_expenditures SET date=?, details=?, amount=? WHERE id=?",
                (date_str, details, amount, self.row["id"]))
        else:
            conn.execute(
                "INSERT INTO general_expenditures (date, details, amount) VALUES (?,?,?)",
                (date_str, details, amount))
        conn.commit(); conn.close()
        self.accept()