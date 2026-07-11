from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QPushButton,
    QDateEdit, QMessageBox, QCompleter, QFrame, QWidget
)
from PyQt5.QtCore import Qt, QDate
import database, config
from ui.base_module import BaseModule


class RoyaltyModule(BaseModule):
    CHAPTER_TITLE = "Chapter 2 — Royalty to Government"
    CHAPTER_COLOR = "#6C3483"
    COLUMNS = ["Vehicle Number", "Weight (kg)", "Payment (PKR)", "Date"]

    def get_all_rows(self):
        return database.ch2_get_all_v2()

    def row_to_cells(self, row):
        keys = row.keys()
        wt  = float(row["weight_tons"]) if "weight_tons" in keys and row["weight_tons"] else 0
        amt = float(row["amount"])      if "amount"      in keys and row["amount"]      else 0
        vehicle = ""
        if "vehicle_number" in keys and row["vehicle_number"]:
            vehicle = row["vehicle_number"]
        elif "details" in keys and row["details"]:
            vehicle = row["details"]
        return [
            vehicle or "—",
            f"{wt:,.0f} kg",
            f"PKR {amt:,.2f}" if amt else "—",
            row["date"],
        ]

    def get_grand_total(self):
        return database.ch2_grand_total_v2()

    def open_add_dialog(self, date_str):
        dlg = RoyaltyDialog(date_str, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_table()

    def open_edit_dialog(self, row_id):
        row = database.ch2_get_by_id(row_id)
        if row:
            dlg = RoyaltyDialog(row["date"], row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.refresh_table()

    def do_delete(self, row_id):
        database.ch2_delete(row_id)

    def refresh_table(self):
        rows         = self.get_all_rows()
        total_pay    = database.ch2_grand_total_v2()
        total_weight = database.ch2_total_weight()
        self._populate_table(rows)
        self.lbl_total.setText(f"PKR {total_pay:,.2f}")
        if hasattr(self, "lbl_weight"):
            self.lbl_weight.setText(f"{total_weight:,.0f} kg")
        self.lbl_footer_total.setText(
            f"Total Weight: {total_weight:,.0f} kg     |     "
            f"Total Payment: PKR {total_pay:,.2f}")
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()

    # Override toolbar to show weight + payment side by side
    def _make_toolbar(self):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color:white; border-bottom:2px solid #DDDDDD;")
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(20)

        def hint(t):
            l = QLabel(t)
            l.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#AAAAAA; letter-spacing:1px;")
            return l

        # Date picker
        date_col = QVBoxLayout(); date_col.setSpacing(3)
        date_col.addWidget(hint("DATE FOR NEW ENTRIES"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(46)
        self.date_edit.setFixedWidth(210)
        self.date_edit.setStyleSheet(
            "font-size:16px; font-weight:bold; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px; background:white;")
        date_col.addWidget(self.date_edit)
        layout.addLayout(date_col)

        div1 = QFrame(); div1.setFrameShape(QFrame.VLine)
        div1.setStyleSheet("color:#EEEEEE;"); layout.addWidget(div1)

        # Total weight
        wt_col = QVBoxLayout(); wt_col.setSpacing(3)
        wt_col.addWidget(hint("TOTAL WEIGHT (ALL ENTRIES)"))
        self.lbl_weight = QLabel("0 kg")
        self.lbl_weight.setStyleSheet(
            "color:#6C3483; font-size:24px; font-weight:bold;")
        wt_col.addWidget(self.lbl_weight)
        layout.addLayout(wt_col)

        div2 = QFrame(); div2.setFrameShape(QFrame.VLine)
        div2.setStyleSheet("color:#EEEEEE;"); layout.addWidget(div2)

        # Total payment
        pay_col = QVBoxLayout(); pay_col.setSpacing(3)
        pay_col.addWidget(hint("TOTAL PAYMENT (ALL ENTRIES)"))
        self.lbl_total = QLabel("PKR 0")
        self.lbl_total.setStyleSheet(
            "color:#C0392B; font-size:24px; font-weight:bold;")
        pay_col.addWidget(self.lbl_total)
        layout.addLayout(pay_col)

        layout.addStretch()

        btn_add = QPushButton("  ＋   ADD NEW ENTRY")
        btn_add.setFixedHeight(62)
        btn_add.setMinimumWidth(270)
        btn_add.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #9B59B6, stop:1 #6C3483);
                color:white; border-radius:12px; border:none;
                font-size:19px; font-weight:bold; letter-spacing:1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #AF7AC5, stop:1 #9B59B6);
            }
            QPushButton:pressed { background:#1A1A2E; }
        """)
        btn_add.clicked.connect(self._on_add)
        layout.addWidget(btn_add)
        return frame


class RoyaltyDialog(QDialog):
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

        lbl = QLabel(f"Chapter 2 — Royalty to Government\n"
                     f"{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{config.DARK};")
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        def L(t):
            l = QLabel(t)
            l.setStyleSheet("font-size:14px; font-weight:bold;")
            return l

        # Date
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

        # Vehicle number
        self.inp_vehicle = QLineEdit()
        self.inp_vehicle.setPlaceholderText("e.g. LEA-1234")
        self.inp_vehicle.setMinimumHeight(44)
        self.inp_vehicle.setStyleSheet(
            "font-size:15px; font-weight:bold; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        try:
            known = database.ch4_get_known_vehicles()
            comp = QCompleter(known)
            comp.setCaseSensitivity(Qt.CaseInsensitive)
            self.inp_vehicle.setCompleter(comp)
        except:
            pass
        form.addRow(L("Vehicle Number:"), self.inp_vehicle)

        # Weight
        self.inp_weight = QDoubleSpinBox()
        self.inp_weight.setRange(0, 99999999)
        self.inp_weight.setDecimals(0)
        self.inp_weight.setSuffix(" kg")
        self.inp_weight.setMinimumHeight(44)
        self.inp_weight.setStyleSheet(
            "font-size:14px; padding:6px 10px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        form.addRow(L("Weight (kg):"), self.inp_weight)

        # Payment (optional)
        self.inp_payment = QDoubleSpinBox()
        self.inp_payment.setRange(0, 99_999_999)
        self.inp_payment.setDecimals(2)
        self.inp_payment.setPrefix("PKR ")
        self.inp_payment.setMinimumHeight(44)
        self.inp_payment.setStyleSheet(
            "font-size:14px; padding:6px 10px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        lbl_pay = L("Payment (PKR):")
        hint = QLabel("Optional — leave 0 if no payment for this entry")
        hint.setStyleSheet("font-size:11px; color:#AAAAAA;")
        pay_box = QVBoxLayout(); pay_box.setSpacing(3)
        pay_box.addWidget(self.inp_payment)
        pay_box.addWidget(hint)
        pay_w = QWidget(); pay_w.setLayout(pay_box)
        form.addRow(lbl_pay, pay_w)

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
            "QPushButton{background:#6C3483;color:white;border-radius:8px;"
            "border:none;font-size:15px;font-weight:bold;}"
            "QPushButton:hover{background:#8E44AD;}")
        btn_s.clicked.connect(self._save)

        btn_row.addWidget(btn_c)
        btn_row.addStretch()
        btn_row.addWidget(btn_s)
        layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"], "yyyy-MM-dd")
        if d.isValid():
            self.inp_date.setDate(d)
        keys = row.keys()
        vehicle = ""
        if "vehicle_number" in keys and row["vehicle_number"]:
            vehicle = row["vehicle_number"]
        elif "details" in keys and row["details"]:
            vehicle = row["details"]
        self.inp_vehicle.setText(vehicle)
        self.inp_weight.setValue(float(row["weight_tons"]) if "weight_tons" in keys and row["weight_tons"] else 0)
        self.inp_payment.setValue(float(row["amount"]) if "amount" in keys and row["amount"] else 0)

    def _save(self):
        vehicle = self.inp_vehicle.text().strip().upper()
        if not vehicle:
            QMessageBox.warning(self, "Missing", "Please enter vehicle number.")
            return
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        if self.row:
            database.ch2_edit_v2(
                self.row["id"], date_str, vehicle,
                self.inp_weight.value(), self.inp_payment.value())
        else:
            database.ch2_add_v2(
                date_str, vehicle,
                self.inp_weight.value(), self.inp_payment.value())
        self.accept()