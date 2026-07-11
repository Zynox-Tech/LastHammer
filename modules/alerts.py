"""CH 12 — Alerts & Reminders"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QTextEdit, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from datetime import date as dt_date
import database, config

COLOR = "#E74C3C"
DARK  = config.DARK


class AlertsModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 12 — Alerts & Reminders")
        self.setMinimumSize(1200, 750)
        self._build_ui(); self._load()

    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._auto_alerts_bar())
        root.addWidget(self._toolbar())
        root.addWidget(self._table_area(), 1)
        root.addWidget(self._footer())

    def _topbar(self):
        f = QFrame(); f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {COLOR};"); f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28,0,28,0)
        bar = QFrame(); bar.setFixedSize(6,40); bar.setStyleSheet(f"background:{COLOR};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(12)
        vb = QVBoxLayout(); vb.setSpacing(1)
        vb.addWidget(QLabel("Chapter 12 — Alerts & Reminders", styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel("Set payment reminders, due dates, royalty alerts — never miss a deadline", styleSheet="color:#AAAAAA;font-size:12px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Dashboard"); btn.setFixedHeight(40); btn.setMinimumWidth(160)
        btn.setStyleSheet("QPushButton{background:#2C2C4E;color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}QPushButton:hover{background:#3D3D6E;}")
        btn.clicked.connect(self._back); lay.addWidget(btn)
        return f

    def _auto_alerts_bar(self):
        """Shows auto-generated alerts from system data."""
        self.auto_bar = QFrame()
        self.auto_bar.setStyleSheet("background:#FFF3CD;border-bottom:2px solid #F39C12;")
        lay = QHBoxLayout(self.auto_bar); lay.setContentsMargins(20,8,20,8); lay.setSpacing(16)
        self._auto_labels = []
        self._refresh_auto_alerts(lay)
        return self.auto_bar

    def _refresh_auto_alerts(self, lay=None):
        if lay is None:
            # clear and rebuild
            for i in reversed(range(self.auto_bar.layout().count())):
                item = self.auto_bar.layout().takeAt(i)
                if item.widget(): item.widget().deleteLater()
            lay = self.auto_bar.layout()
        alerts = self._compute_auto_alerts()
        if not alerts:
            lbl = QLabel("✅  No automatic alerts — all clear")
            lbl.setStyleSheet("font-size:13px;color:#1E8449;font-weight:bold;border:none;")
            lay.addWidget(lbl)
        else:
            ico = QLabel("⚠"); ico.setStyleSheet(f"font-size:18px;color:{COLOR};border:none;")
            lay.addWidget(ico)
            for a in alerts[:4]:
                lbl = QLabel(a)
                lbl.setStyleSheet(f"font-size:12px;font-weight:bold;color:{COLOR};border:none;")
                lay.addWidget(lbl)
                sep = QFrame(); sep.setFrameShape(QFrame.VLine); sep.setStyleSheet("color:#CCCCCC;")
                lay.addWidget(sep)
        lay.addStretch()

    def _compute_auto_alerts(self):
        alerts = []
        try:
            # Outstanding advances
            owed = database.adv_total_outstanding()
            if owed > 0: alerts.append(f"Advances Outstanding: PKR {owed:,.0f}")
        except: pass
        try:
            # Excavator balance
            conn = database.get_connection()
            work  = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM excavator_expenditure").fetchone()[0] or 0
            adv   = conn.execute("SELECT COALESCE(SUM(cash_advance+diesel_advance),0) FROM excavator_expenditure").fetchone()[0] or 0
            conn.close()
            bal = work - adv
            if bal > 0: alerts.append(f"Excavator Balance Due: PKR {bal:,.0f}")
        except: pass
        try:
            # Dumprei unpaid balances
            conn = database.get_connection()
            bal = conn.execute("SELECT COALESCE(SUM(balance_due),0) FROM dumprei_expenditure WHERE balance_due>0").fetchone()[0] or 0
            conn.close()
            if bal > 0: alerts.append(f"Dumprei Balance Due: PKR {bal:,.0f}")
        except: pass
        return alerts

    def _toolbar(self):
        f = QFrame(); f.setStyleSheet("background:#F5F5F5;border-bottom:1px solid #DDDDDD;"); f.setFixedHeight(60)
        lay = QHBoxLayout(f); lay.setContentsMargins(24,0,24,0); lay.setSpacing(10)
        def btn(t, c, fn):
            b = QPushButton(t); b.setFixedHeight(40); b.setMinimumWidth(150)
            b.setStyleSheet(f"QPushButton{{background:{c};color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}}QPushButton:hover{{opacity:0.85;}}")
            b.clicked.connect(fn); return b
        lay.addWidget(btn("＋  New Reminder", COLOR, self._add))
        lay.addWidget(btn("✓  Mark Done", "#1E8449", self._dismiss))
        lay.addWidget(btn("✕  Delete", "#555555", self._delete))
        lay.addStretch()
        self.cmb_filter = QComboBox(); self.cmb_filter.setFixedHeight(38)
        self.cmb_filter.addItems(["Active Only","All Alerts"])
        self.cmb_filter.setStyleSheet("font-size:13px;padding:4px 10px;border:1px solid #DDDDDD;border-radius:6px;")
        self.cmb_filter.currentIndexChanged.connect(self._load)
        lay.addWidget(self.cmb_filter)
        return f

    def _table_area(self):
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["#","Due Date","Title","Details","Category","Priority","Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget{border:none;font-size:13px;}
            QHeaderView::section{background:#1A1A2E;color:white;font-weight:bold;padding:8px;border:none;}
            QTableWidget::item:selected{background:#E74C3C;color:white;}
        """)
        scroll = QScrollArea(); scroll.setWidget(self.table); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        return scroll

    def _footer(self):
        f = QFrame(); f.setStyleSheet(f"background:{DARK};border-top:2px solid {COLOR};"); f.setFixedHeight(54)
        lay = QHBoxLayout(f); lay.setContentsMargins(24,0,24,0)
        self.lbl_ov = QLabel("")
        self.lbl_ov.setStyleSheet(f"color:{COLOR};font-size:15px;font-weight:bold;border:none;")
        lay.addWidget(self.lbl_ov); lay.addStretch()
        self.lbl_cnt = QLabel(""); self.lbl_cnt.setStyleSheet("color:#AAAAAA;font-size:13px;border:none;")
        lay.addWidget(self.lbl_cnt)
        return f

    def _load(self):
        today = dt_date.today().isoformat()
        rows = database.alert_get_active() if self.cmb_filter.currentIndex() == 0 else database.alert_get_all()
        self._rows = rows
        self.table.setRowCount(len(rows))
        overdue = 0
        for i, r in enumerate(rows):
            is_overdue = r["due_date"] <= today and not r["dismissed"]
            if is_overdue: overdue += 1
            p_color = {"High":"#C0392B","Normal":"#F39C12","Low":"#1E8449"}.get(r["priority"],"#555")
            vals = [str(i+1), r["due_date"], r["title"], r["body"] or "—",
                    r["category"], r["priority"], "✓ Done" if r["dismissed"] else ("⚠ OVERDUE" if is_overdue else "Active")]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if is_overdue and not r["dismissed"]:
                    item.setBackground(QColor("#FFF0F0"))
                if j == 5: item.setForeground(QColor(p_color))
                if j == 6 and is_overdue and not r["dismissed"]:
                    item.setForeground(QColor("#C0392B")); item.setFont(QFont("Arial",10,QFont.Bold))
                self.table.setItem(i, j, item)
        self.lbl_ov.setText(f"⚠  {overdue} Overdue" if overdue else "✅  All Clear")
        self.lbl_cnt.setText(f"{len(rows)} alerts")
        self._refresh_auto_alerts()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self._rows[row]["id"]

    def _add(self):
        dlg = AlertDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            from datetime import date
            database.alert_add(date.today().isoformat(), d["due"], d["title"], d["body"], d["category"], d["priority"])
            self._load()

    def _dismiss(self):
        aid = self._selected_id()
        if not aid: QMessageBox.warning(self,"Select","Select an alert first."); return
        database.alert_dismiss(aid); self._load()

    def _delete(self):
        aid = self._selected_id()
        if not aid: QMessageBox.warning(self,"Select","Select an alert first."); return
        if QMessageBox.question(self,"Delete","Delete this alert?",
            QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            database.alert_delete(aid); self._load()

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()
    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)


class AlertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Alert / Reminder")
        self.setFixedSize(440, 380)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,20,24,20); lay.setSpacing(12)
        lay.addWidget(QLabel("NEW REMINDER", styleSheet=f"font-size:16px;font-weight:bold;color:{DARK};"))
        form = QFormLayout(); form.setSpacing(10)
        self.due = QDateEdit(QDate.currentDate().addDays(7)); self.due.setCalendarPopup(True)
        self.due.setDisplayFormat("dd/MM/yyyy"); self.due.setMinimumHeight(40)
        self.title = QLineEdit(); self.title.setPlaceholderText("e.g. Pay Showal balance, Royalty due..."); self.title.setMinimumHeight(40)
        self.body  = QTextEdit(); self.body.setFixedHeight(70); self.body.setPlaceholderText("Details...")
        self.cat   = QComboBox(); self.cat.addItems(["Payment","Royalty","Salary","Fuel","General"]); self.cat.setMinimumHeight(40)
        self.pri   = QComboBox(); self.pri.addItems(["High","Normal","Low"]); self.pri.setMinimumHeight(40)
        for lbl,w in [("Due Date:",self.due),("Title:",self.title),("Details:",self.body),
                       ("Category:",self.cat),("Priority:",self.pri)]:
            form.addRow(QLabel(lbl,styleSheet="font-weight:bold;"), w)
        lay.addLayout(form); lay.addStretch()
        btns = QHBoxLayout()
        ok = QPushButton("✓  Save Reminder"); ok.setMinimumHeight(44)
        ok.setStyleSheet(f"background:{COLOR};color:white;border-radius:8px;border:none;font-size:14px;font-weight:bold;")
        ok.clicked.connect(self._save)
        ca = QPushButton("Cancel"); ca.setMinimumHeight(44)
        ca.setStyleSheet("background:#CCCCCC;color:#333;border-radius:8px;border:none;font-size:13px;")
        ca.clicked.connect(self.reject)
        btns.addWidget(ca); btns.addWidget(ok); lay.addLayout(btns)

    def _save(self):
        if not self.title.text().strip(): QMessageBox.warning(self,"Required","Enter title."); return
        self.accept()

    def data(self):
        return {"due":self.due.date().toString("yyyy-MM-dd"), "title":self.title.text().strip(),
                "body":self.body.toPlainText().strip(), "category":self.cat.currentText(),
                "priority":self.pri.currentText()}