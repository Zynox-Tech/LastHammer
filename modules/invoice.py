"""
Invoice Module — Last Hammer EMS  (CH 8)
Generates invoices for Dumprei, Excavator, Truck, Loader, Royalty.
Shows full REVIEW DIALOG before generating — user must confirm all figures.
"""
import os
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QComboBox, QDateEdit, QMessageBox, QProgressDialog,
    QApplication, QGridLayout
)
from PyQt5.QtCore import Qt, QDate
import database
import config

GOLD = "#F39C12"


class InvoiceModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 8 — Invoice Generator")
        self.setMinimumSize(1280, 800)
        self._last_pdf_path = None
        self._build_ui()
        self._on_type_changed(0)

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_topbar())
        root.addWidget(self._make_body(), 1)

    def _make_topbar(self):
        frame = QFrame()
        frame.setStyleSheet(f"background:{config.DARK};border-bottom:3px solid {GOLD};")
        frame.setFixedHeight(80)
        lay = QHBoxLayout(frame); lay.setContentsMargins(30, 0, 30, 0)
        bar = QFrame(); bar.setFixedWidth(6); bar.setFixedHeight(46)
        bar.setStyleSheet(f"background:{GOLD};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        t = QLabel("Chapter 8 — Invoice Generator")
        t.setStyleSheet("color:white;font-size:22px;font-weight:bold;border:none;")
        s = QLabel("Select person / vehicle, date range — then review every figure before generating PDF")
        s.setStyleSheet("color:#AAAAAA;font-size:12px;border:none;")
        vb.addWidget(t); vb.addWidget(s)
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Back to Dashboard")
        btn.setFixedHeight(44); btn.setMinimumWidth(200)
        btn.setStyleSheet("""
            QPushButton{background:#2C2C4E;color:white;border-radius:8px;
                border:none;font-size:14px;font-weight:bold;}
            QPushButton:hover{background:#3D3D6E;}""")
        btn.clicked.connect(self._go_back)
        lay.addWidget(btn)
        return frame

    def _make_body(self):
        w = QWidget(); w.setStyleSheet("background:#EFEFEF;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(30, 24, 30, 24); lay.setSpacing(24)
        lay.addWidget(self._make_left_panel(), 0)
        lay.addWidget(self._make_right_panel(), 1)
        return w

    def _make_left_panel(self):
        frame = QFrame(); frame.setFixedWidth(380)
        frame.setStyleSheet("background:white;border-radius:14px;border:1px solid #DDDDDD;")
        lay = QVBoxLayout(frame); lay.setContentsMargins(24, 24, 24, 24); lay.setSpacing(16)

        def sec(t):
            l = QLabel(t)
            l.setStyleSheet("font-size:10px;font-weight:bold;color:#AAAAAA;letter-spacing:1px;border:none;")
            return l

        def combo():
            c = QComboBox()
            c.setMinimumHeight(46)
            c.setStyleSheet(f"""
                QComboBox{{font-size:13px;font-weight:bold;padding:6px 12px;
                    border:2px solid #DDDDDD;border-radius:8px;background:white;}}
                QComboBox:focus{{border-color:{GOLD};}}
                QComboBox::drop-down{{border:none;width:28px;}}""")
            return c

        def datepick():
            d = QDateEdit(); d.setCalendarPopup(True)
            d.setDisplayFormat("dd/MM/yyyy"); d.setMinimumHeight(46)
            d.setStyleSheet(f"""
                QDateEdit{{font-size:13px;font-weight:bold;padding:6px 12px;
                    border:2px solid #DDDDDD;border-radius:8px;background:white;}}
                QDateEdit:focus{{border-color:{GOLD};}}""")
            return d

        lay.addWidget(QLabel("🧾  Generate Invoice",
            styleSheet=f"font-size:18px;font-weight:bold;color:{config.DARK};border:none;"))

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#EEEEEE;border:none;border-top:1px solid #EEEEEE;")
        lay.addWidget(sep)

        # Type
        lay.addWidget(sec("STEP 1 — INVOICE TYPE"))
        self.cmb_type = combo()
        self.cmb_type.addItems([
            "Dumprei Expenditure",
            "Excavator (Showal Machine)",
            "Truck / Dumper (Fleet)",
            "Loader (Fleet)",
            "Royalty to Government",
            "Land / Surface Rent",
        ])
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        lay.addWidget(self.cmb_type)

        # Person
        lay.addWidget(sec("STEP 2 — PERSON / VEHICLE"))
        self.cmb_person = combo()
        self.cmb_person.currentIndexChanged.connect(self._refresh_preview)
        lay.addWidget(self.cmb_person)

        # Dates
        lay.addWidget(sec("STEP 3 — DATE RANGE"))
        dr = QHBoxLayout(); dr.setSpacing(10)
        for label, attr, default_offset in [("From:", "date_from", -30), ("To:", "date_to", 0)]:
            col = QVBoxLayout(); col.setSpacing(3)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:11px;font-weight:bold;border:none;color:#555;")
            dp = datepick()
            dp.setDate(QDate.currentDate().addDays(default_offset))
            setattr(self, attr, dp)
            dp.dateChanged.connect(self._refresh_preview)
            col.addWidget(lbl); col.addWidget(dp)
            dr.addLayout(col)
        lay.addLayout(dr)
        lay.addStretch()

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color:#EEEEEE;border:none;border-top:1px solid #EEEEEE;")
        lay.addWidget(sep2)

        # Buttons
        self.btn_generate = QPushButton("📄   Review & Generate Invoice PDF")
        self.btn_generate.setMinimumHeight(56)
        self.btn_generate.setStyleSheet(f"""
            QPushButton{{background:{GOLD};color:#1A1A2E;border-radius:10px;
                border:none;font-size:15px;font-weight:bold;}}
            QPushButton:hover{{background:#F5B041;}}""")
        self.btn_generate.clicked.connect(self._review_and_generate)
        lay.addWidget(self.btn_generate)

        self.btn_open = QPushButton("👁   Open Last PDF")
        self.btn_open.setMinimumHeight(44); self.btn_open.setEnabled(False)
        self.btn_open.setStyleSheet("""
            QPushButton{background:#2C3E50;color:white;border-radius:8px;
                border:none;font-size:13px;font-weight:bold;}
            QPushButton:hover{background:#3D5166;}
            QPushButton:disabled{background:#CCCCCC;color:#888;}""")
        self.btn_open.clicked.connect(self._open_pdf)
        lay.addWidget(self.btn_open)

        self.btn_email = QPushButton("📧   Send Invoice by Email")
        self.btn_email.setMinimumHeight(44); self.btn_email.setEnabled(False)
        self.btn_email.setStyleSheet("""
            QPushButton{background:#1B4F72;color:white;border-radius:8px;
                border:none;font-size:13px;font-weight:bold;}
            QPushButton:hover{background:#2980B9;}
            QPushButton:disabled{background:#CCCCCC;color:#888;}""")
        self.btn_email.clicked.connect(self._send_email)
        lay.addWidget(self.btn_email)
        return frame

    def _make_right_panel(self):
        frame = QFrame()
        frame.setStyleSheet("background:white;border-radius:14px;border:1px solid #DDDDDD;")
        lay = QVBoxLayout(frame); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(14)
        hdr = QLabel("📋  Invoice Preview")
        hdr.setStyleSheet(f"font-size:17px;font-weight:bold;color:{config.DARK};border:none;")
        lay.addWidget(hdr)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#EEEEEE;border:none;border-top:1px solid #EEEEEE;")
        lay.addWidget(sep)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#FAFAFA;}")
        self._pv_widget = QWidget(); self._pv_widget.setStyleSheet("background:#FAFAFA;")
        self._pv_lay = QVBoxLayout(self._pv_widget)
        self._pv_lay.setContentsMargins(12, 12, 12, 12); self._pv_lay.setSpacing(10)
        scroll.setWidget(self._pv_widget)
        lay.addWidget(scroll, 1)
        self._show_welcome()
        return frame

    # ── Preview helpers ───────────────────────────────────────
    def _clear_pv(self):
        while self._pv_lay.count():
            item = self._pv_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _show_welcome(self):
        self._clear_pv()
        l = QLabel("Select invoice type and person above,\n"
                   "then click  📄 Review & Generate Invoice PDF\n\n"
                   "A review screen will show every figure\n"
                   "so you can verify before saving or emailing.")
        l.setStyleSheet("font-size:13px;color:#AAAAAA;border:none;")
        l.setAlignment(Qt.AlignCenter)
        self._pv_lay.addStretch(); self._pv_lay.addWidget(l); self._pv_lay.addStretch()

    def _stat_card(self, label, value, color):
        f = QFrame()
        f.setStyleSheet(f"background:#FAFAFA;border-radius:8px;"
                        f"border-left:4px solid {color};"
                        f"border-top:1px solid #EEE;"
                        f"border-right:1px solid #EEE;"
                        f"border-bottom:1px solid #EEE;")
        vb = QVBoxLayout(f); vb.setContentsMargins(12,8,12,8); vb.setSpacing(2)
        lk = QLabel(label); lk.setStyleSheet(f"font-size:9px;font-weight:bold;color:{color};border:none;letter-spacing:1px;")
        lv = QLabel(value);  lv.setStyleSheet(f"font-size:17px;font-weight:bold;color:{config.DARK};border:none;")
        vb.addWidget(lk); vb.addWidget(lv)
        return f

    def _bal_widget(self, we_owe, they_owe):
        row = QHBoxLayout(); row.setSpacing(10)
        for active, amount, color, lbl, sub in [
            (we_owe>0,   we_owe,   "#C0392B", "WE OWE THEM",  "Still to pay them"),
            (they_owe>0, they_owe, "#1E8449", "THEY OWE US",  "Overpaid — they return"),
        ]:
            f = QFrame()
            f.setStyleSheet(f"background:{'#FEF0F0' if active and color=='#C0392B' else '#EAFAF1' if active else '#FAFAFA'};"
                            f"border-radius:8px;border:{'2px' if active else '1px'} solid "
                            f"{'#C0392B' if active and color=='#C0392B' else '#1E8449' if active else '#EEEEEE'};")
            vb = QVBoxLayout(f); vb.setContentsMargins(12,10,12,10); vb.setSpacing(2)
            lk = QLabel(lbl); lk.setStyleSheet(f"font-size:9px;font-weight:bold;color:{color if active else '#AAAAAA'};border:none;letter-spacing:1px;")
            lv = QLabel(f"PKR {amount:,.2f}"); lv.setStyleSheet(f"font-size:16px;font-weight:bold;color:{color if active else '#CCCCCC'};border:none;")
            ls = QLabel(sub); ls.setStyleSheet("font-size:9px;color:#888;border:none;")
            vb.addWidget(lk); vb.addWidget(lv); vb.addWidget(ls)
            row.addWidget(f)
        w = QWidget(); w.setLayout(row); w.setStyleSheet("background:transparent;border:none;")
        return w

    def _pv_header(self, title, subtitle, color):
        f = QFrame()
        f.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                        f"stop:0 {color},stop:1 {config.DARK});border-radius:10px;border:none;")
        vb = QVBoxLayout(f); vb.setContentsMargins(18,12,18,12); vb.setSpacing(3)
        t = QLabel(title); t.setStyleSheet("color:white;font-size:16px;font-weight:bold;border:none;")
        s = QLabel(subtitle); s.setStyleSheet("color:rgba(255,255,255,.7);font-size:11px;border:none;")
        vb.addWidget(t); vb.addWidget(s)
        return f

    # ── Data loading ──────────────────────────────────────────
    def _on_type_changed(self, idx):
        self.cmb_person.blockSignals(True)
        self.cmb_person.clear()
        try:
            conn = database.get_connection()
            if idx == 0:
                rows = conn.execute(
                    "SELECT DISTINCT reg_number, owner_name FROM dumprei_expenditure ORDER BY owner_name"
                ).fetchall()
                for r in rows:
                    self.cmb_person.addItem(f"{r['owner_name']}  ({r['reg_number']})",
                        userData={"reg": r["reg_number"], "owner": r["owner_name"]})
            elif idx == 1:
                self.cmb_person.addItem("Showal / Excavator Machine",
                    userData={"type": "excavator"})
            elif idx == 2:
                rows = conn.execute(
                    "SELECT * FROM truck_fleet WHERE truck_type='Dumper' ORDER BY owner_name"
                ).fetchall()
                for r in rows:
                    self.cmb_person.addItem(f"{r['owner_name']}  ({r['reg_number']})",
                        userData={"id": r["id"], "reg": r["reg_number"],
                                  "owner": r["owner_name"], "type": r["truck_type"]})
            elif idx == 3:
                rows = conn.execute(
                    "SELECT * FROM truck_fleet WHERE truck_type='Loader' ORDER BY owner_name"
                ).fetchall()
                for r in rows:
                    self.cmb_person.addItem(f"{r['owner_name']}  ({r['reg_number']})",
                        userData={"id": r["id"], "reg": r["reg_number"], "owner": r["owner_name"]})
            elif idx == 4:
                rows = conn.execute(
                    "SELECT DISTINCT COALESCE(NULLIF(vehicle_number,''), details) as veh "
                    "FROM royalty_payments ORDER BY veh"
                ).fetchall()
                for r in rows:
                    v = r["veh"] or "Unknown"
                    self.cmb_person.addItem(v, userData={"vehicle": v})
            elif idx == 5:
                try:
                    owners = database.land_get_owners()
                    for o in owners:
                        self.cmb_person.addItem(o, userData={"owner": o})
                except Exception:
                    pass
            conn.close()
        except Exception as e:
            pass
        self.cmb_person.blockSignals(False)
        self._refresh_preview()

    def _refresh_preview(self):
        idx = self.cmb_type.currentIndex()
        pd  = self.cmb_person.currentData()
        if not pd:
            self._show_welcome(); return
        d_from = self.date_from.date().toString("yyyy-MM-dd")
        d_to   = self.date_to.date().toString("yyyy-MM-dd")
        try:
            rd = self._build_review_data(idx, pd, d_from, d_to)
            self._show_preview(rd)
        except Exception as e:
            self._clear_pv()
            self._pv_lay.addWidget(QLabel(f"Preview error: {e}",
                styleSheet="color:red;font-size:11px;border:none;"))

    def _show_preview(self, rd):
        self._clear_pv()
        color = {"dumprei":"#CA6F1E","excavator":"#0E6655","dumper":"#1B4F72",
                 "loader":"#1E8449","royalty":"#6C3483","land":"#2C7873"}.get(rd["inv_type"], config.DARK)
        d_from = rd["date_from"]; d_to = rd["date_to"]
        n = rd["entry_count"]
        self._pv_lay.addWidget(self._pv_header(
            f"{rd['type_label']}  —  {rd['payee_name']}",
            f"{rd['payee_detail']}   |   {d_from} → {d_to}   |   {n} entr{'y' if n==1 else 'ies'}",
            color))

        grid = QGridLayout(); grid.setSpacing(10)
        fin  = rd.get("financials", {})
        items= list(fin.items())
        for i, (k, v) in enumerate(items):
            grid.addWidget(self._stat_card(k, str(v), color), i//2, i%2)
        w = QWidget(); w.setLayout(grid); w.setStyleSheet("background:transparent;border:none;")
        self._pv_lay.addWidget(w)
        self._pv_lay.addWidget(self._bal_widget(rd["we_still_owe"], rd["they_owe_us"]))

        info = QLabel(f"ℹ  Click  📄 Review & Generate  to see full breakdown before PDF")
        info.setStyleSheet("font-size:11px;color:#AAAAAA;border:none;font-style:italic;")
        info.setAlignment(Qt.AlignCenter)
        self._pv_lay.addWidget(info)
        self._pv_lay.addStretch()

    # ── Build review data ─────────────────────────────────────
    def _build_review_data(self, idx, pd, d_from, d_to):
        conn = database.get_connection()
        type_labels = ["dumprei","excavator","dumper","loader","royalty","land"]
        inv_type = type_labels[idx]

        if idx == 0:  # Dumprei
            rows = conn.execute(
                "SELECT * FROM dumprei_expenditure "
                "WHERE reg_number=? AND date>=? AND date<=? ORDER BY date ASC",
                (pd["reg"], d_from, d_to)).fetchall()
            conn.close()
            total_trips   = sum(int(r["total_trips"] or 0) for r in rows)
            total_cash    = sum(float(r["paid_cash"] or 0) for r in rows)
            total_diesel  = sum(float(r["paid_diesel_worth"] or 0) for r in rows)
            total_paid    = total_cash + total_diesel
            total_balance = sum(float(r["balance_due"] or 0) for r in rows)
            grand         = total_paid + max(total_balance, 0)
            we_owe  = max(total_balance,  0)
            they_owe= max(-total_balance, 0)
            line_items = [[str(i+1), r["date"],
                           str(int(r["total_trips"] or 0)),
                           f"PKR {float(r['paid_cash'] or 0):,.0f}",
                           f"PKR {float(r['paid_diesel_worth'] or 0):,.0f}",
                           f"PKR {float(r['balance_due'] or 0):,.0f}"]
                          for i, r in enumerate(rows)]
            headers = ["#","Date","Trips","Cash Paid","Diesel Paid","Balance Due"]
            fins = {"Total Trips": str(total_trips),
                    "Cash Paid":   f"PKR {total_cash:,.0f}",
                    "Diesel Paid": f"PKR {total_diesel:,.0f}",
                    "Total Paid":  f"PKR {total_paid:,.0f}",
                    "Balance Due": f"PKR {total_balance:,.0f}",
                    "Grand Total": f"PKR {grand:,.0f}"}
            payee_name   = pd["owner"]
            payee_detail = f"Vehicle: {pd['reg']}"

        elif idx == 1:  # Excavator
            rows = conn.execute(
                "SELECT * FROM excavator_expenditure "
                "WHERE date>=? AND date<=? ORDER BY date ASC",
                (d_from, d_to)).fetchall()
            conn.close()
            rk = rows[0].keys() if rows else []
            def sg(r, *ks, d=0.0):
                for k in ks:
                    if k in r.keys() and r[k] is not None: return float(r[k])
                return d
            total_hours   = sum(sg(r,"hours_worked")                  for r in rows)
            total_work    = sum(sg(r,"total_amount")                  for r in rows)
            total_ca      = sum(sg(r,"cash_advance", "paid_cash")     for r in rows)
            # User does not use diesel advance — only cash advance
            we_owe   = max(total_work - total_ca, 0)
            they_owe = max(total_ca - total_work, 0)
            net_bal  = total_work - total_ca
            line_items = [[str(i+1), r["date"],
                           f"{sg(r,'hours_worked'):.1f} hrs",
                           f"PKR {sg(r,'total_amount'):,.0f}",
                           f"PKR {sg(r,'cash_advance','paid_cash'):,.0f}",
                           f"PKR {sg(r,'total_amount') - sg(r,'cash_advance','paid_cash'):,.0f}"]
                          for i, r in enumerate(rows)]
            headers  = ["#", "Date", "Hours", "Work Total", "Cash Advance", "Balance"]
            fins = {"Total Hours":   f"{total_hours:.1f} hrs",
                    "Work Earned":   f"PKR {total_work:,.0f}",
                    "Cash Advance":  f"PKR {total_ca:,.0f}",
                    "Balance":       f"PKR {net_bal:,.0f}"}
            grand        = total_work
            payee_name   = "Excavator / Showal Machine"
            payee_detail = f"Period: {d_from} to {d_to}"

        elif idx == 2:  # Dumper
            rows = conn.execute(
                "SELECT * FROM truck_entries WHERE truck_id=? AND date>=? AND date<=? ORDER BY date ASC",
                (pd["id"], d_from, d_to)).fetchall()
            conn.close()
            def sg(r, *ks, d=0.0):
                for k in ks:
                    if k in r.keys() and r[k] is not None: return float(r[k])
                return d
            total_trips  = sum(int(sg(r,"trips"))    for r in rows)
            total_paid   = sum(sg(r,"payment")       for r in rows)
            total_bal    = sum(sg(r,"balance_due")   for r in rows)
            grand        = total_paid + max(total_bal, 0)
            we_owe  = max(total_bal,  0)
            they_owe= max(-total_bal, 0)
            line_items = [[str(i+1), r["date"],
                           str(int(sg(r,"trips"))),
                           f"PKR {sg(r,'paid_cash'):,.0f}",
                           f"PKR {sg(r,'paid_diesel'):,.0f}",
                           f"PKR {sg(r,'balance_due'):,.0f}"]
                          for i, r in enumerate(rows)]
            headers = ["#","Date","Trips","Cash Paid","Diesel Paid","Balance Due"]
            fins = {"Total Trips": str(total_trips),
                    "Total Paid":  f"PKR {total_paid:,.0f}",
                    "Balance Due": f"PKR {total_bal:,.0f}",
                    "Grand Total": f"PKR {grand:,.0f}"}
            payee_name   = pd["owner"]
            payee_detail = f"Vehicle: {pd['reg']}"

        elif idx == 3:  # Loader
            rows = conn.execute(
                "SELECT * FROM loader_entries WHERE truck_id=? AND date>=? AND date<=? ORDER BY date ASC",
                (pd["id"], d_from, d_to)).fetchall()
            conn.close()
            def sg(r, *ks, d=0.0):
                for k in ks:
                    if k in r.keys() and r[k] is not None: return float(r[k])
                return d
            def sstr(r, k, default=""):
                try: return str(r[k]) if r[k] else default
                except: return default
            total_days   = sum(sg(r,"days_worked")  for r in rows)
            total_cash   = sum(sg(r,"cash_paid")    for r in rows)
            total_diesel = sum(sg(r,"diesel_worth") for r in rows)
            grand        = total_cash + total_diesel
            we_owe       = grand
            they_owe     = 0.0
            line_items = []
            for i, r in enumerate(rows):
                etype = sstr(r, "entry_type", "Work")
                desc  = sstr(r, "description", "")
                label = f"{etype}" + (f" — {desc}" if desc else "")
                days  = sg(r,"days_worked")
                cash  = sg(r,"cash_paid")
                diesel= sg(r,"diesel_worth")
                line_items.append([
                    str(i+1), r["date"], label,
                    f"{days:.1f} days" if days else "—",
                    f"PKR {cash:,.0f}" if cash else "—",
                    f"PKR {diesel:,.0f}" if diesel else "—",
                ])
            headers = ["#", "Date", "Type / Description", "Days", "Cash Paid", "Diesel (PKR)"]
            fins = {"Days Worked":  f"{total_days:.1f} days",
                    "Cash Paid":    f"PKR {total_cash:,.0f}",
                    "Diesel Paid":  f"PKR {total_diesel:,.0f}",
                    "Grand Total":  f"PKR {grand:,.0f}"}
            # Fix "NIL" vehicle display
            reg_raw = pd.get("reg","") or ""
            reg_display = reg_raw.strip() if reg_raw.strip().upper() not in ("NIL","NONE","N/A","") else "Loader Vehicle"
            payee_name   = pd["owner"]
            payee_detail = f"Vehicle: {reg_display}"

        elif idx == 4:  # Royalty
            v = pd["vehicle"]
            rows = conn.execute(
                "SELECT * FROM royalty_payments "
                "WHERE (vehicle_number=? OR details=?) AND date>=? AND date<=? ORDER BY date ASC",
                (v, v, d_from, d_to)).fetchall()
            conn.close()
            def sg(r, *ks, d=0.0):
                for k in ks:
                    if k in r.keys() and r[k] is not None: return float(r[k])
                return d
            total_wt = sum(sg(r,"weight_tons") for r in rows)
            total_py = sum(sg(r,"amount")      for r in rows)
            grand    = total_py
            we_owe   = 0.0; they_owe = 0.0
            line_items = [[str(i+1), r["date"],
                           f"{sg(r,'weight_tons'):,.0f} kg",
                           f"PKR {sg(r,'amount'):,.0f}"]
                          for i, r in enumerate(rows)]
            headers = ["#","Date","Weight (kg)","Payment"]
            fins = {"Total Entries": str(len(rows)),
                    "Total Weight":  f"{total_wt:,.0f} kg",
                    "Total Payment": f"PKR {total_py:,.0f}"}
            payee_name   = "Government — Royalty Office"
            payee_detail = f"Vehicle: {v}"
        elif idx == 5:  # Land Rent
            conn.close()
            rows = database.land_get_range(d_from, d_to)
            rows = [r for r in rows if r["owner_name"] == pd.get("owner","")]
            def sg(r, k, d=0.0):
                try: return float(r[k]) if r[k] else d
                except: return d
            total_paid = sum(sg(r,"amount") for r in rows)
            cash_t  = sum(sg(r,"amount") for r in rows if (r["payment_mode"] or "")=="Cash")
            chq_t   = sum(sg(r,"amount") for r in rows if (r["payment_mode"] or "")!="Cash")
            line_items = []
            for i, r in enumerate(rows):
                mode = r["payment_mode"] or "Cash"
                chq  = ""
                if mode == "Cheque":
                    cn = r["cheque_number"] or ""; bn = r["bank_name"] or ""
                    chq = f"#{cn}" + (f" {bn}" if bn else "") if cn else bn
                line_items.append([
                    str(i+1), r["payment_date"] or "—",
                    f"{r['rent_from']} → {r['rent_to']}",
                    r["land_desc"] or "—",
                    mode + (f"  {chq}" if chq else ""),
                    f"PKR {sg(r,'amount'):,.0f}",
                ])
            headers = ["#", "Payment Date", "Rent Period", "Location", "Mode", "Amount"]
            fins = {"Total Payments": str(len(rows)),
                    "Cash Total":     f"PKR {cash_t:,.0f}",
                    "Cheque Total":   f"PKR {chq_t:,.0f}",
                    "Grand Total":    f"PKR {total_paid:,.0f}"}
            grand    = total_paid
            we_owe   = 0.0; they_owe = 0.0
            payee_name   = pd.get("owner","Land Owner")
            payee_detail = f"Surface / Land Rent  |  {d_from} to {d_to}"
        else:
            conn.close()
            return {}

        type_label = self.cmb_type.currentText()
        return {
            "inv_type":    inv_type,
            "type_label":  type_label,
            "payee_name":  payee_name,
            "payee_detail":payee_detail,
            "date_from":   d_from,
            "date_to":     d_to,
            "entry_count": len(rows),
            "line_items":  line_items,
            "headers":     headers,
            "financials":  fins,
            "grand_total": grand,
            "we_still_owe":we_owe,
            "they_owe_us": they_owe,
            "pd":          pd,
        }

    # ── Review & Generate ─────────────────────────────────────
    def _review_and_generate(self):
        idx = self.cmb_type.currentIndex()
        pd  = self.cmb_person.currentData()
        if not pd:
            QMessageBox.warning(self, "No Selection", "Please select a person/vehicle."); return
        d_from = self.date_from.date().toString("yyyy-MM-dd")
        d_to   = self.date_to.date().toString("yyyy-MM-dd")
        if d_from > d_to:
            QMessageBox.warning(self, "Invalid Dates", "From date must be before To date."); return

        try:
            rd = self._build_review_data(idx, pd, d_from, d_to)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load data:\n{e}"); return

        if rd["entry_count"] == 0:
            QMessageBox.information(self, "No Entries",
                "No entries found for this person in the selected date range."); return

        from ui.invoice_review import InvoiceReviewDialog
        dlg = InvoiceReviewDialog(rd, parent=self)
        dlg.exec_()
        if not dlg.confirmed:
            return  # user cancelled — go back and correct

        notes = dlg.notes
        self._generate(idx, pd, d_from, d_to, notes)

    def _generate(self, idx, pd, d_from, d_to, notes=""):
        prog = QProgressDialog("Generating Invoice PDF...", None, 0, 0, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setWindowTitle("Please Wait")
        prog.show(); QApplication.processEvents()
        try:
            from reports.invoice_generator import (
                generate_dumprei_invoice, generate_excavator_invoice,
                generate_truck_invoice, generate_loader_invoice,
                generate_royalty_invoice)
            out_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

            if   idx == 0:
                path = generate_dumprei_invoice(
                    pd["reg"], pd["owner"], d_from, d_to, out_dir, notes)
            elif idx == 1:
                path = generate_excavator_invoice(None, d_from, d_to, out_dir, notes)
            elif idx == 2:
                path = generate_truck_invoice(
                    pd["id"], pd["reg"], pd["owner"], pd["type"], d_from, d_to, out_dir, notes)
            elif idx == 3:
                path = generate_loader_invoice(
                    pd["id"], pd["reg"], pd["owner"], d_from, d_to, out_dir, notes)
            elif idx == 4:
                path = generate_royalty_invoice(pd["vehicle"], d_from, d_to, out_dir, notes)
            elif idx == 5:
                from reports.invoice_generator import generate_land_rent_invoice
                path = generate_land_rent_invoice(pd["owner"], d_from, d_to, out_dir, notes)

            prog.close()
            self._last_pdf_path = path
            self.btn_open.setEnabled(True)
            self.btn_email.setEnabled(True)
            QMessageBox.information(self, "Invoice Ready",
                f"✅ Invoice PDF generated!\n\n{os.path.basename(path)}\n\n"
                "Click 'Open Last PDF' to view it.")
        except Exception as e:
            prog.close()
            QMessageBox.critical(self, "Error", f"Could not generate invoice:\n{e}")

    def _open_pdf(self):
        if self._last_pdf_path and os.path.exists(self._last_pdf_path):
            if os.name == "nt": os.startfile(self._last_pdf_path)
            else: subprocess.Popen(["xdg-open", self._last_pdf_path])
        else:
            QMessageBox.warning(self, "Not Found", "PDF file not found.")

    def _send_email(self):
        if not self._last_pdf_path or not os.path.exists(self._last_pdf_path):
            QMessageBox.warning(self, "No PDF", "Generate an invoice first."); return
        try:
            from reports.email_sender import send_invoice_email
            send_invoice_email(self._last_pdf_path, parent=self)
        except Exception as e:
            QMessageBox.critical(self, "Email Error", f"Could not send email:\n{e}")

    def _go_back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()

    def closeEvent(self, event):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(event)