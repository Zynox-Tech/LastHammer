"""CH 14 — Business Intelligence Dashboard"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QGridLayout,
    QDateEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from datetime import date as dt_date, timedelta
import database, config

COLOR = "#F39C12"
DARK  = config.DARK
RED   = "#C0392B"
GREEN = "#1E8449"
BLUE  = "#1B4F72"
PURPLE= "#6C3483"
TEAL  = "#0E6655"
ORANGE= "#CA6F1E"


class BIModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 14 — Business Intelligence")
        self.setMinimumSize(1380, 860)
        self._build_ui()
        self._load()

    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._filter_bar())
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#EFEFEF;}")
        self._scroll_widget = QWidget(); self._scroll_widget.setStyleSheet("background:#EFEFEF;")
        self._scroll_lay = QVBoxLayout(self._scroll_widget)
        self._scroll_lay.setContentsMargins(28,20,28,20); self._scroll_lay.setSpacing(20)
        scroll.setWidget(self._scroll_widget)
        root.addWidget(scroll, 1)

    def _topbar(self):
        f = QFrame(); f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {COLOR};"); f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28,0,28,0)
        bar = QFrame(); bar.setFixedSize(6,40); bar.setStyleSheet(f"background:{COLOR};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(12)
        vb = QVBoxLayout(); vb.setSpacing(1)
        vb.addWidget(QLabel("Chapter 14 — Business Intelligence", styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel("P&L summary, cost per ton, vehicle performance, monthly trends", styleSheet="color:#AAAAAA;font-size:12px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Dashboard"); btn.setFixedHeight(40); btn.setMinimumWidth(160)
        btn.setStyleSheet("QPushButton{background:#2C2C4E;color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}QPushButton:hover{background:#3D3D6E;}")
        btn.clicked.connect(self._back); lay.addWidget(btn)
        return f

    def _filter_bar(self):
        f = QFrame(); f.setStyleSheet("background:#E8E8E8;border-bottom:1px solid #CCCCCC;"); f.setFixedHeight(60)
        lay = QHBoxLayout(f); lay.setContentsMargins(28,0,28,0); lay.setSpacing(14)
        lbl = QLabel("📅  Period:"); lbl.setStyleSheet("font-weight:bold;font-size:13px;border:none;")
        lay.addWidget(lbl)
        self.cmb_period = QComboBox(); self.cmb_period.setFixedHeight(40)
        self.cmb_period.addItems(["This Month","Last Month","Last 3 Months","Last 6 Months","This Year","All Time"])
        self.cmb_period.setStyleSheet("font-size:13px;padding:4px 12px;border:1px solid #CCCCCC;border-radius:7px;background:white;")
        self.cmb_period.currentIndexChanged.connect(self._load)
        lay.addWidget(self.cmb_period)
        lay.addStretch()
        btn = QPushButton("↻  Refresh"); btn.setFixedHeight(40); btn.setMinimumWidth(120)
        btn.setStyleSheet(f"QPushButton{{background:{COLOR};color:#1A1A2E;border-radius:7px;border:none;font-size:13px;font-weight:bold;}}QPushButton:hover{{background:#F5B041;}}")
        btn.clicked.connect(self._load); lay.addWidget(btn)
        return f

    def _date_range(self):
        today = dt_date.today()
        idx = self.cmb_period.currentIndex()
        if idx == 0:   # This month
            return today.replace(day=1).isoformat(), today.isoformat()
        elif idx == 1: # Last month
            first = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last  = today.replace(day=1) - timedelta(days=1)
            return first.isoformat(), last.isoformat()
        elif idx == 2: return (today - timedelta(days=90)).isoformat(), today.isoformat()
        elif idx == 3: return (today - timedelta(days=180)).isoformat(), today.isoformat()
        elif idx == 4: return today.replace(month=1,day=1).isoformat(), today.isoformat()
        else:          return "2000-01-01", today.isoformat()

    def _load(self):
        # Clear layout
        while self._scroll_lay.count():
            item = self._scroll_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        d_from, d_to = self._date_range()
        period_lbl = f"{d_from}  to  {d_to}"

        try:
            conn = database.get_connection()
            # Expenditure per chapter
            t1 = conn.execute("SELECT COALESCE(SUM(amount),0) FROM general_expenditures WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            t2 = conn.execute("SELECT COALESCE(SUM(amount),0) FROM royalty_payments WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            t3 = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM excavator_expenditure WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            t4 = conn.execute("SELECT COALESCE(SUM(payment_received),0) FROM dumprei_expenditure WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            t5_truck = conn.execute("SELECT COALESCE(SUM(payment),0) FROM truck_entries WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            t5_loader= conn.execute("SELECT COALESCE(SUM(cash_paid+diesel_worth),0) FROM loader_entries WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            t5 = t5_truck + t5_loader
            # Production
            tons = conn.execute("SELECT COALESCE(SUM(tons_extracted),0) FROM production WHERE date>=? AND date<=?", (d_from,d_to)).fetchone()[0] or 0
            # Advances outstanding
            adv_out = conn.execute("SELECT COALESCE(SUM(amount-repaid),0) FROM advances WHERE status='Pending'").fetchone()[0] or 0
            # Vehicle performance — dumprei
            dumprei_perf = conn.execute(
                "SELECT reg_number, owner_name, "
                "SUM(total_trips) as trips, "
                "SUM(payment_received) as paid "
                "FROM dumprei_expenditure WHERE date>=? AND date<=? "
                "GROUP BY reg_number ORDER BY paid DESC LIMIT 10", (d_from,d_to)).fetchall()
            # Monthly breakdown
            monthly = conn.execute(
                "SELECT substr(date,1,7) as month, "
                "SUM(amount) as gen, 0 as exc FROM general_expenditures "
                "WHERE date>=? AND date<=? GROUP BY month ORDER BY month", (d_from,d_to)).fetchall()
            conn.close()
        except Exception as e:
            conn.close() if conn else None
            self._scroll_lay.addWidget(QLabel(f"Error loading data: {e}", styleSheet="color:red;font-size:13px;"))
            return

        grand = t1 + t2 + t3 + t4 + t5
        cpt   = (grand / tons) if tons > 0 else 0

        # ── KPI Cards row ──
        self._scroll_lay.addWidget(self._section_lbl(f"📊  KEY PERFORMANCE INDICATORS  ({period_lbl})"))
        kpi_grid = QGridLayout(); kpi_grid.setSpacing(14)
        kpis = [
            ("GRAND TOTAL EXPENDITURE", f"PKR {grand:,.0f}", RED,    "Total spent across all chapters"),
            ("TOTAL TONS EXTRACTED",    f"{tons:,.1f} tons",  PURPLE, "From production tracker"),
            ("COST PER TON",            f"PKR {cpt:,.0f}",    RED if cpt>5000 else GREEN, "Grand total ÷ tons extracted"),
            ("CH1 GENERAL",             f"PKR {t1:,.0f}",    RED,    "General expenditures"),
            ("CH2 ROYALTY",             f"PKR {t2:,.0f}",    PURPLE, "Government royalty"),
            ("CH3 EXCAVATOR",           f"PKR {t3:,.0f}",    TEAL,   "Excavator work"),
            ("CH4 DUMPREI",             f"PKR {t4:,.0f}",    ORANGE, "Dumprei / tipper"),
            ("CH5 FLEET",               f"PKR {t5:,.0f}",    BLUE,   "Truck + loader fleet"),
            ("ADVANCES OUTSTANDING",    f"PKR {adv_out:,.0f}",RED if adv_out>0 else GREEN,"Pending repayments"),
        ]
        for i, (title, value, color, sub) in enumerate(kpis):
            kpi_grid.addWidget(self._kpi_card(title, value, color, sub), i//3, i%3)
        w = QWidget(); w.setLayout(kpi_grid); w.setStyleSheet("background:transparent;")
        self._scroll_lay.addWidget(w)

        # ── Chapter breakdown bar ──
        self._scroll_lay.addWidget(self._section_lbl("💰  EXPENDITURE BY CHAPTER"))
        self._scroll_lay.addWidget(self._chapter_breakdown(t1,t2,t3,t4,t5,grand))

        # ── Vehicle performance table ──
        if dumprei_perf:
            self._scroll_lay.addWidget(self._section_lbl("🚛  DUMPREI VEHICLE PERFORMANCE"))
            self._scroll_lay.addWidget(self._vehicle_table(dumprei_perf))

        # ── Cost per ton insight ──
        self._scroll_lay.addWidget(self._section_lbl("⚖  COST ANALYSIS"))
        self._scroll_lay.addWidget(self._cost_analysis(grand, tons, cpt, t3, t4, t5))

        self._scroll_lay.addStretch()

    def _section_lbl(self, t):
        l = QLabel(t)
        l.setStyleSheet("font-size:11px;font-weight:bold;color:#888888;letter-spacing:1px;background:transparent;border:none;")
        return l

    def _kpi_card(self, title, value, color, sub):
        f = QFrame()
        f.setStyleSheet(f"background:white;border-radius:12px;"
                        f"border-left:5px solid {color};"
                        f"border-top:1px solid #EEEEEE;"
                        f"border-right:1px solid #EEEEEE;"
                        f"border-bottom:1px solid #EEEEEE;")
        lay = QVBoxLayout(f); lay.setContentsMargins(16,12,16,12); lay.setSpacing(4)
        lt = QLabel(title); lt.setStyleSheet(f"font-size:10px;font-weight:bold;color:{color};border:none;letter-spacing:1px;")
        lv = QLabel(value); lv.setStyleSheet(f"font-size:20px;font-weight:bold;color:{DARK};border:none;")
        ls = QLabel(sub);   ls.setStyleSheet("font-size:10px;color:#AAAAAA;border:none;")
        lay.addWidget(lt); lay.addWidget(lv); lay.addWidget(ls)
        return f

    def _chapter_breakdown(self, t1,t2,t3,t4,t5,grand):
        f = QFrame(); f.setStyleSheet("background:white;border-radius:12px;border:1px solid #EEEEEE;")
        lay = QVBoxLayout(f); lay.setContentsMargins(20,16,20,16); lay.setSpacing(10)
        items = [("CH1 General",  t1, RED),   ("CH2 Royalty", t2, PURPLE),
                 ("CH3 Excavator",t3, TEAL),   ("CH4 Dumprei", t4, ORANGE),
                 ("CH5 Fleet",    t5, BLUE)]
        for name, val, color in items:
            row = QHBoxLayout(); row.setSpacing(10)
            lbl = QLabel(name); lbl.setFixedWidth(140)
            lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{DARK};border:none;")
            # Progress bar (fake using QFrame width ratio)
            pct = (val / grand * 100) if grand > 0 else 0
            bar_bg = QFrame(); bar_bg.setFixedHeight(22)
            bar_bg.setStyleSheet("background:#F0F0F0;border-radius:4px;border:none;")
            bar_inner = QFrame(bar_bg); bar_inner.setFixedHeight(22)
            bar_inner.move(0,0)
            bar_inner.setStyleSheet(f"background:{color};border-radius:4px;border:none;")
            bar_inner.setFixedWidth(max(int(pct*5),4))
            amt = QLabel(f"PKR {val:,.0f}  ({pct:.1f}%)"); amt.setFixedWidth(200)
            amt.setStyleSheet(f"font-size:12px;color:{color};font-weight:bold;border:none;")
            amt.setAlignment(Qt.AlignRight)
            row.addWidget(lbl); row.addWidget(bar_bg,1); row.addWidget(amt)
            lay.addLayout(row)
        return f

    def _vehicle_table(self, rows):
        f = QFrame(); f.setStyleSheet("background:white;border-radius:12px;border:1px solid #EEEEEE;")
        lay = QVBoxLayout(f); lay.setContentsMargins(0,0,0,0)
        tbl = QTableWidget(); tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels(["Rank","Reg Number","Owner","Total Trips","Total Paid"])
        tbl.setRowCount(len(rows))
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setStyleSheet("""
            QTableWidget{border:none;font-size:13px;}
            QHeaderView::section{background:#1A1A2E;color:white;font-weight:bold;padding:8px;border:none;}
            QTableWidget::item:selected{background:#F39C12;color:#1A1A2E;}
        """)
        for i, r in enumerate(rows):
            vals = [f"#{i+1}", r["reg_number"], r["owner_name"],
                    str(int(r["trips"] or 0)), f"PKR {float(r['paid'] or 0):,.0f}"]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v); item.setTextAlignment(Qt.AlignCenter)
                if i == 0: item.setForeground(QColor(ORANGE)); item.setFont(QFont("Arial",10,QFont.Bold))
                tbl.setItem(i, j, item)
        tbl.setFixedHeight(40 + len(rows)*36)
        lay.addWidget(tbl)
        return f

    def _cost_analysis(self, grand, tons, cpt, t3, t4, t5):
        f = QFrame(); f.setStyleSheet("background:white;border-radius:12px;border:1px solid #EEEEEE;")
        lay = QGridLayout(f); lay.setContentsMargins(20,16,20,16); lay.setSpacing(16)

        def insight(title, value, note, color):
            card = QFrame()
            card.setStyleSheet(f"background:#FAFAFA;border-radius:8px;border:1px solid {color}40;border-left:3px solid {color};")
            vb = QVBoxLayout(card); vb.setContentsMargins(12,10,12,10); vb.setSpacing(3)
            vb.addWidget(QLabel(title, styleSheet=f"font-size:10px;font-weight:bold;color:{color};border:none;letter-spacing:1px;"))
            vb.addWidget(QLabel(value, styleSheet=f"font-size:18px;font-weight:bold;color:{DARK};border:none;"))
            vb.addWidget(QLabel(note,  styleSheet="font-size:10px;color:#888;border:none;"))
            return card

        exc_pct  = (t3/grand*100) if grand > 0 else 0
        dump_pct = (t4/grand*100) if grand > 0 else 0
        fleet_pct= (t5/grand*100) if grand > 0 else 0

        lay.addWidget(insight("COST PER TON",      f"PKR {cpt:,.0f}",
                              "Lower is more efficient", RED if cpt>8000 else ORANGE if cpt>4000 else GREEN), 0, 0)
        lay.addWidget(insight("EXCAVATOR SHARE",   f"{exc_pct:.1f}%  of spend",
                              f"PKR {t3:,.0f} on excavator", TEAL), 0, 1)
        lay.addWidget(insight("DUMPREI SHARE",     f"{dump_pct:.1f}%  of spend",
                              f"PKR {t4:,.0f} on dumprei", ORANGE), 0, 2)
        lay.addWidget(insight("FLEET SHARE",       f"{fleet_pct:.1f}%  of spend",
                              f"PKR {t5:,.0f} on fleet", BLUE), 1, 0)
        lay.addWidget(insight("TONS EXTRACTED",    f"{tons:,.1f} tons",
                              "From production tracker", PURPLE), 1, 1)
        lay.addWidget(insight("EFFICIENCY RATING",
                              "Good" if cpt < 4000 else "Fair" if cpt < 8000 else "Review",
                              "Based on cost per ton", GREEN if cpt<4000 else ORANGE if cpt<8000 else RED), 1, 2)
        return f

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()
    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)