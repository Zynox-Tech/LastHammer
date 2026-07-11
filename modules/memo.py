from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QDateEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
import database, config
from ui.base_module import BaseModule


class MemoModule(BaseModule):
    CHAPTER_TITLE = "Chapter 6 — Memory / Personal Notes"
    CHAPTER_COLOR = "#1E8449"
    COLUMNS = ["Description", "Person", "Amount (PKR)", "Type", "Date"]

    def get_all_rows(self):    return database.ch6_get_all()
    def get_grand_total(self): return database.ch6_grand_total()

    def row_to_cells(self, row):
        return [
            row["description"],
            row["person_name"] or "—",
            f"PKR {row['amount']:,.2f}",
            row["transaction_type"],
            row["date"],
        ]

    def open_add_dialog(self, date_str):
        dlg = MemoDialog(date_str, parent=self)
        if dlg.exec_() == QDialog.Accepted: self.refresh_table()

    def open_edit_dialog(self, row_id):
        row = database.ch6_get_by_id(row_id)
        if row:
            dlg = MemoDialog(row["date"], row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted: self.refresh_table()

    def do_delete(self, row_id): database.ch6_delete(row_id)


class MemoDialog(QDialog):
    def __init__(self, date_str, row=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit Note" if row else "Add Note")
        self.setFixedWidth(480); self.setModal(True)
        self._build_ui(date_str)
        if row: self._populate(row)

    def _build_ui(self, date_str):
        layout = QVBoxLayout(self)
        layout.setSpacing(20); layout.setContentsMargins(28, 28, 28, 28)

        lbl = QLabel(f"Chapter 6 — Memory Notes\n"
                     f"{'Edit' if self.row else 'Add New Note'}")
        lbl.setStyleSheet(f"font-size:16px; font-weight:bold; color:{config.DARK};")
        layout.addWidget(lbl)

        form = QFormLayout(); form.setSpacing(14); form.setLabelAlignment(Qt.AlignRight)

        def L(t):
            l = QLabel(t); l.setStyleSheet("font-size:14px; font-weight:bold;"); return l

        self.inp_date = QDateEdit()
        d = QDate.fromString(date_str, "yyyy-MM-dd")
        self.inp_date.setDate(d if d.isValid() else QDate.currentDate())
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setMinimumHeight(42)
        self.inp_date.setStyleSheet("font-size:14px; padding:6px 10px;")
        form.addRow(L("Date:"), self.inp_date)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("What is this note about?")
        self.inp_desc.setMinimumHeight(42)
        self.inp_desc.setStyleSheet("font-size:14px; padding:6px 10px;")
        form.addRow(L("Description:"), self.inp_desc)

        self.inp_person = QLineEdit()
        self.inp_person.setPlaceholderText("Person name (optional)")
        self.inp_person.setMinimumHeight(42)
        self.inp_person.setStyleSheet("font-size:14px; padding:6px 10px;")
        form.addRow(L("Person:"), self.inp_person)

        self.inp_amount = QDoubleSpinBox()
        self.inp_amount.setRange(0, 99_999_999); self.inp_amount.setDecimals(2)
        self.inp_amount.setPrefix("PKR "); self.inp_amount.setMinimumHeight(42)
        self.inp_amount.setStyleSheet("font-size:14px; padding:6px 10px;")
        form.addRow(L("Amount:"), self.inp_amount)

        self.inp_type = QComboBox()
        self.inp_type.addItems(["Given", "Taken", "Note"])
        self.inp_type.setMinimumHeight(42)
        self.inp_type.setStyleSheet("font-size:14px; padding:6px 10px;")
        form.addRow(L("Type:"), self.inp_type)

        layout.addLayout(form); layout.addSpacing(10)

        btn_row = QHBoxLayout(); btn_row.setSpacing(14)
        btn_c = QPushButton("Cancel"); btn_c.setMinimumHeight(46); btn_c.setMinimumWidth(120)
        btn_c.setStyleSheet("QPushButton{background:#555;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#888;}")
        btn_c.clicked.connect(self.reject)
        btn_s = QPushButton("Save"); btn_s.setMinimumHeight(46); btn_s.setMinimumWidth(160)
        btn_s.setStyleSheet("QPushButton{background:#1E8449;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#27AE60;}")
        btn_s.clicked.connect(self._save)
        btn_row.addWidget(btn_c); btn_row.addStretch(); btn_row.addWidget(btn_s)
        layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"], "yyyy-MM-dd")
        if d.isValid(): self.inp_date.setDate(d)
        self.inp_desc.setText(row["description"])
        self.inp_person.setText(row["person_name"] or "")
        self.inp_amount.setValue(float(row["amount"]))
        idx = self.inp_type.findText(row["transaction_type"])
        if idx >= 0: self.inp_type.setCurrentIndex(idx)

    def _save(self):
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Missing", "Please enter a description."); return
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        args = (desc, self.inp_person.text().strip(),
                self.inp_amount.value(), self.inp_type.currentText())
        if self.row: database.ch6_edit(self.row["id"], *args)
        else:        database.ch6_add(date_str, *args)
        self.accept()