"""CH 11 — Quick Entry: Log today's data across all modules in one screen"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QDoubleSpinBox, QTextEdit, QGridLayout,
    QApplication, QTabWidget
)
from PyQt5.QtCore import Qt, QDate
import database, config

DARK  = config.DARK
GOLD  = "#F39C12"

def _fld(placeholder="", height=40):
    w = QLineEdit(); w.setPlaceholderText(placeholder); w.setMinimumHeight(height)
    w.setStyleSheet("border:1px solid #DDDDDD;border-radius:6px;padding:4px 10px;font-size:13px;")
    return w

def _spin(max_val=9999999, decimals=0, suffix=""):
    w = QDoubleSpinBox(); w.setRange(0, max_val); w.setDecimals(decimals)
    w.setMinimumHeight(40)
    if suffix: w.setSuffix(f" {suffix}")
    w.setStyleSheet("border:1px solid #DDDDDD;border-radius:6px;padding:4px;font-size:13px;")
    return w

def _lbl(t, bold=False, color=DARK):
    l = QLabel(t)
    l.setStyleSheet(f"font-size:{'13' if bold else '12'}px;"
                    f"{'font-weight:bold;' if bold else ''}"
                    f"color:{color};border:none;")
    return l

def _section(title, color):
    f = QFrame()
    f.setStyleSheet(f"background:{color}20;border-radius:8px;"
                    f"border-left:4px solid {color};border-top:none;border-right:none;border-bottom:none;")
    lay = QVBoxLayout(f); lay.setContentsMargins(14,10,14,10); lay.setSpacing(8)
    t = QLabel(title); t.setStyleSheet(f"font-size:13px;font-weight:bold;color:{color};border:none;")
    lay.addWidget(t)
    return f, lay

def _save_btn(t, color):
    b = QPushButton(t); b.setMinimumHeight(44)
    b.setStyleSheet(f"QPushButton{{background:{color};color:white;border-radius:8px;"
                    f"border:none;font-size:14px;font-weight:bold;}}"
                    f"QPushButton:hover{{opacity:0.85;}}")
    return b


class QuickEntryModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 11 — Quick Entry")
        self.setMinimumSize(1280, 820)
        self._build_ui()

    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._date_bar())
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane{border:none;background:#EFEFEF;}
            QTabBar::tab{background:#DDDDDD;padding:10px 20px;font-size:13px;font-weight:bold;border:none;margin-right:2px;}
            QTabBar::tab:selected{background:#1A1A2E;color:white;}
        """)
        tabs.addTab(self._tab_general(),    "CH1 General")
        tabs.addTab(self._tab_excavator(),  "CH3 Excavator")
        tabs.addTab(self._tab_dumprei(),    "CH4 Dumprei")
        tabs.addTab(self._tab_production(), "Production")
        tabs.addTab(self._tab_advance(),    "Advance")
        root.addWidget(tabs, 1)

    def _topbar(self):
        f = QFrame(); f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {GOLD};"); f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28,0,28,0)
        bar = QFrame(); bar.setFixedSize(6,40); bar.setStyleSheet(f"background:{GOLD};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(12)
        vb = QVBoxLayout(); vb.setSpacing(1)
        vb.addWidget(QLabel("Chapter 11 — Quick Entry", styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel("Log today's expenses across all chapters from one single screen", styleSheet="color:#AAAAAA;font-size:12px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Dashboard"); btn.setFixedHeight(40); btn.setMinimumWidth(160)
        btn.setStyleSheet("QPushButton{background:#2C2C4E;color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}QPushButton:hover{background:#3D3D6E;}")
        btn.clicked.connect(self._back); lay.addWidget(btn)
        return f

    def _date_bar(self):
        f = QFrame(); f.setStyleSheet("background:#E8E8E8;border-bottom:1px solid #CCCCCC;"); f.setFixedHeight(54)
        lay = QHBoxLayout(f); lay.setContentsMargins(28,0,28,0)
        lay.addWidget(_lbl("📅  Entry Date for all tabs:", bold=True))
        lay.addSpacing(12)
        self.global_date = QDateEdit(QDate.currentDate())
        self.global_date.setCalendarPopup(True); self.global_date.setDisplayFormat("dd/MM/yyyy")
        self.global_date.setFixedHeight(40); self.global_date.setFixedWidth(200)
        self.global_date.setStyleSheet("font-size:14px;font-weight:bold;border:2px solid #CCCCCC;border-radius:7px;padding:4px 10px;")
        lay.addWidget(self.global_date); lay.addStretch()
        info = _lbl("All entries below will use this date", color="#888888")
        lay.addWidget(info)
        return f

    # ── Tab: General ──────────────────────────────────────────
    def _tab_general(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(30,20,30,20); lay.setSpacing(16)
        sec, sl = _section("General Expenditure Entry", config.RED)
        grid = QGridLayout(); grid.setSpacing(10)
        self.g_desc    = _fld("Description / what was purchased")
        self.g_amount  = _spin(99999999, 0, "PKR")
        self.g_paid_to = _fld("Paid to (person name)")
        for i,(lbl,w2) in enumerate([("Description:",self.g_desc),("Amount (PKR):",self.g_amount),("Paid To:",self.g_paid_to)]):
            grid.addWidget(_lbl(lbl,bold=True), i, 0)
            grid.addWidget(w2, i, 1)
        sl.addLayout(grid)
        btn = _save_btn("✓  Save General Entry", config.RED)
        btn.clicked.connect(self._save_general)
        sl.addWidget(btn)
        lay.addWidget(sec); lay.addStretch()
        return w

    def _save_general(self):
        if not self.g_desc.text().strip(): QMessageBox.warning(self,"Required","Enter description."); return
        if self.g_amount.value() <= 0: QMessageBox.warning(self,"Required","Enter amount."); return
        date = self.global_date.date().toString("yyyy-MM-dd")
        try:
            database.ch1_add(date, self.g_desc.text().strip(),
                             self.g_paid_to.text().strip(), self.g_amount.value())
            self._ok("General entry saved!")
            self.g_desc.clear(); self.g_amount.setValue(0); self.g_paid_to.clear()
        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

    # ── Tab: Excavator ────────────────────────────────────────
    def _tab_excavator(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(30,20,30,20); lay.setSpacing(16)
        sec, sl = _section("Excavator Work Session", "#0E6655")
        grid = QGridLayout(); grid.setSpacing(10)
        self.ex_details = _fld("Details / notes")
        self.ex_hours   = _spin(24, 1, "hrs")
        self.ex_rate    = _spin(99999, 0, "PKR/hr")
        self.ex_cash_adv= _spin(99999999, 0, "PKR")
        self.ex_diesel  = _spin(99999999, 0, "PKR")
        for i,(lbl,w2) in enumerate([("Details:",self.ex_details),("Hours Worked:",self.ex_hours),
                                      ("Rate/Hour:",self.ex_rate),("Cash Advance:",self.ex_cash_adv),
                                      ("Diesel Advance:",self.ex_diesel)]):
            grid.addWidget(_lbl(lbl,bold=True), i, 0)
            grid.addWidget(w2, i, 1)
        sl.addLayout(grid)
        btn = _save_btn("✓  Save Excavator Entry", "#0E6655")
        btn.clicked.connect(self._save_excavator)
        sl.addWidget(btn)
        lay.addWidget(sec); lay.addStretch()
        return w

    def _save_excavator(self):
        if self.ex_hours.value() <= 0: QMessageBox.warning(self,"Required","Enter hours."); return
        date = self.global_date.date().toString("yyyy-MM-dd")
        hrs  = self.ex_hours.value(); rate = self.ex_rate.value()
        total= hrs * rate
        try:
            database.ex_add_v2(date, self.ex_details.text().strip(), hrs, rate, total,
                               self.ex_cash_adv.value(), self.ex_diesel.value())
            self._ok(f"Excavator entry saved! Work total: PKR {total:,.0f}")
            self.ex_details.clear(); self.ex_hours.setValue(0); self.ex_rate.setValue(0)
            self.ex_cash_adv.setValue(0); self.ex_diesel.setValue(0)
        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

    # ── Tab: Dumprei ──────────────────────────────────────────
    def _tab_dumprei(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(30,20,30,20); lay.setSpacing(16)
        sec, sl = _section("Dumprei / Tipper Entry", config.ORANGE)
        grid = QGridLayout(); grid.setSpacing(10)
        self.dp_reg    = _fld("Registration number e.g. JU-1234")
        self.dp_owner  = _fld("Owner name")
        self.dp_trips  = _spin(9999, 0, "trips")
        self.dp_cash   = _spin(99999999, 0, "PKR")
        self.dp_diesel = _spin(99999999, 0, "PKR")
        for i,(lbl,w2) in enumerate([("Reg Number:",self.dp_reg),("Owner Name:",self.dp_owner),
                                      ("Total Trips:",self.dp_trips),("Cash Paid:",self.dp_cash),
                                      ("Diesel Paid:",self.dp_diesel)]):
            grid.addWidget(_lbl(lbl,bold=True), i, 0)
            grid.addWidget(w2, i, 1)
        sl.addLayout(grid)
        btn = _save_btn("✓  Save Dumprei Entry", config.ORANGE)
        btn.clicked.connect(self._save_dumprei)
        sl.addWidget(btn)
        lay.addWidget(sec); lay.addStretch()
        return w

    def _save_dumprei(self):
        if not self.dp_reg.text().strip(): QMessageBox.warning(self,"Required","Enter reg number."); return
        if self.dp_trips.value() <= 0: QMessageBox.warning(self,"Required","Enter trips."); return
        date  = self.global_date.date().toString("yyyy-MM-dd")
        cash  = self.dp_cash.value(); diesel = self.dp_diesel.value()
        total = cash + diesel
        try:
            database.ch4_add_v2(date, self.dp_reg.text().strip().upper(),
                                 self.dp_owner.text().strip(),
                                 int(self.dp_trips.value()), 0,0, cash, diesel, total, 0)
            self._ok("Dumprei entry saved!")
            self.dp_reg.clear(); self.dp_owner.clear()
            self.dp_trips.setValue(0); self.dp_cash.setValue(0); self.dp_diesel.setValue(0)
        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

    # ── Tab: Production ───────────────────────────────────────
    def _tab_production(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(30,20,30,20); lay.setSpacing(16)
        sec, sl = _section("Production Log", "#8E44AD")
        grid = QGridLayout(); grid.setSpacing(10)
        self.pr_shift    = QComboBox(); self.pr_shift.addItems(["Day","Night","Full Day"]); self.pr_shift.setMinimumHeight(40)
        self.pr_machine  = _fld("Machine / Excavator name")
        self.pr_operator = _fld("Operator name")
        self.pr_hours    = _spin(24, 1, "hrs")
        self.pr_tons     = _spin(99999, 1, "tons")
        self.pr_note     = _fld("Notes")
        for i,(lbl,w2) in enumerate([("Shift:",self.pr_shift),("Machine:",self.pr_machine),
                                      ("Operator:",self.pr_operator),("Hours Run:",self.pr_hours),
                                      ("Tons Extracted:",self.pr_tons),("Notes:",self.pr_note)]):
            grid.addWidget(_lbl(lbl,bold=True), i, 0)
            grid.addWidget(w2, i, 1)
        sl.addLayout(grid)
        btn = _save_btn("✓  Save Production Entry", "#8E44AD")
        btn.clicked.connect(self._save_production)
        sl.addWidget(btn)
        lay.addWidget(sec); lay.addStretch()
        return w

    def _save_production(self):
        if self.pr_tons.value() <= 0: QMessageBox.warning(self,"Required","Enter tons."); return
        date = self.global_date.date().toString("yyyy-MM-dd")
        try:
            database.prod_add(date, self.pr_shift.currentText(), self.pr_tons.value(),
                              self.pr_machine.text().strip(), self.pr_operator.text().strip(),
                              self.pr_hours.value(), self.pr_note.text().strip())
            self._ok(f"Production logged: {self.pr_tons.value():.1f} tons")
            self.pr_tons.setValue(0); self.pr_hours.setValue(0)
            self.pr_machine.clear(); self.pr_operator.clear(); self.pr_note.clear()
        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

    # ── Tab: Advance ──────────────────────────────────────────
    def _tab_advance(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(30,20,30,20); lay.setSpacing(16)
        sec, sl = _section("Advance / Loan Given", "#E67E22")
        grid = QGridLayout(); grid.setSpacing(10)
        self.ad_person   = _fld("Person name")
        self.ad_category = QComboBox(); self.ad_category.addItems(["Driver","Worker","Contractor","Fuel","Other"]); self.ad_category.setMinimumHeight(40)
        self.ad_amount   = _spin(99999999, 0, "PKR")
        self.ad_note     = _fld("Reason for advance")
        for i,(lbl,w2) in enumerate([("Person:",self.ad_person),("Category:",self.ad_category),
                                      ("Amount:",self.ad_amount),("Reason:",self.ad_note)]):
            grid.addWidget(_lbl(lbl,bold=True), i, 0)
            grid.addWidget(w2, i, 1)
        sl.addLayout(grid)
        btn = _save_btn("✓  Record Advance Given", "#E67E22")
        btn.clicked.connect(self._save_advance)
        sl.addWidget(btn)
        lay.addWidget(sec); lay.addStretch()
        return w

    def _save_advance(self):
        if not self.ad_person.text().strip(): QMessageBox.warning(self,"Required","Enter person name."); return
        if self.ad_amount.value() <= 0: QMessageBox.warning(self,"Required","Enter amount."); return
        date = self.global_date.date().toString("yyyy-MM-dd")
        try:
            database.adv_add(date, self.ad_person.text().strip(),
                             self.ad_category.currentText(),
                             self.ad_amount.value(), self.ad_note.text().strip())
            self._ok("Advance recorded!")
            self.ad_person.clear(); self.ad_amount.setValue(0); self.ad_note.clear()
        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

    def _ok(self, msg):
        bar = QMessageBox(self)
        bar.setWindowTitle("Saved"); bar.setText(f"✅  {msg}")
        bar.setStyleSheet("font-size:14px;")
        bar.exec_()

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()
    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)