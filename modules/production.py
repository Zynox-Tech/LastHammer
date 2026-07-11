"""
CH 10 — Production Tracker
Reads weight data directly from royalty_payments (CH2) — that is where
vehicle weights are recorded. Also shows daily totals, vehicle breakdown,
and calculates cost-per-kg automatically.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDateEdit, QComboBox, QSplitter,
    QGridLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
import database, config
from datetime import date as dt_date, timedelta

COLOR  = "#8E44AD"
DARK   = config.DARK
GOLD   = "#F39C12"
GREEN  = "#1E8449"
RED    = "#C0392B"
BLUE   = "#1B4F72"
TEAL   = "#0E6655"


class ProductionModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 10 — Production Tracker")
        self.setMinimumSize(1380, 820)
        self._build_ui()
        self._load()

    # ── UI BUILD ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._kpi_bar())
        root.addWidget(self._filter_bar())
        root.addWidget(self._body(), 1)

    def _topbar(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {COLOR};")
        f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28, 0, 28, 0)
        bar = QFrame(); bar.setFixedSize(6, 44)
        bar.setStyleSheet(f"background:{COLOR};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        vb.addWidget(QLabel("Chapter 10 — Production Tracker",
            styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel(
            "Live weight data from Royalty (CH2) — vehicle weights, daily totals, cost per kg",
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
        f.setFixedHeight(96)
        lay = QHBoxLayout(f); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self._kpi = {}
        specs = [
            ("today_kg",    "TODAY'S WEIGHT",       GOLD),
            ("month_kg",    "THIS MONTH",           COLOR),
            ("total_kg",    "ALL TIME TOTAL",        BLUE),
            ("vehicles",    "VEHICLES TRACKED",     TEAL),
            ("cost_per_kg", "COST PER KG",           RED),
            ("total_exp",   "TOTAL EXPENDITURE",     GREEN),
        ]
        for key, title, color in specs:
            sep = QFrame()
            sep.setStyleSheet("background:#2A2A4A;border:none;"); sep.setFixedWidth(1)
            card = QFrame()
            card.setStyleSheet("background:transparent;border:none;")
            vb = QVBoxLayout(card); vb.setContentsMargins(22, 10, 22, 10); vb.setSpacing(3)
            lk = QLabel(title)
            lk.setStyleSheet(f"font-size:9px;font-weight:bold;color:{color};"
                             "border:none;letter-spacing:1px;")
            lv = QLabel("—")
            lv.setStyleSheet("font-size:22px;font-weight:bold;color:white;border:none;")
            vb.addWidget(lk); vb.addWidget(lv)
            self._kpi[key] = lv
            lay.addWidget(sep); lay.addWidget(card, 1)
        return f

    def _filter_bar(self):
        f = QFrame()
        f.setStyleSheet("background:#F0F0F0;border-bottom:1px solid #D5D5D5;")
        f.setFixedHeight(56)
        lay = QHBoxLayout(f); lay.setContentsMargins(24, 0, 24, 0); lay.setSpacing(12)
        lay.addWidget(self._lbl("📅  Period:", bold=True))
        self.cmb_period = QComboBox(); self.cmb_period.setFixedHeight(38)
        self.cmb_period.addItems([
            "Today", "Yesterday", "This Week",
            "This Month", "Last Month", "Last 3 Months", "All Time"
        ])
        self.cmb_period.setCurrentIndex(3)
        self.cmb_period.setStyleSheet(
            "font-size:13px;font-weight:bold;padding:4px 12px;"
            "border:2px solid #CCCCCC;border-radius:7px;background:white;")
        self.cmb_period.currentIndexChanged.connect(self._load)
        lay.addWidget(self.cmb_period)
        lay.addSpacing(20)
        lay.addWidget(self._lbl("Filter by vehicle:", bold=True))
        self.cmb_vehicle = QComboBox(); self.cmb_vehicle.setFixedHeight(38)
        self.cmb_vehicle.setMinimumWidth(200)
        self.cmb_vehicle.setStyleSheet(
            "font-size:13px;padding:4px 12px;border:2px solid #CCCCCC;"
            "border-radius:7px;background:white;")
        self.cmb_vehicle.currentIndexChanged.connect(self._apply_vehicle_filter)
        lay.addWidget(self.cmb_vehicle)
        lay.addStretch()
        self.lbl_period = QLabel("")
        self.lbl_period.setStyleSheet(
            f"font-size:12px;font-weight:bold;color:{COLOR};border:none;")
        lay.addWidget(self.lbl_period)
        return f

    def _body(self):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            "QSplitter{background:#EFEFEF;}"
            "QSplitter::handle{background:#DDDDDD;width:2px;}")
        splitter.addWidget(self._left_panel())
        splitter.addWidget(self._right_panel())
        splitter.setSizes([820, 420])
        return splitter

    def _left_panel(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        hdr = QFrame(); hdr.setStyleSheet(
            f"background:white;border-bottom:2px solid {COLOR};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(self._lbl("⛏  DAILY PRODUCTION LOG  (from Royalty / CH2)", bold=True))
        hl.addStretch()
        self.lbl_rows = QLabel(""); self.lbl_rows.setStyleSheet(
            "font-size:12px;color:#AAAAAA;border:none;")
        hl.addWidget(self.lbl_rows)
        lay.addWidget(hdr)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "#", "Date", "Vehicle / Reg No.", "Weight (kg)", "Royalty Paid", "Notes / Details"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self.table.setColumnWidth(0, 40)
        hh.setSectionResizeMode(1, QHeaderView.Fixed); self.table.setColumnWidth(1, 100)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Fixed); self.table.setColumnWidth(3, 110)
        hh.setSectionResizeMode(4, QHeaderView.Fixed); self.table.setColumnWidth(4, 110)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)
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
            QTableWidget::item { padding:4px 6px; }
            QTableWidget::item:alternate { background:#F7F5FF; }
            QTableWidget::item:selected { background:#8E44AD; color:white; }
        """)
        lay.addWidget(self.table, 1)
        # Footer total bar
        foot = QFrame()
        foot.setStyleSheet(f"background:{DARK};border-top:2px solid {COLOR};")
        foot.setFixedHeight(44)
        fl = QHBoxLayout(foot); fl.setContentsMargins(16, 0, 16, 0)
        self.lbl_total_kg = QLabel("Total: 0 kg")
        self.lbl_total_kg.setStyleSheet(
            f"color:{COLOR};font-size:14px;font-weight:bold;border:none;")
        fl.addWidget(self.lbl_total_kg)
        lay.addWidget(foot)
        return w

    def _right_panel(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        hdr = QFrame(); hdr.setStyleSheet(
            f"background:white;border-bottom:2px solid {TEAL};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(self._lbl("🚛  PER VEHICLE BREAKDOWN", bold=True))
        lay.addWidget(hdr)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#FAFAFA;}")
        self._veh_widget = QWidget()
        self._veh_widget.setStyleSheet("background:#FAFAFA;")
        self._veh_lay = QVBoxLayout(self._veh_widget)
        self._veh_lay.setContentsMargins(12, 12, 12, 12); self._veh_lay.setSpacing(8)
        scroll.setWidget(self._veh_widget)
        lay.addWidget(scroll, 1)
        return w

    # ── DATA LOADING ──────────────────────────────────────────────────────────
    def _date_range(self):
        today = dt_date.today()
        idx   = self.cmb_period.currentIndex()
        if idx == 0:   return today.isoformat(), today.isoformat()
        if idx == 1:   d = today - timedelta(days=1); return d.isoformat(), d.isoformat()
        if idx == 2:   return (today - timedelta(days=today.weekday())).isoformat(), today.isoformat()
        if idx == 3:   return today.replace(day=1).isoformat(), today.isoformat()
        if idx == 4:
            first = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last  = today.replace(day=1) - timedelta(days=1)
            return first.isoformat(), last.isoformat()
        if idx == 5:   return (today - timedelta(days=90)).isoformat(), today.isoformat()
        return "2000-01-01", today.isoformat()

    def _load(self):
        d_from, d_to = self._date_range()
        self.lbl_period.setText(f"{d_from}  →  {d_to}")

        # Pull from royalty_payments — weight_tons column is kg in this system
        try:
            conn = database.get_connection()
            rows = conn.execute(
                "SELECT id, date, "
                "COALESCE(NULLIF(TRIM(vehicle_number),''), details, '?') AS vehicle, "
                "COALESCE(weight_tons, 0) AS kg, "
                "COALESCE(amount, 0) AS paid, "
                "details "
                "FROM royalty_payments "
                "WHERE date >= ? AND date <= ? "
                "ORDER BY date DESC, id DESC",
                (d_from, d_to)
            ).fetchall()

            # Vehicle totals for filter + right panel
            veh_data = conn.execute(
                "SELECT "
                "COALESCE(NULLIF(TRIM(vehicle_number),''), details, '?') AS vehicle, "
                "SUM(COALESCE(weight_tons,0)) AS total_kg, "
                "SUM(COALESCE(amount,0)) AS total_paid, "
                "COUNT(*) AS trips "
                "FROM royalty_payments "
                "WHERE date >= ? AND date <= ? "
                "GROUP BY vehicle ORDER BY total_kg DESC",
                (d_from, d_to)
            ).fetchall()

            # Total expenditure across all chapters for cost-per-kg
            total_exp = self._total_expenditure(conn)
            conn.close()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "DB Error", str(e))
            return

        self._all_rows = rows
        self._veh_data = veh_data

        # Populate vehicle filter combo
        cur_veh = self.cmb_vehicle.currentText()
        self.cmb_vehicle.blockSignals(True)
        self.cmb_vehicle.clear()
        self.cmb_vehicle.addItem("All Vehicles")
        for vd in veh_data:
            self.cmb_vehicle.addItem(str(vd["vehicle"]))
        idx = self.cmb_vehicle.findText(cur_veh)
        self.cmb_vehicle.setCurrentIndex(max(idx, 0))
        self.cmb_vehicle.blockSignals(False)

        self._render_table(rows)
        self._render_vehicle_cards(veh_data, total_exp)

        # KPIs
        total_kg   = sum(float(r["kg"] or 0) for r in rows)
        n_vehicles = len(set(str(r["vehicle"]) for r in rows))
        today_str  = dt_date.today().isoformat()
        today_kg   = sum(float(r["kg"] or 0) for r in rows if r["date"] == today_str)
        month_str  = dt_date.today().replace(day=1).isoformat()
        month_kg   = sum(float(r["kg"] or 0) for r in self._get_all_rows()
                         if r["date"] >= month_str)
        cpt = (total_exp / total_kg) if total_kg > 0 else 0
        self._kpi["today_kg"].setText(f"{today_kg:,.0f} kg")
        self._kpi["month_kg"].setText(f"{month_kg:,.0f} kg")
        self._kpi["total_kg"].setText(f"{total_kg:,.0f} kg")
        self._kpi["vehicles"].setText(str(n_vehicles))
        self._kpi["cost_per_kg"].setText(f"PKR {cpt:,.2f}" if cpt else "—")
        self._kpi["total_exp"].setText(f"PKR {total_exp:,.0f}")

    def _get_all_rows(self):
        try:
            conn = database.get_connection()
            rows = conn.execute(
                "SELECT date, COALESCE(weight_tons,0) AS kg FROM royalty_payments"
            ).fetchall()
            conn.close(); return rows
        except: return []

    def _total_expenditure(self, conn):
        total = 0
        for tbl, col in [
            ("general_expenditures",  "amount"),
            ("excavator_expenditure", "total_amount"),
            ("dumprei_expenditure",   "payment_received"),
            ("truck_entries",         "payment"),
        ]:
            try:
                v = conn.execute(
                    f"SELECT COALESCE(SUM({col}),0) FROM {tbl}"
                ).fetchone()[0]
                total += float(v or 0)
            except: pass
        return total

    def _apply_vehicle_filter(self):
        veh = self.cmb_vehicle.currentText()
        if veh == "All Vehicles":
            self._render_table(self._all_rows)
        else:
            filtered = [r for r in self._all_rows if str(r["vehicle"]) == veh]
            self._render_table(filtered)

    def _render_table(self, rows):
        self.table.setRowCount(len(rows))
        total_kg = 0
        for i, r in enumerate(rows):
            kg   = float(r["kg"] or 0)
            paid = float(r["paid"] or 0)
            total_kg += kg
            # color code weight: high=green, low=orange, zero=red
            kg_color = GREEN if kg >= 10000 else GOLD if kg >= 1000 else RED

            vals = [
                str(i + 1),
                r["date"],
                str(r["vehicle"]),
                f"{kg:,.0f} kg",
                f"PKR {paid:,.0f}" if paid else "—",
                str(r["details"] or "—"),
            ]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if j == 3:  # weight column — colored
                    item.setForeground(QColor(kg_color))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                elif j == 2:  # vehicle
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(i, j, item)

        self.lbl_total_kg.setText(
            f"Total weight in period:  {total_kg:,.0f} kg  "
            f"({total_kg/1000:.1f} tonnes)  |  {len(rows)} records")
        self.lbl_rows.setText(f"{len(rows)} entries")

    def _render_vehicle_cards(self, veh_data, total_exp):
        # Clear
        while self._veh_lay.count():
            item = self._veh_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not veh_data:
            no = QLabel("No royalty data in this period")
            no.setStyleSheet("font-size:13px;color:#AAAAAA;border:none;")
            no.setAlignment(Qt.AlignCenter)
            self._veh_lay.addWidget(no)
            self._veh_lay.addStretch()
            return

        total_kg_all = sum(float(v["total_kg"] or 0) for v in veh_data)

        for vd in veh_data:
            veh   = str(vd["vehicle"])
            kg    = float(vd["total_kg"] or 0)
            paid  = float(vd["total_paid"] or 0)
            trips = int(vd["trips"] or 0)
            share = (kg / total_kg_all * 100) if total_kg_all > 0 else 0
            cpk   = (paid / kg) if kg > 0 else 0

            card = QFrame()
            card.setStyleSheet(
                f"background:white;border-radius:10px;"
                f"border-left:4px solid {COLOR};"
                f"border-top:1px solid #EEEEEE;"
                f"border-right:1px solid #EEEEEE;"
                f"border-bottom:1px solid #EEEEEE;")
            vb = QVBoxLayout(card)
            vb.setContentsMargins(14, 10, 14, 10); vb.setSpacing(6)

            # Title row
            title_row = QHBoxLayout()
            lv = QLabel(veh)
            lv.setStyleSheet(
                f"font-size:14px;font-weight:bold;color:{DARK};border:none;")
            lt = QLabel(f"{trips} trips")
            lt.setStyleSheet(
                f"font-size:11px;color:{COLOR};font-weight:bold;border:none;")
            title_row.addWidget(lv); title_row.addStretch(); title_row.addWidget(lt)
            vb.addLayout(title_row)

            # Progress bar showing share of total weight
            bar_bg = QFrame()
            bar_bg.setFixedHeight(8)
            bar_bg.setStyleSheet("background:#EEE;border-radius:4px;border:none;")
            bar_inner = QFrame(bar_bg)
            bar_inner.setFixedHeight(8)
            bar_inner.move(0, 0)
            bar_w = max(int(share * 2.2), 4)  # max ~220px
            bar_inner.setFixedWidth(bar_w)
            bar_inner.setStyleSheet(
                f"background:{COLOR};border-radius:4px;border:none;")
            vb.addWidget(bar_bg)

            # Stats row
            stats = QHBoxLayout(); stats.setSpacing(0)
            for label, value, color in [
                ("WEIGHT",    f"{kg:,.0f} kg",       COLOR),
                ("ROYALTY",   f"PKR {paid:,.0f}",     TEAL),
                ("SHARE",     f"{share:.1f}%",         GOLD),
                ("COST/KG",   f"PKR {cpk:.2f}" if cpk else "—", RED),
            ]:
                stat_w = QWidget()
                stat_w.setStyleSheet("background:transparent;border:none;")
                sv = QVBoxLayout(stat_w)
                sv.setContentsMargins(0, 0, 12, 0); sv.setSpacing(1)
                sl = QLabel(label)
                sl.setStyleSheet(
                    f"font-size:8px;font-weight:bold;color:{color};"
                    "border:none;letter-spacing:1px;")
                sv2 = QLabel(value)
                sv2.setStyleSheet(
                    f"font-size:12px;font-weight:bold;color:{DARK};border:none;")
                sv.addWidget(sl); sv.addWidget(sv2)
                stats.addWidget(stat_w)
            stats.addStretch()
            vb.addLayout(stats)
            self._veh_lay.addWidget(card)

        self._veh_lay.addStretch()

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _lbl(self, text, bold=False):
        l = QLabel(text)
        l.setStyleSheet(
            f"font-size:{'13' if bold else '12'}px;"
            f"{'font-weight:bold;' if bold else ''}"
            f"color:{DARK};border:none;")
        return l

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()

    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)