"""
CH 8 — Surface / Land Owner Rent
Track rent payments to land owners: period covered, payment date,
cash or cheque, cheque number, bank, notes.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QDoubleSpinBox, QTextEdit,
    QAbstractItemView, QGridLayout, QSplitter, QStackedWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from datetime import date as dt_date
import database, config

DARK   = config.DARK
COLOR  = "#2C7873"   # deep teal — land/earth feel
GOLD   = "#F39C12"
RED    = "#C0392B"
GREEN  = "#1E8449"
BLUE   = "#1B4F72"
CASH_C = "#27AE60"
CHQ_C  = "#2980B9"


class LandRentModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 8 — Surface / Land Owner Rent")
        self.setMinimumSize(1380, 840)
        self._build_ui()
        self._load()

    # ── BUILD ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._kpi_bar())
        root.addWidget(self._toolbar())
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            "QSplitter{background:#EFEFEF;}"
            "QSplitter::handle{background:#CCCCCC;width:2px;}")
        splitter.addWidget(self._left_panel())
        splitter.addWidget(self._right_panel())
        splitter.setSizes([870, 400])
        root.addWidget(splitter, 1)

    def _topbar(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {COLOR};")
        f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28, 0, 28, 0)
        accent = QFrame(); accent.setFixedSize(6, 44)
        accent.setStyleSheet(f"background:{COLOR};border-radius:3px;border:none;")
        lay.addWidget(accent); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        vb.addWidget(QLabel("Chapter 8 — Surface / Land Owner Rent",
            styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel(
            "Record rent payments to land owners — period covered, payment date, cash or cheque, full history",
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
            ("total_paid",   "TOTAL RENT PAID (ALL TIME)", COLOR),
            ("this_year",    "THIS YEAR",                  GOLD),
            ("by_cash",      "PAID BY CASH",               CASH_C),
            ("by_cheque",    "PAID BY CHEQUE",             CHQ_C),
            ("owners",       "LAND OWNERS",                BLUE),
            ("last_payment", "LAST PAYMENT DATE",          RED),
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
                "font-size:20px;font-weight:bold;color:white;border:none;")
            vb.addWidget(lk); vb.addWidget(lv)
            self._kpi[key] = lv
            lay.addWidget(sep); lay.addWidget(card, 1)
        return f

    def _toolbar(self):
        f = QFrame()
        f.setStyleSheet("background:#F5F5F5;border-bottom:1px solid #DDDDDD;")
        f.setFixedHeight(60)
        lay = QHBoxLayout(f); lay.setContentsMargins(20, 0, 20, 0); lay.setSpacing(10)

        def btn(label, color, fn, width=180):
            b = QPushButton(label)
            b.setFixedHeight(42); b.setMinimumWidth(width)
            b.setStyleSheet(
                f"QPushButton{{background:{color};color:white;border-radius:8px;"
                f"border:none;font-size:13px;font-weight:bold;}}"
                f"QPushButton:hover{{opacity:.85;}}")
            b.clicked.connect(fn); return b

        lay.addWidget(btn("🏠  New Rent Payment", COLOR, self._add))
        lay.addWidget(btn("✏  Edit Selected",    BLUE,  self._edit, 140))
        lay.addWidget(btn("✕  Delete",           RED,   self._delete, 110))
        lay.addStretch()

        lay.addWidget(QLabel("Owner Filter:",
            styleSheet="font-size:12px;font-weight:bold;border:none;"))
        self.cmb_owner = QComboBox(); self.cmb_owner.setFixedHeight(38)
        self.cmb_owner.setMinimumWidth(200)
        self.cmb_owner.setStyleSheet(
            "font-size:13px;padding:4px 12px;border:2px solid #CCCCCC;"
            "border-radius:7px;background:white;")
        self.cmb_owner.currentIndexChanged.connect(self._apply_filter)
        lay.addWidget(self.cmb_owner)
        return f

    def _left_panel(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(f"background:white;border-bottom:2px solid {COLOR};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(QLabel("🏠  ALL RENT PAYMENTS",
            styleSheet="font-size:13px;font-weight:bold;color:#1A1A2E;border:none;"))
        hl.addStretch()
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size:12px;color:#AAAAAA;border:none;")
        hl.addWidget(self.lbl_count)
        lay.addWidget(hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "#", "Owner Name", "Land / Location",
            "Rent From", "Rent To", "Payment Date",
            "Mode", "Cheque / Bank", "Amount (PKR)"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed);  self.table.setColumnWidth(0, 36)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Fixed);  self.table.setColumnWidth(3, 95)
        hh.setSectionResizeMode(4, QHeaderView.Fixed);  self.table.setColumnWidth(4, 95)
        hh.setSectionResizeMode(5, QHeaderView.Fixed);  self.table.setColumnWidth(5, 100)
        hh.setSectionResizeMode(6, QHeaderView.Fixed);  self.table.setColumnWidth(6, 80)
        hh.setSectionResizeMode(7, QHeaderView.Stretch)
        hh.setSectionResizeMode(8, QHeaderView.Fixed);  self.table.setColumnWidth(8, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { border:none; font-size:12.5px; background:white; }
            QHeaderView::section {
                background:#1A1A2E; color:white; font-weight:bold;
                font-size:11px; padding:7px 4px; border:none;
                border-right:1px solid #2A2A4A;
            }
            QTableWidget::item { padding:5px 4px; }
            QTableWidget::item:alternate { background:#F0F8F6; }
            QTableWidget::item:selected { background:#2C7873; color:white; }
        """)
        lay.addWidget(self.table, 1)

        foot = QFrame()
        foot.setStyleSheet(f"background:{DARK};border-top:2px solid {COLOR};")
        foot.setFixedHeight(44)
        fl = QHBoxLayout(foot); fl.setContentsMargins(16, 0, 16, 0)
        self.lbl_total = QLabel("Total Paid: PKR 0")
        self.lbl_total.setStyleSheet(
            f"color:{COLOR};font-size:15px;font-weight:bold;border:none;")
        fl.addWidget(self.lbl_total); fl.addStretch()
        self.lbl_period = QLabel("")
        self.lbl_period.setStyleSheet("color:#AAAAAA;font-size:12px;border:none;")
        fl.addWidget(self.lbl_period)
        lay.addWidget(foot)
        return w

    def _right_panel(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        hdr = QFrame()
        hdr.setStyleSheet(f"background:white;border-bottom:2px solid {GOLD};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(QLabel("👤  PER OWNER SUMMARY",
            styleSheet="font-size:13px;font-weight:bold;color:#1A1A2E;border:none;"))
        lay.addWidget(hdr)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#FAFAFA;}")
        self._owner_widget = QWidget()
        self._owner_widget.setStyleSheet("background:#FAFAFA;")
        self._owner_lay = QVBoxLayout(self._owner_widget)
        self._owner_lay.setContentsMargins(12, 12, 12, 12)
        self._owner_lay.setSpacing(10)
        scroll.setWidget(self._owner_widget)
        lay.addWidget(scroll, 1)
        return w

    # ── DATA ───────────────────────────────────────────────────────────────────
    def _load(self):
        try:
            rows = database.land_get_all()
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e)); return

        self._all_rows = rows

        # Rebuild owner filter
        cur = self.cmb_owner.currentText()
        self.cmb_owner.blockSignals(True)
        self.cmb_owner.clear()
        self.cmb_owner.addItem("All Owners")
        owners = sorted(set(r["owner_name"] for r in rows))
        for o in owners:
            self.cmb_owner.addItem(o)
        idx = self.cmb_owner.findText(cur)
        self.cmb_owner.setCurrentIndex(max(idx, 0))
        self.cmb_owner.blockSignals(False)

        self._render_table(rows)
        self._render_owner_cards(rows)
        self._update_kpis(rows)

    def _update_kpis(self, rows):
        total = sum(float(r["amount"] or 0) for r in rows)
        year  = str(dt_date.today().year)
        this_year = sum(float(r["amount"] or 0) for r in rows
                        if r["payment_date"].startswith(year))
        cash_t = sum(float(r["amount"] or 0) for r in rows
                     if r["payment_mode"] == "Cash")
        chq_t  = sum(float(r["amount"] or 0) for r in rows
                     if r["payment_mode"] == "Cheque")
        owners = len(set(r["owner_name"] for r in rows))
        last   = max((r["payment_date"] for r in rows), default="—")
        self._kpi["total_paid"].setText(f"PKR {total:,.0f}")
        self._kpi["this_year"].setText(f"PKR {this_year:,.0f}")
        self._kpi["by_cash"].setText(f"PKR {cash_t:,.0f}")
        self._kpi["by_cheque"].setText(f"PKR {chq_t:,.0f}")
        self._kpi["owners"].setText(str(owners))
        self._kpi["last_payment"].setText(last)

    def _apply_filter(self):
        owner = self.cmb_owner.currentText()
        if owner == "All Owners":
            filtered = self._all_rows
        else:
            filtered = [r for r in self._all_rows if r["owner_name"] == owner]
        self._render_table(filtered)

    def _render_table(self, rows):
        self.table.setRowCount(len(rows))
        total = 0
        for i, r in enumerate(rows):
            mode  = r["payment_mode"] or "Cash"
            color = CASH_C if mode == "Cash" else CHQ_C
            amt   = float(r["amount"] or 0)
            total += amt
            chq_bank = ""
            if mode == "Cheque":
                chq_num  = r["cheque_number"] or ""
                bank     = r["bank_name"] or ""
                chq_bank = f"#{chq_num}" + (f"  {bank}" if bank else "") if chq_num else bank
            chq_bank = chq_bank or "—"

            vals = [
                str(i + 1),
                r["owner_name"] or "—",
                r["land_desc"] or "—",
                r["rent_from"] or "—",
                r["rent_to"]   or "—",
                r["payment_date"] or "—",
                mode,
                chq_bank,
                f"PKR {amt:,.0f}",
            ]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if j in (1, 2, 7):
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if j == 6:
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                if j == 8:
                    item.setForeground(QColor(COLOR))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table.setItem(i, j, item)

        self.lbl_count.setText(f"{len(rows)} payments")
        self.lbl_total.setText(f"Total Paid: PKR {total:,.0f}")
        if rows:
            dates = [r["payment_date"] for r in rows if r["payment_date"]]
            if dates:
                self.lbl_period.setText(
                    f"{min(dates)}  →  {max(dates)}")

    def _render_owner_cards(self, rows):
        while self._owner_lay.count():
            item = self._owner_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not rows:
            no = QLabel("No payments recorded yet")
            no.setStyleSheet("font-size:13px;color:#AAAAAA;border:none;")
            no.setAlignment(Qt.AlignCenter)
            self._owner_lay.addWidget(no)
            self._owner_lay.addStretch()
            return

        from collections import defaultdict
        by_owner = defaultdict(lambda: {"total": 0, "cash": 0, "cheque": 0,
                                        "count": 0, "periods": [], "last": ""})
        for r in rows:
            o   = r["owner_name"]
            amt = float(r["amount"] or 0)
            by_owner[o]["total"]  += amt
            by_owner[o]["count"]  += 1
            if r["payment_mode"] == "Cash": by_owner[o]["cash"]   += amt
            else:                            by_owner[o]["cheque"] += amt
            period = f"{r['rent_from']} → {r['rent_to']}"
            if period not in by_owner[o]["periods"]:
                by_owner[o]["periods"].append(period)
            if r["payment_date"] > by_owner[o]["last"]:
                by_owner[o]["last"] = r["payment_date"]

        grand = sum(d["total"] for d in by_owner.values()) or 1

        for owner, d in sorted(by_owner.items(),
                                 key=lambda x: x[1]["total"], reverse=True):
            share = d["total"] / grand * 100
            card  = QFrame()
            card.setStyleSheet(
                f"background:white;border-radius:10px;"
                f"border-left:4px solid {COLOR};"
                f"border-top:1px solid #DDD;"
                f"border-right:1px solid #DDD;"
                f"border-bottom:1px solid #DDD;")
            vb = QVBoxLayout(card)
            vb.setContentsMargins(14, 12, 14, 12); vb.setSpacing(7)

            # Name row
            nr = QHBoxLayout()
            nm = QLabel(f"🏠  {owner}")
            nm.setStyleSheet(
                "font-size:14px;font-weight:bold;color:#1A1A2E;border:none;")
            cnt_lbl = QLabel(f"{d['count']} payment{'s' if d['count']!=1 else ''}")
            cnt_lbl.setStyleSheet(
                f"font-size:11px;color:{COLOR};font-weight:bold;border:none;")
            nr.addWidget(nm); nr.addStretch(); nr.addWidget(cnt_lbl)
            vb.addLayout(nr)

            # Last payment
            if d["last"]:
                lp = QLabel(f"Last payment: {d['last']}")
                lp.setStyleSheet("font-size:11px;color:#888;border:none;")
                vb.addWidget(lp)

            # Progress bar
            bar_bg = QFrame(); bar_bg.setFixedHeight(8)
            bar_bg.setStyleSheet("background:#EEE;border-radius:4px;border:none;")
            bar_in = QFrame(bar_bg); bar_in.setFixedHeight(8); bar_in.move(0, 0)
            bar_in.setFixedWidth(max(int(share * 2.2), 6))
            bar_in.setStyleSheet(f"background:{COLOR};border-radius:4px;border:none;")
            vb.addWidget(bar_bg)

            # Stats
            sr = QHBoxLayout(); sr.setSpacing(0)
            for lbl, val, col in [
                ("TOTAL",  f"PKR {d['total']:,.0f}",  COLOR),
                ("CASH",   f"PKR {d['cash']:,.0f}",   CASH_C),
                ("CHEQUE", f"PKR {d['cheque']:,.0f}", CHQ_C),
                ("SHARE",  f"{share:.1f}%",            GOLD),
            ]:
                sw = QWidget(); sw.setStyleSheet("background:transparent;border:none;")
                sv = QVBoxLayout(sw)
                sv.setContentsMargins(0, 0, 14, 0); sv.setSpacing(1)
                sv.addWidget(QLabel(lbl,
                    styleSheet=f"font-size:8px;font-weight:bold;color:{col};"
                               "border:none;letter-spacing:1px;"))
                sv.addWidget(QLabel(val,
                    styleSheet=f"font-size:12px;font-weight:bold;"
                               "color:#1A1A2E;border:none;"))
                sr.addWidget(sw)
            sr.addStretch()
            vb.addLayout(sr)

            # Periods covered
            if d["periods"]:
                periods_str = "  |  ".join(d["periods"][:3])
                if len(d["periods"]) > 3:
                    periods_str += f"  + {len(d['periods'])-3} more"
                pl = QLabel(f"Periods: {periods_str}")
                pl.setStyleSheet("font-size:10px;color:#AAAAAA;border:none;")
                pl.setWordWrap(True)
                vb.addWidget(pl)

            self._owner_lay.addWidget(card)
        self._owner_lay.addStretch()

    # ── CRUD ───────────────────────────────────────────────────────────────────
    def _selected(self):
        row = self.table.currentRow()
        if row < 0: return None
        # find in _all_rows based on displayed table -- use filtered view
        filt = self.cmb_owner.currentText()
        displayed = self._all_rows if filt == "All Owners" else \
                    [r for r in self._all_rows if r["owner_name"] == filt]
        return displayed[row] if row < len(displayed) else None

    def _add(self):
        dlg = LandRentDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.land_add(d["owner"], d["land_desc"],
                              d["rent_from"], d["rent_to"],
                              d["payment_date"], d["amount"],
                              d["mode"], d["cheque_no"], d["bank"], d["notes"])
            self._load()

    def _edit(self):
        r = self._selected()
        if not r:
            QMessageBox.warning(self, "Select", "Select a payment first."); return
        dlg = LandRentDialog(row=r, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.land_edit(r["id"], d["owner"], d["land_desc"],
                               d["rent_from"], d["rent_to"],
                               d["payment_date"], d["amount"],
                               d["mode"], d["cheque_no"], d["bank"], d["notes"])
            self._load()

    def _delete(self):
        r = self._selected()
        if not r:
            QMessageBox.warning(self, "Select", "Select a payment first."); return
        if QMessageBox.question(self, "Delete",
                f"Delete rent payment of PKR {float(r['amount']):,.0f} "
                f"to {r['owner_name']}?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            database.land_delete(r["id"])
            self._load()

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()

    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)


# ═══════════════════════════════════════════════════════════════════
class LandRentDialog(QDialog):
    def __init__(self, row=None, parent=None):
        super().__init__(parent)
        self._row = row
        self.setWindowTitle("New Rent Payment" if not row else "Edit Rent Payment")
        self.setFixedSize(500, 580)
        self.setStyleSheet("QDialog{background:white;} QLabel{border:none;}")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22); lay.setSpacing(14)

        # Header bar
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:#2C787315;border-radius:8px;"
            f"border-left:4px solid #2C7873;"
            f"border-top:none;border-right:none;border-bottom:none;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14, 10, 14, 10)
        hl.addWidget(QLabel(
            "🏠  SURFACE / LAND RENT PAYMENT",
            styleSheet="font-size:14px;font-weight:bold;color:#2C7873;border:none;"))
        lay.addWidget(hdr)

        form = QFormLayout(); form.setSpacing(10); form.setLabelAlignment(Qt.AlignRight)

        def L(t): return QLabel(t, styleSheet="font-weight:bold;font-size:12px;")
        def inp(ph=""): w = QLineEdit(); w.setPlaceholderText(ph); w.setMinimumHeight(42); return w
        def dt(default_today=True):
            w = QDateEdit(QDate.currentDate() if default_today else QDate.currentDate().addMonths(-1))
            w.setCalendarPopup(True); w.setDisplayFormat("dd/MM/yyyy")
            w.setMinimumHeight(42); return w

        self.inp_owner   = inp("e.g. Malik Sahab, Haji Rehman...")
        self.inp_land    = inp("e.g. Plot A near mine, Eastern boundary...")
        self.inp_from    = dt(False)   # rent period start
        self.inp_to      = dt(True)    # rent period end
        self.inp_pdate   = dt(True)    # actual payment date
        self.inp_amount  = QDoubleSpinBox()
        self.inp_amount.setRange(0, 99999999); self.inp_amount.setDecimals(0)
        self.inp_amount.setSuffix(" PKR"); self.inp_amount.setMinimumHeight(42)
        self.inp_mode    = QComboBox()
        self.inp_mode.addItems(["Cash", "Cheque", "Bank Transfer"])
        self.inp_mode.setMinimumHeight(42)
        self.inp_mode.currentTextChanged.connect(self._on_mode_changed)
        self.inp_cheque  = inp("Cheque number")
        self.inp_bank    = inp("Bank name  e.g. HBL, UBL...")
        self.inp_notes   = QTextEdit(); self.inp_notes.setFixedHeight(68)
        self.inp_notes.setPlaceholderText("Any additional notes...")

        form.addRow(L("Land Owner:"),   self.inp_owner)
        form.addRow(L("Land / Location:"), self.inp_land)
        form.addRow(L("Rent Period — From:"), self.inp_from)
        form.addRow(L("Rent Period — To:"),   self.inp_to)
        form.addRow(L("Payment Date:"),  self.inp_pdate)
        form.addRow(L("Amount:"),        self.inp_amount)
        form.addRow(L("Payment Mode:"),  self.inp_mode)

        # Cheque fields (shown/hidden by mode)
        self._lbl_cheque = L("Cheque No.:")
        self._lbl_bank   = L("Bank:")
        form.addRow(self._lbl_cheque, self.inp_cheque)
        form.addRow(self._lbl_bank,   self.inp_bank)
        form.addRow(L("Notes:"),     self.inp_notes)
        lay.addLayout(form)

        # Pre-fill
        if self._row:
            r = self._row
            self.inp_owner.setText(r["owner_name"] or "")
            self.inp_land.setText(r["land_desc"] or "")
            self.inp_from.setDate(QDate.fromString(r["rent_from"], "yyyy-MM-dd"))
            self.inp_to.setDate(QDate.fromString(r["rent_to"], "yyyy-MM-dd"))
            self.inp_pdate.setDate(QDate.fromString(r["payment_date"], "yyyy-MM-dd"))
            self.inp_amount.setValue(float(r["amount"] or 0))
            mi = self.inp_mode.findText(r["payment_mode"] or "Cash")
            self.inp_mode.setCurrentIndex(max(mi, 0))
            self.inp_cheque.setText(r["cheque_number"] or "")
            self.inp_bank.setText(r["bank_name"] or "")
            self.inp_notes.setPlainText(r["notes"] or "")

        self._on_mode_changed(self.inp_mode.currentText())

        lay.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setMinimumHeight(46)
        cancel.setStyleSheet(
            "background:#DDDDDD;color:#333;border-radius:8px;"
            "border:none;font-size:13px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("🏠  Save Rent Payment"); save.setMinimumHeight(46)
        save.setStyleSheet(
            "background:#2C7873;color:white;border-radius:8px;"
            "border:none;font-size:14px;font-weight:bold;")
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save, 1)
        lay.addLayout(btns)

    def _on_mode_changed(self, mode):
        show = (mode == "Cheque")
        self.inp_cheque.setVisible(show); self._lbl_cheque.setVisible(show)
        bank_show = mode in ("Cheque", "Bank Transfer")
        self.inp_bank.setVisible(bank_show); self._lbl_bank.setVisible(bank_show)

    def _save(self):
        if not self.inp_owner.text().strip():
            QMessageBox.warning(self, "Required", "Enter land owner name."); return
        if self.inp_amount.value() <= 0:
            QMessageBox.warning(self, "Required", "Enter amount > 0."); return
        if self.inp_from.date() > self.inp_to.date():
            QMessageBox.warning(self, "Invalid", "Rent period start must be before end."); return
        self.accept()

    def data(self):
        return {
            "owner":       self.inp_owner.text().strip(),
            "land_desc":   self.inp_land.text().strip(),
            "rent_from":   self.inp_from.date().toString("yyyy-MM-dd"),
            "rent_to":     self.inp_to.date().toString("yyyy-MM-dd"),
            "payment_date":self.inp_pdate.date().toString("yyyy-MM-dd"),
            "amount":      self.inp_amount.value(),
            "mode":        self.inp_mode.currentText(),
            "cheque_no":   self.inp_cheque.text().strip(),
            "bank":        self.inp_bank.text().strip(),
            "notes":       self.inp_notes.toPlainText().strip(),
        }