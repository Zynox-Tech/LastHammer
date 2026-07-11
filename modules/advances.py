"""CH 9 — Advance / Loan Register"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QDoubleSpinBox, QTextEdit, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
import database, config

COLOR = "#E67E22"
DARK  = config.DARK

class AdvancesModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 9 — Advance / Loan Register")
        self.setMinimumSize(1200, 750)
        self._build_ui()
        self._load()

    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._toolbar())
        root.addWidget(self._table_area(), 1)
        root.addWidget(self._footer())

    def _topbar(self):
        f = QFrame(); f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {COLOR};"); f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28,0,28,0)
        bar = QFrame(); bar.setFixedSize(6,40); bar.setStyleSheet(f"background:{COLOR};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(12)
        vb = QVBoxLayout(); vb.setSpacing(1)
        vb.addWidget(QLabel("Chapter 9 — Advance / Loan Register", styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel("Track cash given in advance to workers, drivers, contractors — with repayment", styleSheet="color:#AAAAAA;font-size:12px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Dashboard"); btn.setFixedHeight(40); btn.setMinimumWidth(160)
        btn.setStyleSheet("QPushButton{background:#2C2C4E;color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}QPushButton:hover{background:#3D3D6E;}")
        btn.clicked.connect(self._back); lay.addWidget(btn)
        return f

    def _toolbar(self):
        f = QFrame(); f.setStyleSheet("background:#F5F5F5;border-bottom:1px solid #DDDDDD;"); f.setFixedHeight(60)
        lay = QHBoxLayout(f); lay.setContentsMargins(24,0,24,0); lay.setSpacing(10)
        def btn(t, c, fn):
            b = QPushButton(t); b.setFixedHeight(40); b.setMinimumWidth(160)
            b.setStyleSheet(f"QPushButton{{background:{c};color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}}QPushButton:hover{{opacity:0.85;}}")
            b.clicked.connect(fn); return b
        lay.addWidget(btn("＋  New Advance", COLOR, self._add))
        lay.addWidget(btn("✓  Record Repayment", "#1E8449", self._repay))
        lay.addWidget(btn("✕  Delete", "#C0392B", self._delete))
        lay.addStretch()
        self.lbl_filter = QComboBox(); self.lbl_filter.setFixedHeight(38)
        self.lbl_filter.addItems(["All Records","Pending Only","Cleared Only"])
        self.lbl_filter.setStyleSheet("font-size:13px;padding:4px 10px;border:1px solid #DDDDDD;border-radius:6px;")
        self.lbl_filter.currentIndexChanged.connect(self._load)
        lay.addWidget(self.lbl_filter)
        return f

    def _table_area(self):
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["#","Date","Person / Party","Category","Amount Given","Repaid","Still Owed","Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget{border:none;font-size:13px;}
            QHeaderView::section{background:#1A1A2E;color:white;font-weight:bold;padding:8px;border:none;}
            QTableWidget::item:selected{background:#F39C12;color:#1A1A2E;}
        """)
        scroll = QScrollArea(); scroll.setWidget(self.table); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        return scroll

    def _footer(self):
        f = QFrame(); f.setStyleSheet(f"background:{DARK};border-top:2px solid {COLOR};"); f.setFixedHeight(54)
        lay = QHBoxLayout(f); lay.setContentsMargins(24,0,24,0)
        self.lbl_total = QLabel("Total Outstanding: PKR 0")
        self.lbl_total.setStyleSheet(f"color:{COLOR};font-size:16px;font-weight:bold;border:none;")
        lay.addWidget(self.lbl_total); lay.addStretch()
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color:#AAAAAA;font-size:13px;border:none;")
        lay.addWidget(self.lbl_count)
        return f

    def _load(self):
        filt = self.lbl_filter.currentIndex()
        rows = database.adv_get_all()
        if filt == 1: rows = [r for r in rows if r["status"] == "Pending"]
        if filt == 2: rows = [r for r in rows if r["status"] == "Cleared"]
        self.table.setRowCount(len(rows))
        self._rows = rows
        total_owed = 0
        for i, r in enumerate(rows):
            owed = float(r["amount"]) - float(r["repaid"])
            total_owed += max(owed, 0) if r["status"] == "Pending" else 0
            pending = r["status"] == "Pending"
            vals = [str(i+1), r["date"], r["person_name"], r["category"],
                    f"PKR {float(r['amount']):,.0f}",
                    f"PKR {float(r['repaid']):,.0f}",
                    f"PKR {max(owed,0):,.0f}",
                    r["status"]]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if j == 7:
                    item.setForeground(QColor("#C0392B") if pending else QColor("#1E8449"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table.setItem(i, j, item)
        self.lbl_total.setText(f"Total Outstanding: PKR {total_owed:,.0f}")
        self.lbl_count.setText(f"{len(rows)} records")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None, None
        return self._rows[row]["id"], row

    def _add(self):
        dlg = AdvanceDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.adv_add(d["date"], d["person"], d["category"], d["amount"], d["note"])
            self._load()

    def _repay(self):
        adv_id, _ = self._selected_id()
        if not adv_id: QMessageBox.warning(self, "Select", "Select an advance first."); return
        row = next((r for r in self._rows if r["id"] == adv_id), None)
        if not row: return
        owed = float(row["amount"]) - float(row["repaid"])
        if owed <= 0: QMessageBox.information(self, "Cleared", "This advance is already cleared."); return
        dlg = RepayDialog(row, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            database.adv_repay(adv_id, dlg.amount())
            self._load()

    def _delete(self):
        adv_id, _ = self._selected_id()
        if not adv_id: QMessageBox.warning(self, "Select", "Select a record first."); return
        if QMessageBox.question(self,"Delete","Delete this advance record?",
            QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            database.adv_delete(adv_id); self._load()

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()
    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)


class AdvanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Advance / Loan")
        self.setFixedSize(440, 380)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,20,24,20); lay.setSpacing(14)
        lay.addWidget(QLabel("NEW ADVANCE", styleSheet=f"font-size:16px;font-weight:bold;color:{DARK};"))
        form = QFormLayout(); form.setSpacing(10)
        self.date = QDateEdit(QDate.currentDate()); self.date.setCalendarPopup(True); self.date.setDisplayFormat("dd/MM/yyyy"); self.date.setMinimumHeight(40)
        self.person = QLineEdit(); self.person.setPlaceholderText("e.g. Shoukat, Malik Chacha..."); self.person.setMinimumHeight(40)
        self.category = QComboBox(); self.category.addItems(["Driver","Worker","Contractor","Fuel","Other"]); self.category.setMinimumHeight(40)
        self.amount = QDoubleSpinBox(); self.amount.setRange(0,99999999); self.amount.setDecimals(0); self.amount.setSuffix(" PKR"); self.amount.setMinimumHeight(40)
        self.note = QTextEdit(); self.note.setFixedHeight(70); self.note.setPlaceholderText("Reason for advance...")
        for lbl,w in [("Date:",self.date),("Person / Party:",self.person),
                      ("Category:",self.category),("Amount:",self.amount),("Note:",self.note)]:
            form.addRow(QLabel(lbl, styleSheet="font-weight:bold;"), w)
        lay.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton("✓  Save Advance"); ok.setMinimumHeight(44)
        ok.setStyleSheet(f"background:{COLOR};color:white;border-radius:8px;border:none;font-size:14px;font-weight:bold;")
        ok.clicked.connect(self._save)
        ca = QPushButton("Cancel"); ca.setMinimumHeight(44)
        ca.setStyleSheet("background:#CCCCCC;color:#333;border-radius:8px;border:none;font-size:13px;")
        ca.clicked.connect(self.reject)
        btns.addWidget(ca); btns.addWidget(ok)
        lay.addLayout(btns)

    def _save(self):
        if not self.person.text().strip(): QMessageBox.warning(self,"Required","Enter person name."); return
        if self.amount.value() <= 0: QMessageBox.warning(self,"Required","Enter amount > 0."); return
        self.accept()

    def data(self):
        return {"date": self.date.date().toString("yyyy-MM-dd"),
                "person": self.person.text().strip(),
                "category": self.category.currentText(),
                "amount": self.amount.value(),
                "note": self.note.toPlainText().strip()}


class RepayDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Repayment")
        self.setFixedSize(380, 260)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,20,24,20); lay.setSpacing(12)
        owed = float(row["amount"]) - float(row["repaid"])
        lay.addWidget(QLabel(f"Repayment for: {row['person_name']}", styleSheet="font-size:15px;font-weight:bold;"))
        lay.addWidget(QLabel(f"Still owed: PKR {owed:,.0f}", styleSheet=f"font-size:13px;color:#C0392B;"))
        form = QFormLayout()
        self.amt = QDoubleSpinBox(); self.amt.setRange(0, owed); self.amt.setValue(owed)
        self.amt.setDecimals(0); self.amt.setSuffix(" PKR"); self.amt.setMinimumHeight(42)
        form.addRow(QLabel("Amount Repaid:", styleSheet="font-weight:bold;"), self.amt)
        lay.addLayout(form); lay.addStretch()
        btn = QPushButton("✓  Record Repayment"); btn.setMinimumHeight(46)
        btn.setStyleSheet("background:#1E8449;color:white;border-radius:8px;border:none;font-size:14px;font-weight:bold;")
        btn.clicked.connect(self.accept); lay.addWidget(btn)

    def amount(self): return self.amt.value()