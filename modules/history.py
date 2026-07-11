import os
from datetime import datetime, date as dt_date
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QDateEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication, QProgressDialog, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QDate

import database
import config


MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

CH_COLORS = {
    "ch1": config.RED,
    "ch2": "#6C3483",
    "ch3": "#0E6655",
    "ch4": config.ORANGE,
    "ch5": config.BLUE,
    "ch6": "#1E8449",
}
CH_NAMES = {
    "ch1": "General Expenditures",
    "ch2": "Royalty to Government",
    "ch3": "Excavator Expenditure",
    "ch4": "Dumprei Expenditure",
    "ch5": "Truck / Dumper",
    "ch6": "Memory Notes",
}


class HistoryModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("Last Hammer  —  Reports & History")
        self.setMinimumSize(1280, 800)
        self._current_mode  = "day"
        self._current_value = dt_date.today().isoformat()
        self._build_ui()
        self._run_search()

    # ─────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_search_bar())

        # Scrollable results area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #EFEFEF; }")
        self._results_container = QWidget()
        self._results_container.setStyleSheet("background: #EFEFEF;")
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(28, 20, 28, 20)
        self._results_layout.setSpacing(18)
        scroll.setWidget(self._results_container)
        root.addWidget(scroll, 1)

        root.addWidget(self._make_footer())

    # ── Header ────────────────────────────────────────────────
    def _make_header(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {config.DARK};")
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)

        if os.path.exists(config.LOGO_PATH):
            lbl_logo = QLabel()
            pix = QPixmap(config.LOGO_PATH).scaled(
                64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            layout.addWidget(lbl_logo)
            layout.addSpacing(12)

        accent = QFrame()
        accent.setFixedWidth(6)
        accent.setFixedHeight(52)
        accent.setStyleSheet("background-color: #F39C12; border-radius: 3px;")
        layout.addWidget(accent)
        layout.addSpacing(14)

        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        lbl = QLabel("Reports & History")
        lbl.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        vbox.addWidget(lbl)
        lbl_sub = QLabel("Search by day or month — view, download PDF, or send by email")
        lbl_sub.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        vbox.addWidget(lbl_sub)
        layout.addLayout(vbox)
        layout.addStretch()

        btn_back = QPushButton("←  Back to Dashboard")
        btn_back.setFixedHeight(44)
        btn_back.setMinimumWidth(200)
        btn_back.setStyleSheet("""
            QPushButton { background-color:#444455; color:white; border-radius:8px;
                border:none; font-size:14px; font-weight:bold; padding:0 20px; }
            QPushButton:hover { background-color:#6666AA; }
        """)
        btn_back.clicked.connect(self._go_back)
        layout.addWidget(btn_back)
        return frame

    # ── Search bar ────────────────────────────────────────────
    def _make_search_bar(self):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-bottom: 2px solid #DDDDDD;")
        frame.setFixedHeight(100)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(20)

        # Mode toggle buttons
        self.btn_mode_day = self._mode_btn("📅  Specific Day", True)
        self.btn_mode_month = self._mode_btn("📆  Specific Month", False)
        self.btn_mode_day.clicked.connect(lambda: self._switch_mode("day"))
        self.btn_mode_month.clicked.connect(lambda: self._switch_mode("month"))
        layout.addWidget(self.btn_mode_day)
        layout.addWidget(self.btn_mode_month)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #EEEEEE;")
        layout.addWidget(div)

        # Day picker
        self.day_widget = QWidget()
        dwl = QHBoxLayout(self.day_widget)
        dwl.setContentsMargins(0, 0, 0, 0)
        lbl_d = QLabel("Date:")
        lbl_d.setStyleSheet("font-size:14px; font-weight:bold; color:#333;")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(46)
        self.date_edit.setFixedWidth(210)
        self.date_edit.setStyleSheet(
            "font-size:16px; font-weight:bold; padding:6px 12px; "
            "border:2px solid #DDDDDD; border-radius:8px;")
        dwl.addWidget(lbl_d)
        dwl.addSpacing(8)
        dwl.addWidget(self.date_edit)
        layout.addWidget(self.day_widget)

        # Month picker
        self.month_widget = QWidget()
        self.month_widget.setVisible(False)
        mwl = QHBoxLayout(self.month_widget)
        mwl.setContentsMargins(0, 0, 0, 0)
        mwl.setSpacing(10)
        lbl_m = QLabel("Month:")
        lbl_m.setStyleSheet("font-size:14px; font-weight:bold; color:#333;")
        self.combo_month = QComboBox()
        self.combo_month.addItems(MONTHS)
        self.combo_month.setCurrentIndex(QDate.currentDate().month() - 1)
        self.combo_month.setFixedHeight(46)
        self.combo_month.setMinimumWidth(160)
        self.combo_month.setStyleSheet(
            "font-size:14px; padding:6px 12px; border:2px solid #DDDDDD; "
            "border-radius:8px; background:white;")
        lbl_y = QLabel("Year:")
        lbl_y.setStyleSheet("font-size:14px; font-weight:bold; color:#333;")
        self.combo_year = QComboBox()
        cy = QDate.currentDate().year()
        for y in range(cy - 3, cy + 2):
            self.combo_year.addItem(str(y))
        self.combo_year.setCurrentText(str(cy))
        self.combo_year.setFixedHeight(46)
        self.combo_year.setMinimumWidth(110)
        self.combo_year.setStyleSheet(
            "font-size:14px; padding:6px 12px; border:2px solid #DDDDDD; "
            "border-radius:8px; background:white;")
        mwl.addWidget(lbl_m)
        mwl.addWidget(self.combo_month)
        mwl.addWidget(lbl_y)
        mwl.addWidget(self.combo_year)
        layout.addWidget(self.month_widget)

        layout.addStretch()

        # Search button
        btn_search = QPushButton("🔍   View Report")
        btn_search.setFixedHeight(56)
        btn_search.setMinimumWidth(220)
        btn_search.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #F39C12, stop:1 #D68910);
                color: white; border-radius: 10px; border: none;
                font-size: 17px; font-weight: bold;
            }
            QPushButton:hover { background: #F5B041; }
            QPushButton:pressed { background: #1A1A2E; }
        """)
        btn_search.clicked.connect(self._run_search)
        layout.addWidget(btn_search)
        return frame

    def _mode_btn(self, text, active):
        btn = QPushButton(text)
        btn.setFixedHeight(46)
        btn.setMinimumWidth(180)
        btn.setCheckable(True)
        btn.setChecked(active)
        self._set_mode_btn_style(btn, active)
        return btn

    def _set_mode_btn_style(self, btn, active):
        if active:
            btn.setStyleSheet("""
                QPushButton { background:#1A1A2E; color:white; border-radius:8px;
                    border:none; font-size:14px; font-weight:bold; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton { background:#EEEEEE; color:#555555; border-radius:8px;
                    border:2px solid #DDDDDD; font-size:14px; font-weight:bold; }
                QPushButton:hover { background:#DDDDDD; }
            """)

    def _switch_mode(self, mode):
        self._current_mode = mode
        self.day_widget.setVisible(mode == "day")
        self.month_widget.setVisible(mode == "month")
        self._set_mode_btn_style(self.btn_mode_day,   mode == "day")
        self._set_mode_btn_style(self.btn_mode_month, mode == "month")
        self.btn_mode_day.setChecked(mode == "day")
        self.btn_mode_month.setChecked(mode == "month")

    # ── Footer ────────────────────────────────────────────────
    def _make_footer(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {config.DARK}; border-top: 4px solid #F39C12;")
        frame.setFixedHeight(60)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)

        self.lbl_period = QLabel("Showing: Today")
        self.lbl_period.setStyleSheet(
            "color: #F39C12; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.lbl_period)
        layout.addStretch()

        self.lbl_grand = QLabel("Total: PKR 0")
        self.lbl_grand.setStyleSheet(
            "color: #FFFFFF; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.lbl_grand)
        return frame

    # ─────────────────────────────────────────────────────────
    def _get_mode_value(self):
        if self._current_mode == "day":
            return "day", self.date_edit.date().toString("yyyy-MM-dd")
        else:
            month_num = str(self.combo_month.currentIndex() + 1).zfill(2)
            year      = self.combo_year.currentText()
            return "month", f"{year}-{month_num}"

    def _period_label(self, mode, value):
        if mode == "day":
            return datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y  (%A)")
        else:
            return datetime.strptime(value + "-01", "%Y-%m-%d").strftime("%B %Y")

    def _filter_month(self, rows, ym):
        return [r for r in rows if r["date"].startswith(ym)]

    def _get_data(self, mode, value):
        conn = database.get_connection()
        if mode == "day":
            ch5_dumper = conn.execute(
                "SELECT te.*, tf.reg_number, tf.owner_name, tf.truck_type "
                "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
                "WHERE te.date=? ORDER BY tf.reg_number, te.id", (value,)
            ).fetchall()
            ch5_loader = conn.execute(
                "SELECT le.*, tf.reg_number, tf.owner_name "
                "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
                "WHERE le.date=? ORDER BY tf.reg_number, le.id", (value,)
            ).fetchall()
            conn.close()
            return {
                "ch1": database.ch1_get_entries(value),
                "ch2": [r for r in database.ch2_get_all_v2() if r["date"] == value],
                "ch3": database.ch3_get_entries(value),
                "ch4": [r for r in database.ch4_get_all_v2() if r["date"] == value],
                "ch5": list(ch5_dumper),
                "ch5_loader": list(ch5_loader),
                "ch6": database.ch6_get_entries(value),
            }
        else:
            if mode == "month":
                ch5_dumper = conn.execute(
                    "SELECT te.*, tf.reg_number, tf.owner_name, tf.truck_type "
                    "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
                    "WHERE te.date LIKE ? ORDER BY tf.reg_number, te.date ASC, te.id",
                    (value + "%",)
                ).fetchall()
                ch5_loader = conn.execute(
                    "SELECT le.*, tf.reg_number, tf.owner_name "
                    "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
                    "WHERE le.date LIKE ? ORDER BY tf.reg_number, le.date ASC, le.id",
                    (value + "%",)
                ).fetchall()
            else:
                ch5_dumper = conn.execute(
                    "SELECT te.*, tf.reg_number, tf.owner_name, tf.truck_type "
                    "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
                    "ORDER BY tf.reg_number, te.date ASC, te.id"
                ).fetchall()
                ch5_loader = conn.execute(
                    "SELECT le.*, tf.reg_number, tf.owner_name "
                    "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
                    "ORDER BY tf.reg_number, le.date ASC, le.id"
                ).fetchall()
            conn.close()
            return {
                "ch1": self._filter_month(database.ch1_get_all(), value),
                "ch2": self._filter_month(database.ch2_get_all_v2(), value),
                "ch3": self._filter_month(database.ch3_get_all(), value),
                "ch4": self._filter_month(database.ch4_get_all_v2(), value),
                "ch5": list(ch5_dumper),
                "ch5_loader": list(ch5_loader),
                "ch6": self._filter_month(database.ch6_get_all(), value),
            }

    # ─────────────────────────────────────────────────────────
    def _run_search(self):
        mode, value = self._get_mode_value()
        self._current_mode  = mode
        self._current_value = value
        label = self._period_label(mode, value)
        data  = self._get_data(mode, value)

        # Totals
        t1  = sum(float(r["amount"] or 0)           for r in data["ch1"])
        t2  = sum(float(r["amount"] or 0)           for r in data["ch2"])
        t3  = sum(float(r["total_amount"] or 0)     for r in data["ch3"])
        t4  = sum(float(r["payment_received"] or 0) for r in data["ch4"])
        t5_loader = sum(float(r["cash_paid"] or 0) + float(r["diesel_worth"] or 0)
                        for r in data.get("ch5_loader", []))
        t5  = sum(float(r["payment"] or 0) for r in data["ch5"]) + t5_loader
        t6  = sum(float(r["amount"] or 0)           for r in data["ch6"])
        grand = t1 + t2 + t3 + t4 + t5 + t6

        self.lbl_period.setText(f"Showing: {label}")
        self.lbl_grand.setText(f"Total: PKR {grand:,.2f}")

        # Clear old results
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ── Action bar (Download + Email) ─────────────────────
        action_bar = self._make_action_bar(mode, value, label, grand)
        self._results_layout.addWidget(action_bar)

        # ── Summary card ──────────────────────────────────────
        summary = self._make_summary_card(
            data, t1, t2, t3, t4, t5, t6, grand, label)
        self._results_layout.addWidget(summary)

        # ── Chapter detail cards ───────────────────────────────
        totals = {"ch1":t1, "ch2":t2, "ch3":t3, "ch4":t4, "ch5":t5, "ch6":t6}
        ch_builders = {
            "ch1": self._ch1_rows,
            "ch2": self._ch2_rows,
            "ch3": self._ch3_rows,
            "ch4": self._ch4_rows,
            "ch5": self._ch5_rows,
            "ch6": self._ch6_rows,
        }
        ch_cols = {
            "ch1": ["Details / Description", "Amount (PKR)", "Date"],
            "ch2": ["Vehicle No.", "Weight (kg)", "Payment (PKR)", "Date"],
            "ch3": ["Details", "Hours", "Total", "Cash Adv", "Diesel Adv", "Balance", "Date"],
            "ch4": ["Reg. No.", "Owner", "Trips", "Cash Paid", "Diesel Paid", "Total Paid", "Balance", "Date"],
            "ch5": ["Details", "Cash Paid", "Diesel Paid", "Total Paid", "Date"],
            "ch6": ["Description", "Person", "Type", "Amount (PKR)", "Date"],
        }

        for key in ["ch1","ch2","ch3","ch4","ch6"]:
            rows = data[key]
            card = self._make_chapter_card(
                key, rows, ch_cols[key], ch_builders[key],
                totals[key], len(rows))
            self._results_layout.addWidget(card)

        # CH5 — custom grouped card
        ch5_card = self._make_ch5_card(
            data["ch5"], data.get("ch5_loader", []), t5)
        self._results_layout.addWidget(ch5_card)

        self._results_layout.addStretch()

    # ── Action bar ────────────────────────────────────────────
    def _make_action_bar(self, mode, value, label, grand):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-radius: 12px; "
            "border: 1px solid #DDDDDD;")
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        lbl = QLabel(f"📋  {label}")
        lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1A1A2E; border: none;")
        layout.addWidget(lbl)
        layout.addStretch()

        # PKR total
        lbl_total = QLabel(f"PKR {grand:,.2f}")
        lbl_total.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {config.RED}; border: none;")
        layout.addWidget(lbl_total)

        layout.addSpacing(30)

        btn_pdf = QPushButton("📄   Download PDF")
        btn_pdf.setFixedHeight(54)
        btn_pdf.setMinimumWidth(200)
        btn_pdf.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #E74C3C, stop:1 #C0392B);
                color: white; border-radius: 10px; border: none;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #E74C3C; }
        """)
        btn_pdf.clicked.connect(lambda: self._do_pdf(mode, value, label))

        btn_email = QPushButton("📧   Send by Email")
        btn_email.setFixedHeight(54)
        btn_email.setMinimumWidth(200)
        btn_email.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #2980B9, stop:1 #1B4F72);
                color: white; border-radius: 10px; border: none;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #3498DB; }
        """)
        btn_email.clicked.connect(lambda: self._do_email(mode, value, label))

        layout.addWidget(btn_pdf)
        layout.addWidget(btn_email)
        return frame

    # ── Summary card ──────────────────────────────────────────
    def _make_summary_card(self, data, t1,t2,t3,t4,t5,t6, grand, label):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-radius: 12px; "
            "border: 1px solid #DDDDDD;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        lbl = QLabel("SUMMARY")
        lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #888888; "
            "letter-spacing: 2px; border: none;")
        title_row.addWidget(lbl)
        title_row.addStretch()
        layout.addLayout(title_row)

        # 6-column summary grid
        grid = QGridLayout()
        grid.setSpacing(12)
        # Compute extra stats
        total_weight_kg  = sum(float(r["weight_tons"] or 0) for r in data["ch2"])
        total_payment_r  = sum(float(r["amount"] or 0)      for r in data["ch2"])
        total_hours      = sum(float(r["hours_worked"] or 0) for r in data["ch3"])
        total_trips_d    = sum(int(r["total_trips"] or 0)    for r in data["ch4"])
        total_dumper_pay = sum(float(r["payment"] or 0)      for r in data["ch5"])
        total_loader_days= sum(float(r["days_worked"] or 0)  for r in data.get("ch5_loader",[]))
        total_loader_pay = sum(float(r["cash_paid"] or 0) + float(r["diesel_worth"] or 0)
                               for r in data.get("ch5_loader",[]))

        def extra(lines):
            w = QWidget(); w.setStyleSheet("background:transparent;border:none;")
            vb = QVBoxLayout(w); vb.setContentsMargins(0,2,0,0); vb.setSpacing(1)
            for line in lines:
                l = QLabel(line)
                l.setStyleSheet("font-size:11px;color:#555555;border:none;")
                vb.addWidget(l)
            return w

        chapters = [
            ("CH 1", "General Expenditures", config.RED,    t1, len(data["ch1"]),
             [f"{len(data['ch1'])} entries"]),
            ("CH 2", "Royalty to Govt",       "#6C3483",    t2, len(data["ch2"]),
             [f"Total Weight: {total_weight_kg:,.0f} kg",
              f"Total Payment: PKR {total_payment_r:,.0f}",
              f"{len(data['ch2'])} entries"]),
            ("CH 3", "Excavator",             "#0E6655",    t3, len(data["ch3"]),
             [f"Total Hours: {total_hours:.1f} hrs",
              f"Work Total: PKR {t3:,.0f}",
              f"{len(data['ch3'])} entries"]),
            ("CH 4", "Dumprei",               config.ORANGE,t4, len(data["ch4"]),
             [f"Total Trips: {total_trips_d}",
              f"Total Paid: PKR {t4:,.0f}",
              f"{len(data['ch4'])} entries"]),
            ("CH 5", "Truck / Dumper / Loader", config.BLUE, t5,
             len(data["ch5"]) + len(data.get("ch5_loader",[])),
             [f"Dumper Paid: PKR {total_dumper_pay:,.0f}",
              f"Loader Days: {total_loader_days:.1f}  |  PKR {total_loader_pay:,.0f}",
              f"{len(data['ch5'])} dumper + {len(data.get('ch5_loader',[]))} loader entries"]),
            ("CH 6", "Memory Notes",          "#1E8449",    t6, len(data["ch6"]),
             [f"{len(data['ch6'])} entries"]),
        ]
        for i, (ch, name, color, total, count, extra_lines) in enumerate(chapters):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: #FAFAFA;
                    border-radius: 8px;
                    border-left: 5px solid {color};
                    border-top: 1px solid #EEEEEE;
                    border-right: 1px solid #EEEEEE;
                    border-bottom: 1px solid #EEEEEE;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.setSpacing(3)
            lbl_ch = QLabel(f"{ch}  •  {name}")
            lbl_ch.setStyleSheet(
                f"font-size:12px; font-weight:bold; color:{color}; border:none;")
            lbl_amt = QLabel(f"PKR {total:,.0f}")
            lbl_amt.setStyleSheet(
                f"font-size:17px; font-weight:bold; color:#1A1A2E; border:none;")
            cl.addWidget(lbl_ch)
            cl.addWidget(lbl_amt)
            cl.addWidget(extra(extra_lines))
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)

        # Grand total
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #EEEEEE; border: none; "
                         "border-top: 1px solid #EEEEEE;")
        layout.addWidget(sep)
        gt_row = QHBoxLayout()
        lbl_gt = QLabel("GRAND TOTAL")
        lbl_gt.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#888; border:none;")
        lbl_gt_val = QLabel(f"PKR {grand:,.2f}")
        lbl_gt_val.setStyleSheet(
            f"font-size:26px; font-weight:bold; color:{config.RED}; border:none;")
        gt_row.addWidget(lbl_gt)
        gt_row.addStretch()
        gt_row.addWidget(lbl_gt_val)
        layout.addLayout(gt_row)
        return frame

    # ── Chapter detail card ───────────────────────────────────
    def _make_chapter_card(self, key, rows, columns, row_builder, total, count):
        color = CH_COLORS[key]
        name  = CH_NAMES[key]

        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-radius: 12px; "
            "border: 1px solid #DDDDDD;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Card header
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {color}, stop:1 {config.DARK});
                border-radius: 12px 12px 0 0;
            }}
        """)
        hdr.setFixedHeight(52)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(20, 0, 20, 0)

        lbl_name = QLabel(f"{key.upper().replace('CH','CH ')}  —  {name}")
        lbl_name.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; background: transparent;")
        hdr_l.addWidget(lbl_name)
        hdr_l.addStretch()

        lbl_cnt = QLabel(f"{count} entr{'y' if count==1 else 'ies'}")
        lbl_cnt.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 13px; background: transparent;")
        hdr_l.addWidget(lbl_cnt)
        hdr_l.addSpacing(20)

        lbl_tot = QLabel(f"PKR {total:,.2f}")
        lbl_tot.setStyleSheet(
            "color: white; font-size: 17px; font-weight: bold; background: transparent;")
        hdr_l.addWidget(lbl_tot)
        layout.addWidget(hdr)

        if not rows:
            no_data = QLabel("  No entries for this period")
            no_data.setStyleSheet(
                "color: #AAAAAA; font-size: 14px; padding: 20px;")
            layout.addWidget(no_data)
            return frame

        # Table
        all_cols = ["S.No"] + columns
        tbl = QTableWidget()
        tbl.setColumnCount(len(all_cols))
        tbl.setHorizontalHeaderLabels(all_cols)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setSortingEnabled(False)
        tbl.setFont(QFont("Arial", 13))
        hf = QFont("Arial", 12); hf.setBold(True)
        tbl.horizontalHeader().setFont(hf)
        tbl.horizontalHeader().setMinimumHeight(44)
        tbl.setFixedHeight(min(44 + len(rows) * 52 + 10, 44 + 8 * 52))

        n = len(all_cols)
        tbl.setColumnWidth(0, 65)
        for i in range(1, n):
            tbl.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        tbl.setStyleSheet(f"""
            QTableWidget {{
                background: white; alternate-background-color: #F5F8FF;
                gridline-color: #EEEEEE; border: none; font-size: 13px;
            }}
            QTableWidget::item {{ padding: 8px 12px; }}
            QTableWidget::item:selected {{ background: #D6EAF8; color: #1A1A2E; }}
            QHeaderView::section {{
                background-color: {config.DARK}; color: white;
                font-size: 12px; font-weight: bold;
                padding: 10px 8px; border: none;
                border-right: 1px solid #2C2C4E;
            }}
        """)

        for i, row in enumerate(rows):
            cells = row_builder(row)
            ri = tbl.rowCount()
            tbl.insertRow(ri)
            sno = QTableWidgetItem(str(i + 1))
            sno.setTextAlignment(Qt.AlignCenter)
            tbl.setItem(ri, 0, sno)
            for j, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if j == len(cells) - 1:  # date col
                    item.setForeground(QColor("#1B4F72"))
                    item.setFont(QFont("Arial", 12, QFont.Bold))
                tbl.setItem(ri, j + 1, item)
            tbl.setRowHeight(ri, 50)

        layout.addWidget(tbl)
        return frame

    # ── Row builders ──────────────────────────────────────────
    def _ch1_rows(self, r):
        return [r["details"], f"PKR {r['amount']:,.2f}", r["date"]]

    def _ch2_rows(self, r):
        keys = r.keys()
        vehicle = (r["vehicle_number"] if "vehicle_number" in keys and r["vehicle_number"] else r["details"]) or "—"
        wt = float(r["weight_tons"]) if "weight_tons" in keys and r["weight_tons"] else 0
        amt = float(r["amount"]) if r["amount"] else 0
        return [vehicle, f"{wt:,.0f} kg", f"PKR {amt:,.2f}" if amt else "—", r["date"]]

    def _ch3_rows(self, r):
        keys = r.keys()
        ca = float(r["cash_advance"] if "cash_advance" in keys and r["cash_advance"] else r["paid_cash"] if "paid_cash" in keys and r["paid_cash"] else 0)
        da = float(r["diesel_advance"] if "diesel_advance" in keys and r["diesel_advance"] else r["paid_diesel"] if "paid_diesel" in keys and r["paid_diesel"] else 0)
        return [(r["details"] if "details" in keys and r["details"] else "—"), str(r["hours_worked"]),
                f"PKR {float(r['total_amount'] or 0):,.2f}",
                f"PKR {ca:,.0f}", f"PKR {da:,.0f}",
                f"PKR {float(r['balance_due'] or 0):,.2f}", r["date"]]

    def _ch4_rows(self, r):
        keys = r.keys()
        pc = float(r["paid_cash"] if "paid_cash" in keys and r["paid_cash"] else 0)
        pd_ = float(r["paid_diesel_worth"] if "paid_diesel_worth" in keys and r["paid_diesel_worth"] else 0)
        total = float(r["payment_received"] if r["payment_received"] else (pc + pd_))
        trips = r["total_trips"] if "total_trips" in keys and r["total_trips"] else 0
        return [r["reg_number"], r["owner_name"], str(trips),
                f"PKR {pc:,.0f}" if pc else "—",
                f"PKR {pd_:,.0f}" if pd_ else "—",
                f"PKR {total:,.2f}",
                f"PKR {float(r['balance_due'] or 0):,.2f}", r["date"]]

    def _make_ch5_card(self, dumper_rows, loader_rows, total):
        """Custom CH5 card — grouped per truck with sub-tables."""
        from PyQt5.QtWidgets import QScrollArea
        color = config.BLUE
        name  = "Truck / Dumper / Loader Fleet"
        total_entries = len(dumper_rows) + len(loader_rows)

        frame = QFrame()
        frame.setStyleSheet(
            "background-color: white; border-radius: 12px; border: 1px solid #DDDDDD;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Card header
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {color}, stop:1 {config.DARK});
                border-radius: 12px 12px 0 0;
            }}
        """)
        hdr.setFixedHeight(52)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(20, 0, 20, 0)
        lbl_n = QLabel(f"CH 5  —  {name}")
        lbl_n.setStyleSheet("color:white;font-size:15px;font-weight:bold;background:transparent;")
        hdr_l.addWidget(lbl_n); hdr_l.addStretch()
        lbl_c = QLabel(f"{total_entries} entr{'y' if total_entries==1 else 'ies'}")
        lbl_c.setStyleSheet("color:rgba(255,255,255,0.7);font-size:13px;background:transparent;")
        hdr_l.addWidget(lbl_c); hdr_l.addSpacing(20)
        lbl_t = QLabel(f"PKR {total:,.2f}")
        lbl_t.setStyleSheet("color:white;font-size:17px;font-weight:bold;background:transparent;")
        hdr_l.addWidget(lbl_t)
        layout.addWidget(hdr)

        if not dumper_rows and not loader_rows:
            nd = QLabel("  No truck/loader entries for this period")
            nd.setStyleSheet("color:#AAAAAA;font-size:14px;padding:20px;")
            layout.addWidget(nd)
            return frame

        body = QWidget(); body.setStyleSheet("background:white;border:none;")
        body_l = QVBoxLayout(body); body_l.setContentsMargins(12,10,12,10); body_l.setSpacing(10)

        def make_sub_header(text, bg):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"background:{bg};color:white;font-size:13px;font-weight:bold;"
                f"padding:7px 14px;border-radius:6px;border:none;")
            lbl.setWordWrap(True)
            return lbl

        def make_sub_table(cols, rows_data, accent):
            tbl = QTableWidget()
            tbl.setColumnCount(len(cols))
            tbl.setHorizontalHeaderLabels(cols)
            tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
            tbl.setAlternatingRowColors(True)
            tbl.verticalHeader().setVisible(False)
            tbl.setSortingEnabled(False)
            tbl.setFont(QFont("Arial", 12))
            hf = QFont("Arial", 11); hf.setBold(True)
            tbl.horizontalHeader().setFont(hf)
            tbl.horizontalHeader().setMinimumHeight(40)
            tbl.setFixedHeight(40 + len(rows_data) * 46 + 4)
            tbl.setColumnWidth(0, 55)
            for i in range(1, len(cols)):
                tbl.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            tbl.setStyleSheet(f"""
                QTableWidget {{background:white;alternate-background-color:#F5F8FF;
                    gridline-color:#EEEEEE;border:none;font-size:12px;}}
                QTableWidget::item {{padding:6px 10px;}}
                QTableWidget::item:selected {{background:#D6EAF8;color:#1A1A2E;}}
                QHeaderView::section {{background:{config.DARK};color:white;
                    font-size:11px;font-weight:bold;padding:8px 6px;border:none;
                    border-right:1px solid #2C2C4E;}}
            """)
            for i, cells in enumerate(rows_data):
                ri = tbl.rowCount(); tbl.insertRow(ri)
                for j, val in enumerate(cells):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    if j == len(cells)-1:
                        item.setForeground(QColor("#1B4F72"))
                        item.setFont(QFont("Arial", 12, QFont.Bold))
                    tbl.setItem(ri, j, item)
                tbl.setRowHeight(ri, 44)
            return tbl

        # ── DUMPERS grouped by truck ──
        trucks_seen = {}
        for r in dumper_rows:
            key = (r["reg_number"], r["owner_name"], r["truck_type"])
            trucks_seen.setdefault(key, []).append(r)

        for (reg, owner, ttype), t_rows in trucks_seen.items():
            truck_total = sum(float(r["payment"] or 0) for r in t_rows)
            body_l.addWidget(make_sub_header(
                f"🚚  {reg}  —  {owner}  ({ttype})   |   Total Paid: PKR {truck_total:,.0f}",
                "#1B4F72"))
            cols = ["S.No", "Details", "Trips", "Cash Paid", "Diesel Paid", "Total Paid", "Balance Due", "Date"]
            rows_data = []
            for i, r in enumerate(t_rows):
                keys = r.keys()
                pc  = float(r["paid_cash"]   if "paid_cash"   in keys and r["paid_cash"]   else 0)
                pd_ = float(r["paid_diesel"] if "paid_diesel" in keys and r["paid_diesel"] else 0)
                tot = float(r["payment"] or 0)
                bal = float(r["balance_due"] if "balance_due" in keys and r["balance_due"] else 0)
                det = (r["details"] if "details" in keys and r["details"] else "") or "—"
                trips = str(r["trips"]) if "trips" in keys and r["trips"] else "—"
                rows_data.append([
                    str(i+1), det, trips,
                    f"PKR {pc:,.0f}" if pc else "—",
                    f"PKR {pd_:,.0f}" if pd_ else "—",
                    f"PKR {tot:,.0f}",
                    f"PKR {bal:,.0f}" if bal else "—",
                    r["date"]
                ])
            body_l.addWidget(make_sub_table(cols, rows_data, "#1B4F72"))

        # ── LOADERS grouped by truck ──
        loaders_seen = {}
        for r in loader_rows:
            key = (r["reg_number"], r["owner_name"])
            loaders_seen.setdefault(key, []).append(r)

        for (reg, owner), l_rows in loaders_seen.items():
            l_cash   = sum(float(r["cash_paid"]   or 0) for r in l_rows)
            l_diesel = sum(float(r["diesel_worth"] or 0) for r in l_rows)
            l_days   = sum(float(r["days_worked"]  or 0) for r in l_rows)
            body_l.addWidget(make_sub_header(
                f"🏗  {reg}  —  {owner}  (Loader)   |   "
                f"Days: {l_days:.1f}  |  Cash: PKR {l_cash:,.0f}  |  Diesel: PKR {l_diesel:,.0f}",
                "#0E6655"))
            cols = ["S.No", "Type", "Description", "Days Worked", "Cash Paid", "Diesel (PKR)", "Date"]
            rows_data = []
            for j, r in enumerate(l_rows):
                keys_r = r.keys()
                etype = r["entry_type"] if "entry_type" in keys_r else "Work"
                desc  = (r["description"] if "description" in keys_r and r["description"] else "") or "—"
                dw    = float(r["days_worked"]  or 0) if "days_worked"  in keys_r and r["days_worked"]  else 0
                cp    = float(r["cash_paid"]    or 0) if "cash_paid"    in keys_r and r["cash_paid"]    else 0
                dv    = float(r["diesel_worth"] or 0) if "diesel_worth" in keys_r and r["diesel_worth"] else 0
                rows_data.append([
                    str(j+1), etype, desc,
                    f"{dw:.1f} days" if dw else "—",
                    f"PKR {cp:,.0f}" if cp else "—",
                    f"PKR {dv:,.0f}" if dv else "—",
                    r["date"]
                ])
            body_l.addWidget(make_sub_table(cols, rows_data, "#0E6655"))

        layout.addWidget(body)
        return frame

    def _make_ch5_card_dummy(self): pass  # placeholder

    def _ch5_rows(self, r):
        keys = r.keys()
        pc  = float(r["paid_cash"] if "paid_cash" in keys and r["paid_cash"] else 0)
        pd_ = float(r["paid_diesel"] if "paid_diesel" in keys and r["paid_diesel"] else 0)
        tot = float(r["payment"] if r["payment"] else (pc + pd_))
        det = (r["details"] if "details" in keys and r["details"] else "") or "—"
        return [det,
                f"PKR {pc:,.0f}" if pc else "—",
                f"PKR {pd_:,.0f}" if pd_ else "—",
                f"PKR {tot:,.2f}", r["date"]]

    def _ch6_rows(self, r):
        return [r["description"], r["person_name"] or "—",
                r["transaction_type"], f"PKR {r['amount']:,.2f}", r["date"]]

    # ── PDF & Email actions ───────────────────────────────────
    def _do_pdf(self, mode, value, label):
        prog = QProgressDialog("Generating PDF...", None, 0, 0, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setWindowTitle("Please Wait")
        prog.show()
        QApplication.processEvents()

        try:
            from reports.daily_report import generate_report
            path = generate_report(mode=mode, value=value)
            prog.close()
            QMessageBox.information(self, "PDF Ready",
                f"✅  PDF generated!\n\nPeriod: {label}\n\nSaved to:\n{path}")
            try:
                os.startfile(path)
            except:
                pass
        except Exception as e:
            prog.close()
            QMessageBox.critical(self, "Error",
                f"Could not generate PDF:\n{str(e)}\n\n"
                "Install reportlab first:\n  pip install reportlab")

    def _do_email(self, mode, value, label):
        reply = QMessageBox.question(
            self, "Confirm Send",
            f"Send the report for:\n{label}\n\nTo the owner's email?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply != QMessageBox.Yes:
            return

        prog = QProgressDialog("Generating PDF and sending email...",
                               None, 0, 0, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setWindowTitle("Please Wait")
        prog.show()
        QApplication.processEvents()

        try:
            from reports.daily_report import generate_report
            path = generate_report(mode=mode, value=value)
        except Exception as e:
            prog.close()
            QMessageBox.critical(self, "Error", f"PDF error:\n{str(e)}")
            return

        from reports.email_sender import send_report
        ok, msg = send_report(path, mode, value, label)
        prog.close()

        if ok:
            QMessageBox.information(self, "Sent!", msg)
        else:
            QMessageBox.critical(self, "Failed", msg)

    def _go_back(self):
        if self.parent_dashboard:
            self.parent_dashboard.showMaximized()
        self.close()