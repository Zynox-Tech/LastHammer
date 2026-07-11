"""
CH 15 — Diesel & Cash Distribution Tracker
Log every litre of diesel and every rupee of cash given out.
Who got it, how much, for what machine/vehicle, for what purpose.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QDoubleSpinBox, QTextEdit,
    QAbstractItemView, QGridLayout, QSplitter, QTabWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from datetime import date as dt_date, timedelta
import database, config

DARK    = config.DARK
DIESEL  = "#E67E22"   # orange — diesel
CASH    = "#1E8449"   # green  — cash
RED     = "#C0392B"
BLUE    = "#1B4F72"
GOLD    = "#F39C12"
PURPLE  = "#6C3483"


# ═══════════════════════════════════════════════════════════════════
class FuelTrackerModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 15 — Diesel & Cash Distribution Tracker")
        self.setMinimumSize(1380, 860)
        self._build_ui()
        self._load()

    # ── BUILD ──────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._kpi_bar())
        root.addWidget(self._toolbar())

        # Split: left=log table, right=breakdown
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            "QSplitter{background:#EFEFEF;}"
            "QSplitter::handle{background:#DDDDDD;width:2px;}")
        splitter.addWidget(self._left_panel())
        splitter.addWidget(self._right_panel())
        splitter.setSizes([850, 420])
        root.addWidget(splitter, 1)

    def _topbar(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {DIESEL};")
        f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28, 0, 28, 0)
        accent = QFrame(); accent.setFixedSize(6, 44)
        accent.setStyleSheet(f"background:{DIESEL};border-radius:3px;border:none;")
        lay.addWidget(accent); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        vb.addWidget(QLabel("Chapter 15 — Diesel & Cash Distribution Tracker",
            styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel(
            "Track every litre of diesel and every rupee of cash given to machines, vehicles and workers",
            styleSheet="color:#AAAAAA;font-size:12px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Dashboard")
        btn.setFixedHeight(40); btn.setMinimumWidth(160)
        btn.setStyleSheet(
            "QPushButton{background:#2C2C4E;color:white;border-radius:7px;"
            "border:none;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#3D3D6E;}")
        btn.clicked.connect(self._back)
        lay.addWidget(btn)
        return f

    def _kpi_bar(self):
        f = QFrame()
        f.setStyleSheet("background:#12122A;border-bottom:1px solid #2A2A4A;")
        f.setFixedHeight(90)
        lay = QHBoxLayout(f); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self._kpi = {}
        specs = [
            ("total_diesel_amt", "TOTAL DIESEL GIVEN",   DIESEL),
            ("total_diesel_ltr", "TOTAL LITRES",         GOLD),
            ("total_cash",       "TOTAL CASH GIVEN",     CASH),
            ("grand_total",      "COMBINED TOTAL",       RED),
            ("entries_today",    "ENTRIES TODAY",        BLUE),
            ("recipients",       "UNIQUE RECIPIENTS",   PURPLE),
        ]
        for key, title, color in specs:
            sep = QFrame()
            sep.setStyleSheet("background:#2A2A4A;border:none;"); sep.setFixedWidth(1)
            card = QFrame()
            card.setStyleSheet("background:transparent;border:none;")
            vb = QVBoxLayout(card); vb.setContentsMargins(20, 10, 20, 10); vb.setSpacing(3)
            lk = QLabel(title)
            lk.setStyleSheet(
                f"font-size:9px;font-weight:bold;color:{color};"
                "border:none;letter-spacing:1px;")
            lv = QLabel("—")
            lv.setStyleSheet(
                "font-size:22px;font-weight:bold;color:white;border:none;")
            vb.addWidget(lk); vb.addWidget(lv)
            self._kpi[key] = lv
            lay.addWidget(sep); lay.addWidget(card, 1)
        return f

    def _toolbar(self):
        f = QFrame()
        f.setStyleSheet("background:#F5F5F5;border-bottom:1px solid #DDDDDD;")
        f.setFixedHeight(60)
        lay = QHBoxLayout(f); lay.setContentsMargins(20, 0, 20, 0); lay.setSpacing(10)

        def btn(label, color, fn, width=160):
            b = QPushButton(label)
            b.setFixedHeight(40); b.setMinimumWidth(width)
            b.setStyleSheet(
                f"QPushButton{{background:{color};color:white;border-radius:7px;"
                f"border:none;font-size:13px;font-weight:bold;}}"
                f"QPushButton:hover{{opacity:.85;}}")
            b.clicked.connect(fn); return b

        lay.addWidget(btn(f"⛽  Add Diesel Entry",  DIESEL, self._add_diesel))
        lay.addWidget(btn(f"💵  Add Cash Entry",    CASH,   self._add_cash))
        lay.addWidget(btn(f"✏  Edit",              BLUE,   self._edit, 110))
        lay.addWidget(btn(f"✕  Delete",            RED,    self._delete, 110))
        lay.addStretch()

        # Filter
        self.cmb_filter = QComboBox(); self.cmb_filter.setFixedHeight(38)
        self.cmb_filter.addItems(["All Entries", "Diesel Only", "Cash Only"])
        self.cmb_filter.setStyleSheet(
            "font-size:13px;padding:4px 12px;border:2px solid #CCCCCC;"
            "border-radius:7px;background:white;font-weight:bold;")
        self.cmb_filter.currentIndexChanged.connect(self._load)
        lay.addWidget(self.cmb_filter)

        # Date range
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setFixedHeight(38); self.date_from.setFixedWidth(130)
        self.date_from.setStyleSheet(
            "font-size:12px;border:2px solid #CCCCCC;border-radius:7px;padding:4px;")
        self.date_from.dateChanged.connect(self._load)

        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setFixedHeight(38); self.date_to.setFixedWidth(130)
        self.date_to.setStyleSheet(
            "font-size:12px;border:2px solid #CCCCCC;border-radius:7px;padding:4px;")
        self.date_to.dateChanged.connect(self._load)

        lay.addWidget(QLabel("From:", styleSheet="font-size:12px;font-weight:bold;border:none;"))
        lay.addWidget(self.date_from)
        lay.addWidget(QLabel("To:", styleSheet="font-size:12px;font-weight:bold;border:none;"))
        lay.addWidget(self.date_to)
        return f

    def _left_panel(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        # Header
        hdr = QFrame()
        hdr.setStyleSheet(f"background:white;border-bottom:2px solid {DIESEL};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(QLabel("📋  DISTRIBUTION LOG",
            styleSheet="font-size:13px;font-weight:bold;color:#1A1A2E;border:none;"))
        hl.addStretch()
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size:12px;color:#AAAAAA;border:none;")
        hl.addWidget(self.lbl_count)
        lay.addWidget(hdr)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "#", "Type", "Date", "Given To", "Category",
            "Qty / Litres", "Rate", "Amount (PKR)", "Purpose / Ref"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed);  self.table.setColumnWidth(0, 36)
        hh.setSectionResizeMode(1, QHeaderView.Fixed);  self.table.setColumnWidth(1, 76)
        hh.setSectionResizeMode(2, QHeaderView.Fixed);  self.table.setColumnWidth(2, 95)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Fixed);  self.table.setColumnWidth(4, 90)
        hh.setSectionResizeMode(5, QHeaderView.Fixed);  self.table.setColumnWidth(5, 90)
        hh.setSectionResizeMode(6, QHeaderView.Fixed);  self.table.setColumnWidth(6, 80)
        hh.setSectionResizeMode(7, QHeaderView.Fixed);  self.table.setColumnWidth(7, 105)
        hh.setSectionResizeMode(8, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { border:none; font-size:12px; background:white; }
            QHeaderView::section {
                background:#1A1A2E; color:white; font-weight:bold;
                font-size:11px; padding:7px 4px; border:none;
                border-right:1px solid #2A2A4A;
            }
            QTableWidget::item { padding:5px 4px; }
            QTableWidget::item:alternate { background:#FFF8F0; }
            QTableWidget::item:selected { background:#E67E22; color:white; }
        """)
        lay.addWidget(self.table, 1)

        # Footer totals bar
        foot = QFrame()
        foot.setStyleSheet(f"background:{DARK};border-top:2px solid {DIESEL};")
        foot.setFixedHeight(44)
        fl = QHBoxLayout(foot); fl.setContentsMargins(16, 0, 16, 0); fl.setSpacing(30)
        self.lbl_foot_diesel = QLabel("Diesel: —")
        self.lbl_foot_diesel.setStyleSheet(
            f"color:{DIESEL};font-size:13px;font-weight:bold;border:none;")
        self.lbl_foot_cash = QLabel("Cash: —")
        self.lbl_foot_cash.setStyleSheet(
            f"color:{CASH};font-size:13px;font-weight:bold;border:none;")
        self.lbl_foot_total = QLabel("Total: —")
        self.lbl_foot_total.setStyleSheet(
            f"color:white;font-size:14px;font-weight:bold;border:none;")
        fl.addWidget(self.lbl_foot_diesel)
        fl.addWidget(self.lbl_foot_cash)
        fl.addStretch()
        fl.addWidget(self.lbl_foot_total)
        lay.addWidget(foot)
        return w

    def _right_panel(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        hdr = QFrame()
        hdr.setStyleSheet(f"background:white;border-bottom:2px solid {CASH};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(QLabel("👤  PER RECIPIENT BREAKDOWN",
            styleSheet="font-size:13px;font-weight:bold;color:#1A1A2E;border:none;"))
        lay.addWidget(hdr)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#FAFAFA;}")
        self._rp_widget = QWidget(); self._rp_widget.setStyleSheet("background:#FAFAFA;")
        self._rp_lay = QVBoxLayout(self._rp_widget)
        self._rp_lay.setContentsMargins(12, 12, 12, 12); self._rp_lay.setSpacing(8)
        scroll.setWidget(self._rp_widget)
        lay.addWidget(scroll, 1)
        return w

    # ── DATA ──────────────────────────────────────────────────────────
    def _load(self):
        d_from = self.date_from.date().toString("yyyy-MM-dd")
        d_to   = self.date_to.date().toString("yyyy-MM-dd")
        filt   = self.cmb_filter.currentIndex()
        etype  = {0: "All", 1: "Diesel", 2: "Cash"}.get(filt, "All")

        try:
            rows = database.fuel_get_range(d_from, d_to, etype)
            totals = database.fuel_totals(d_from, d_to)
            breakdown = database.fuel_by_recipient(d_from, d_to)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e)); return

        self._rows = rows
        self._render_table(rows, totals)
        self._render_breakdown(breakdown, totals)
        self._update_kpis(rows, totals)

    def _update_kpis(self, rows, totals):
        today = dt_date.today().isoformat()
        today_count = sum(1 for r in rows if r["date"] == today)
        recipients  = len(set(r["given_to"] for r in rows))
        self._kpi["total_diesel_amt"].setText(f"PKR {totals['diesel_amount']:,.0f}")
        self._kpi["total_diesel_ltr"].setText(f"{totals['diesel_litres']:,.0f} L")
        self._kpi["total_cash"].setText(f"PKR {totals['cash_amount']:,.0f}")
        self._kpi["grand_total"].setText(f"PKR {totals['total']:,.0f}")
        self._kpi["entries_today"].setText(str(today_count))
        self._kpi["recipients"].setText(str(recipients))

    def _render_table(self, rows, totals):
        self.table.setRowCount(len(rows))
        d_total = c_total = 0
        for i, r in enumerate(rows):
            etype  = r["entry_type"] or "Diesel"
            color  = DIESEL if etype == "Diesel" else CASH
            amt    = float(r["amount"] or 0)
            qty    = float(r["quantity"] or 0)
            rate   = float(r["rate_per_unit"] or 0)
            if etype == "Diesel": d_total += amt
            else: c_total += amt

            qty_str  = f"{qty:,.1f} L" if etype == "Diesel" and qty else (f"{qty:,.0f}" if qty else "—")
            rate_str = f"PKR {rate:,.0f}/L" if etype == "Diesel" and rate else ("—" if not rate else f"PKR {rate:,.0f}")
            ref      = r["ref_chapter"] or ""
            purpose  = r["purpose"] or ""
            purpose_full = (purpose + (f" [{ref}]" if ref else "")).strip() or "—"

            vals = [
                str(i + 1),
                etype,
                r["date"],
                r["given_to"] or "—",
                r["category"] or "—",
                qty_str,
                rate_str,
                f"PKR {amt:,.0f}",
                purpose_full,
            ]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if j in (3, 8):
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if j == 1:  # Type badge
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                if j == 7:  # Amount
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                # Row background tint
                tint = QColor(DIESEL if etype == "Diesel" else CASH)
                tint.setAlpha(15)
                item.setBackground(tint)
                self.table.setItem(i, j, item)

        self.lbl_count.setText(f"{len(rows)} entries")
        self.lbl_foot_diesel.setText(f"⛽  Diesel: PKR {d_total:,.0f}")
        self.lbl_foot_cash.setText(f"💵  Cash: PKR {c_total:,.0f}")
        self.lbl_foot_total.setText(f"Total: PKR {(d_total+c_total):,.0f}")

    def _render_breakdown(self, breakdown, totals):
        # Clear
        while self._rp_lay.count():
            item = self._rp_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not breakdown:
            no = QLabel("No data in this period")
            no.setStyleSheet("font-size:13px;color:#AAAAAA;border:none;")
            no.setAlignment(Qt.AlignCenter)
            self._rp_lay.addWidget(no)
            self._rp_lay.addStretch()
            return

        # Group by recipient
        from collections import defaultdict
        by_person = defaultdict(lambda: {"diesel": 0, "diesel_l": 0, "cash": 0, "count": 0})
        for r in breakdown:
            person = str(r["given_to"])
            etype  = str(r["entry_type"])
            amt    = float(r["total"] or 0)
            qty    = float(r["qty"] or 0)
            cnt    = int(r["cnt"] or 0)
            if etype == "Diesel":
                by_person[person]["diesel"]   += amt
                by_person[person]["diesel_l"] += qty
            else:
                by_person[person]["cash"] += amt
            by_person[person]["count"] += cnt

        grand = totals["total"] or 1  # avoid div/0

        for person, d in sorted(by_person.items(),
                                  key=lambda x: x[1]["diesel"]+x[1]["cash"], reverse=True):
            total_person = d["diesel"] + d["cash"]
            share = (total_person / grand * 100)

            card = QFrame()
            card.setStyleSheet(
                f"background:white;border-radius:10px;"
                f"border-left:4px solid {DIESEL};"
                f"border-top:1px solid #EEE;border-right:1px solid #EEE;"
                f"border-bottom:1px solid #EEE;")
            vb = QVBoxLayout(card)
            vb.setContentsMargins(14, 10, 14, 10); vb.setSpacing(6)

            # Name row
            nr = QHBoxLayout()
            nm = QLabel(person)
            nm.setStyleSheet(
                f"font-size:14px;font-weight:bold;color:#1A1A2E;border:none;")
            cnt_lbl = QLabel(f"{d['count']} entries")
            cnt_lbl.setStyleSheet(
                f"font-size:11px;color:{DIESEL};font-weight:bold;border:none;")
            nr.addWidget(nm); nr.addStretch(); nr.addWidget(cnt_lbl)
            vb.addLayout(nr)

            # Progress bar
            bar_bg = QFrame(); bar_bg.setFixedHeight(7)
            bar_bg.setStyleSheet("background:#EEE;border-radius:4px;border:none;")
            bar_inner = QFrame(bar_bg); bar_inner.setFixedHeight(7); bar_inner.move(0, 0)
            bar_inner.setFixedWidth(max(int(share * 2.1), 4))
            bar_inner.setStyleSheet(f"background:{DIESEL};border-radius:4px;border:none;")
            vb.addWidget(bar_bg)

            # Stat row
            sr = QHBoxLayout(); sr.setSpacing(0)
            stats = []
            if d["diesel"] > 0:
                stats.append(("DIESEL", f"PKR {d['diesel']:,.0f}", DIESEL))
                stats.append(("LITRES", f"{d['diesel_l']:,.0f} L", GOLD))
            if d["cash"] > 0:
                stats.append(("CASH", f"PKR {d['cash']:,.0f}", CASH))
            stats.append(("TOTAL", f"PKR {total_person:,.0f}", RED))
            stats.append(("SHARE", f"{share:.1f}%", PURPLE))
            for lbl, val, col in stats:
                sw = QWidget(); sw.setStyleSheet("background:transparent;border:none;")
                sv = QVBoxLayout(sw); sv.setContentsMargins(0, 0, 14, 0); sv.setSpacing(1)
                sv.addWidget(QLabel(lbl, styleSheet=f"font-size:8px;font-weight:bold;color:{col};border:none;letter-spacing:1px;"))
                sv.addWidget(QLabel(val, styleSheet=f"font-size:12px;font-weight:bold;color:#1A1A2E;border:none;"))
                sr.addWidget(sw)
            sr.addStretch()
            vb.addLayout(sr)
            self._rp_lay.addWidget(card)

        self._rp_lay.addStretch()

    # ── CRUD ACTIONS ──────────────────────────────────────────────────
    def _add_diesel(self):
        dlg = FuelEntryDialog("Diesel", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.fuel_add(d["date"], "Diesel", d["given_to"], d["category"],
                              d["quantity"], "Litres", d["rate"], d["amount"],
                              d["vehicle_reg"], d["purpose"], d["ref_chapter"])
            self._load()

    def _add_cash(self):
        dlg = FuelEntryDialog("Cash", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.fuel_add(d["date"], "Cash", d["given_to"], d["category"],
                              0, "PKR", 0, d["amount"],
                              d["vehicle_reg"], d["purpose"], d["ref_chapter"])
            self._load()

    def _edit(self):
        r = self._selected()
        if not r: QMessageBox.warning(self, "Select", "Select a row first."); return
        dlg = FuelEntryDialog(r["entry_type"], row=r, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.fuel_edit(r["id"], d["date"], r["entry_type"], d["given_to"],
                               d["category"], d["quantity"], "Litres" if r["entry_type"]=="Diesel" else "PKR",
                               d["rate"], d["amount"], d["vehicle_reg"],
                               d["purpose"], d["ref_chapter"])
            self._load()

    def _delete(self):
        r = self._selected()
        if not r: QMessageBox.warning(self, "Select", "Select a row first."); return
        if QMessageBox.question(self, "Delete",
                f"Delete this {r['entry_type']} entry for {r['given_to']}?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            database.fuel_delete(r["id"]); self._load()

    def _selected(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self._rows[row]

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()

    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)


# ═══════════════════════════════════════════════════════════════════
class FuelEntryDialog(QDialog):
    def __init__(self, entry_type="Diesel", row=None, parent=None):
        super().__init__(parent)
        self._etype = entry_type
        color = DIESEL if entry_type == "Diesel" else CASH
        icon  = "⛽" if entry_type == "Diesel" else "💵"
        self.setWindowTitle(
            f"{'Edit' if row else 'New'} {entry_type} Entry")
        self.setFixedSize(480, entry_type == "Diesel" and 520 or 460)
        self.setStyleSheet(f"QDialog{{background:white;}} QLabel{{border:none;}}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(14)

        # Title bar
        title_bar = QFrame()
        title_bar.setStyleSheet(
            f"background:{color}15;border-radius:8px;"
            f"border-left:4px solid {color};border-top:none;"
            f"border-right:none;border-bottom:none;")
        tb = QHBoxLayout(title_bar); tb.setContentsMargins(14, 10, 14, 10)
        tb.addWidget(QLabel(f"{icon}  {entry_type.upper()} ENTRY",
            styleSheet=f"font-size:15px;font-weight:bold;color:{color};border:none;"))
        lay.addWidget(title_bar)

        # Form
        form = QFormLayout(); form.setSpacing(10); form.setLabelAlignment(Qt.AlignRight)

        def L(t): return QLabel(t, styleSheet="font-weight:bold;font-size:12px;")

        self.inp_date = QDateEdit(QDate.currentDate())
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setMinimumHeight(42)

        self.inp_given = QLineEdit()
        self.inp_given.setPlaceholderText("e.g. Showal Machine, Malik Driver, CH5 Loader...")
        self.inp_given.setMinimumHeight(42)

        self.inp_category = QComboBox()
        self.inp_category.addItems(["Machine", "Vehicle / Truck", "Worker", "Generator", "Other"])
        self.inp_category.setMinimumHeight(42)

        self.inp_vehicle = QLineEdit()
        self.inp_vehicle.setPlaceholderText("e.g. JU-1234  (optional)")
        self.inp_vehicle.setMinimumHeight(42)

        self.inp_amount = QDoubleSpinBox()
        self.inp_amount.setRange(0, 99999999); self.inp_amount.setDecimals(0)
        self.inp_amount.setSuffix(" PKR"); self.inp_amount.setMinimumHeight(42)

        if entry_type == "Diesel":
            self.inp_qty = QDoubleSpinBox()
            self.inp_qty.setRange(0, 99999); self.inp_qty.setDecimals(1)
            self.inp_qty.setSuffix(" Litres"); self.inp_qty.setMinimumHeight(42)
            self.inp_rate = QDoubleSpinBox()
            self.inp_rate.setRange(0, 9999); self.inp_rate.setDecimals(0)
            self.inp_rate.setSuffix(" PKR/L"); self.inp_rate.setMinimumHeight(42)
            # Auto-calculate amount when qty or rate changes
            self.inp_qty.valueChanged.connect(self._recalc)
            self.inp_rate.valueChanged.connect(self._recalc)

        self.inp_purpose = QLineEdit()
        self.inp_purpose.setPlaceholderText("e.g. Excavator machine work, Site visit...")
        self.inp_purpose.setMinimumHeight(42)

        self.inp_ref = QComboBox()
        self.inp_ref.addItems(["", "CH1 General", "CH3 Excavator", "CH4 Dumprei",
                                "CH5 Fleet", "CH9 Advance", "Other"])
        self.inp_ref.setMinimumHeight(42)

        form.addRow(L("Date:"), self.inp_date)
        form.addRow(L("Given To:"), self.inp_given)
        form.addRow(L("Category:"), self.inp_category)
        form.addRow(L("Vehicle Reg:"), self.inp_vehicle)
        if entry_type == "Diesel":
            form.addRow(L("Quantity (L):"), self.inp_qty)
            form.addRow(L("Rate/Litre:"), self.inp_rate)
        form.addRow(L("Amount (PKR):"), self.inp_amount)
        form.addRow(L("Purpose:"), self.inp_purpose)
        form.addRow(L("Ref Chapter:"), self.inp_ref)
        lay.addLayout(form)

        # Pre-fill if editing
        if row:
            self.inp_date.setDate(QDate.fromString(row["date"], "yyyy-MM-dd"))
            self.inp_given.setText(str(row["given_to"] or ""))
            idx = self.inp_category.findText(str(row["category"] or "Machine"))
            self.inp_category.setCurrentIndex(max(idx, 0))
            self.inp_vehicle.setText(str(row["vehicle_reg"] or ""))
            self.inp_amount.setValue(float(row["amount"] or 0))
            if entry_type == "Diesel":
                self.inp_qty.setValue(float(row["quantity"] or 0))
                self.inp_rate.setValue(float(row["rate_per_unit"] or 0))
            self.inp_purpose.setText(str(row["purpose"] or ""))
            ri = self.inp_ref.findText(str(row["ref_chapter"] or ""))
            self.inp_ref.setCurrentIndex(max(ri, 0))

        lay.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setMinimumHeight(46)
        cancel.setStyleSheet(
            "background:#DDDDDD;color:#333;border-radius:8px;border:none;font-size:13px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton(f"{icon}  Save {entry_type} Entry"); save.setMinimumHeight(46)
        save.setStyleSheet(
            f"background:{color};color:white;border-radius:8px;"
            f"border:none;font-size:14px;font-weight:bold;")
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save, 1)
        lay.addLayout(btns)

    def _recalc(self):
        qty  = self.inp_qty.value()
        rate = self.inp_rate.value()
        if qty > 0 and rate > 0:
            self.inp_amount.setValue(qty * rate)

    def _save(self):
        if not self.inp_given.text().strip():
            QMessageBox.warning(self, "Required", "Enter who received this."); return
        if self.inp_amount.value() <= 0:
            QMessageBox.warning(self, "Required", "Enter amount > 0."); return
        self.accept()

    def data(self):
        return {
            "date":        self.inp_date.date().toString("yyyy-MM-dd"),
            "given_to":    self.inp_given.text().strip(),
            "category":    self.inp_category.currentText(),
            "vehicle_reg": self.inp_vehicle.text().strip(),
            "quantity":    self.inp_qty.value() if self._etype == "Diesel" else 0,
            "rate":        self.inp_rate.value() if self._etype == "Diesel" else 0,
            "amount":      self.inp_amount.value(),
            "purpose":     self.inp_purpose.text().strip(),
            "ref_chapter": self.inp_ref.currentText(),
        }