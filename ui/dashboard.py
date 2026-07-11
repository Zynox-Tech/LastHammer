import os
from datetime import date as dt_date
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame, QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import database
import config


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.setMinimumSize(1280, 800)
        self._current_win = None
        self._build_ui()
        self.refresh_totals()
        self.showMaximized()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_header())
        root.addWidget(self._make_summary_bar())
        root.addWidget(self._make_module_grid(), 1)
        root.addWidget(self._make_bottom_bar())

    # ── Header ────────────────────────────────────────────────
    def _make_header(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {config.DARK};")
        frame.setFixedHeight(100)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(40, 12, 40, 12)

        if os.path.exists(config.LOGO_PATH):
            lbl_logo = QLabel()
            pix = QPixmap(config.LOGO_PATH).scaled(
                72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            layout.addWidget(lbl_logo)
        layout.addSpacing(20)

        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        lbl_title = QLabel("LAST HAMMER")
        lbl_title.setStyleSheet(
            f"color: {config.WHITE}; font-size: 30px; font-weight: bold;")
        vbox.addWidget(lbl_title)
        lbl_sub = QLabel("Expenditure Management System  —  Mining Operations")
        lbl_sub.setStyleSheet("color: #AAAAAA; font-size: 14px;")
        vbox.addWidget(lbl_sub)
        layout.addLayout(vbox)
        layout.addStretch()

        today_str = dt_date.today().strftime("%A, %d %B %Y")
        lbl_date = QLabel(today_str)
        lbl_date.setStyleSheet(
            "color: #CCCCCC; font-size: 15px; font-weight: bold;")
        lbl_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(lbl_date)
        return frame

    # ── Summary bar ───────────────────────────────────────────
    def _make_summary_bar(self):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: #E8E8E8; border-bottom: 2px solid #CCCCCC;")
        frame.setFixedHeight(72)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(40, 0, 40, 0)

        lbl = QLabel("TODAY'S TOTAL EXPENDITURE:")
        lbl.setStyleSheet("color: #555; font-size: 15px; font-weight: bold;")
        layout.addWidget(lbl)
        layout.addSpacing(20)

        self.lbl_grand_total = QLabel("PKR 0")
        self.lbl_grand_total.setStyleSheet(
            f"color: {config.RED}; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.lbl_grand_total)
        layout.addStretch()

        lbl_bal = QLabel("LEDGER BALANCE:")
        lbl_bal.setStyleSheet("color: #555; font-size: 15px; font-weight: bold;")
        layout.addWidget(lbl_bal)
        layout.addSpacing(14)

        self.lbl_balance = QLabel("PKR 0")
        self.lbl_balance.setStyleSheet(
            f"color: {config.BLUE}; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.lbl_balance)
        return frame

    # ── Module grid ───────────────────────────────────────────
    def _make_module_grid(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #EFEFEF; }")

        container = QWidget()
        container.setStyleSheet("background-color: #EFEFEF;")
        grid = QGridLayout(container)
        grid.setContentsMargins(40, 30, 40, 30)
        grid.setSpacing(22)

        modules = [
            ("CH 1", "General Expenditures",       config.RED,    self._open_ch1),
            ("CH 2", "Royalty to Government",       "#6C3483",     self._open_ch2),
            ("CH 3", "Excavator Expenditure",       "#0E6655",     self._open_ch3),
            ("CH 4", "Dumprei Expenditure",         config.ORANGE, self._open_ch4),
            ("CH 5", "Truck / Dumper Expenditure",  config.BLUE,   self._open_ch5),
            ("CH 6", "Memory Notes",                "#1E8449",     self._open_ch6),
            ("CH 7", "Debit / Credit Ledger",       "#C0392B",     self._open_ch7),
            ("CH 8", "Surface / Land Rent",          "#2C7873",     self._open_land),
            ("📊",   "Reports & History",           "#F39C12",     self._open_history),
            ("🧾",   "Invoice Generator",            "#8E44AD",     self._open_invoice),
            ("💰",   "Advance / Loan Register",       "#E67E22",     self._open_advances),
            ("⛏",    "Production Tracker",            "#8E44AD",     self._open_production),
            ("⚡",   "Quick Entry",                   "#F39C12",     self._open_quick),
            ("🔔",   "Alerts & Reminders",            "#E74C3C",     self._open_alerts),
            ("🔍",   "Global Search",                 "#2980B9",     self._open_search),
            ("📈",   "Business Intelligence",         "#27AE60",     self._open_bi),
            ("⛽",   "Diesel & Cash Tracker",            "#E67E22",     self._open_fuel),
            ("👤",   "People Register",                  "#1B4F72",     self._open_people),
        ]

        self.total_labels = {}
        for i, (ch, name, color, handler) in enumerate(modules):
            card = self._make_module_card(ch, name, color, handler, i)
            row, col = divmod(i, 4)
            grid.addWidget(card, row, col)

        for c in range(4):
            grid.setColumnStretch(c, 1)
        grid.setRowStretch(2, 1)
        grid.setRowStretch(3, 1)

        scroll.setWidget(container)
        return scroll

    def _make_module_card(self, ch, name, color, handler, idx):
        is_special = ch == "📊"

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#1A1A2E' if is_special else 'white'};
                border-radius: 14px;
                border: 2px solid {'#F39C12' if is_special else '#DDDDDD'};
            }}
        """)
        frame.setMinimumHeight(210)
        frame.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)

        bar = QFrame()
        bar.setFixedHeight(6)
        bar.setStyleSheet(
            f"background-color: {color}; border-radius: 3px; border: none;")
        layout.addWidget(bar)
        layout.addSpacing(4)

        lbl_ch = QLabel(ch if is_special else ch)
        txt_color = color if not is_special else "#F39C12"
        lbl_ch.setStyleSheet(
            f"color: {txt_color}; font-size: {'22px' if is_special else '14px'}; "
            f"font-weight: bold; border: none;")
        layout.addWidget(lbl_ch)

        lbl_name = QLabel(name)
        name_color = "white" if is_special else config.DARK
        lbl_name.setStyleSheet(
            f"color: {name_color}; font-size: 18px; font-weight: bold; border: none;")
        lbl_name.setWordWrap(True)
        layout.addWidget(lbl_name)

        layout.addStretch()

        if not is_special:
            lbl_total = QLabel("PKR 0")
            lbl_total.setStyleSheet(
                f"color: {color}; font-size: 22px; font-weight: bold; border: none;")
            layout.addWidget(lbl_total)
            keys = ["ch1","ch2","ch3","ch4","ch5","ch6","balance","land","_","_inv","_","_","_","_","_","_","_","_"]
            self.total_labels[keys[idx]] = lbl_total
        else:
            lbl_sub = QLabel("View  •  Download  •  Send Email")
            lbl_sub.setStyleSheet(
                "color: #AAAAAA; font-size: 13px; border: none;")
            layout.addWidget(lbl_sub)

        layout.addSpacing(6)

        btn = QPushButton(
            f"Open Reports →" if is_special else f"Open  {ch}  →")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {'#1A1A2E' if is_special else 'white'};
                border-radius: 7px; border: none;
                padding: 10px; font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {config.DARK if not is_special else '#F5B041'}; 
                color: white; }}
        """)
        btn.setMinimumHeight(42)
        btn.clicked.connect(handler)
        layout.addWidget(btn)

        return frame

    # ── Bottom bar ────────────────────────────────────────────
    def _make_bottom_bar(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {config.DARK}; "
            f"border-top: 4px solid {config.RED};")
        frame.setFixedHeight(76)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(16)

        btn_email = QPushButton("📧   Send Today's Report by Email")
        btn_email.setFixedHeight(50)
        btn_email.setMinimumWidth(300)
        btn_email.setStyleSheet("""
            QPushButton { background-color:#1B4F72; color:white; border-radius:8px;
                border:none; font-size:15px; font-weight:bold; }
            QPushButton:hover { background-color:#2980B9; }
        """)
        btn_email.clicked.connect(self._send_email)

        btn_report = QPushButton("📄   Generate PDF Report")
        btn_report.setFixedHeight(50)
        btn_report.setMinimumWidth(240)
        btn_report.setStyleSheet("""
            QPushButton { background-color:#922B21; color:white; border-radius:8px;
                border:none; font-size:15px; font-weight:bold; }
            QPushButton:hover { background-color:#E74C3C; }
        """)
        btn_report.clicked.connect(self._generate_report)

        btn_settings = QPushButton("⚙   Settings")
        btn_settings.setFixedHeight(50)
        btn_settings.setMinimumWidth(140)
        btn_settings.setStyleSheet("""
            QPushButton { background-color:#555555; color:white; border-radius:8px;
                border:none; font-size:14px; font-weight:bold; }
            QPushButton:hover { background-color:#888888; }
        """)
        btn_settings.clicked.connect(self._open_settings)

        layout.addWidget(btn_email)
        layout.addWidget(btn_report)
        layout.addStretch()
        layout.addWidget(btn_settings)
        return frame

    # ─────────────────────────────────────────────────────────
    def refresh_totals(self):
        today  = dt_date.today().isoformat()
        # Summary bar = today only
        today_total = database.get_today_total(today)
        self.lbl_grand_total.setText(f"PKR {today_total:,.0f}")
        bal = database.ch7_get_current_balance()
        self.lbl_balance.setText(f"PKR {bal:,.0f}")
        # Module cards = all-time totals
        try:
            t1 = database.ch1_grand_total()
            t2 = 0  # royalty = weight not PKR
            t3 = database.ex_grand_total()
            t4 = database.ch4_grand_total()
            t5 = database.fleet_grand_total()
            t6 = database.ch6_grand_total()
        except Exception:
            t1=t2=t3=t4=t5=t6=0
        mapping = {"ch1":t1,"ch2":t2,"ch3":t3,"ch4":t4,"ch5":t5,"ch6":t6}
        for k,v in mapping.items():
            if k in self.total_labels:
                self.total_labels[k].setText(f"PKR {v:,.0f}")

    def _open_module(self, ModuleClass):
        self._current_win = ModuleClass(parent_dashboard=self)
        self._current_win.showMaximized()
        self.hide()

    def _open_ch1(self):
        from modules.general   import GeneralModule;   self._open_module(GeneralModule)
    def _open_ch2(self):
        from modules.royalty   import RoyaltyModule;   self._open_module(RoyaltyModule)
    def _open_ch3(self):
        from modules.excavator import ExcavatorModule; self._open_module(ExcavatorModule)
    def _open_ch4(self):
        from modules.dumprei   import DumpreiModule;   self._open_module(DumpreiModule)
    def _open_ch5(self):
        from modules.truck     import TruckModule;     self._open_module(TruckModule)
    def _open_ch6(self):
        from modules.memo      import MemoModule;      self._open_module(MemoModule)
    def _open_ch7(self):
        from modules.ledger     import LedgerModule;    self._open_module(LedgerModule)
    def _open_land(self):
        from modules.land_rent  import LandRentModule;  self._open_module(LandRentModule)
    def _open_history(self):
        from modules.history   import HistoryModule;   self._open_module(HistoryModule)
    def _open_invoice(self):
        from modules.invoice       import InvoiceModule;     self._open_module(InvoiceModule)
    def _open_advances(self):
        from modules.advances      import AdvancesModule;    self._open_module(AdvancesModule)
    def _open_production(self):
        from modules.production    import ProductionModule;  self._open_module(ProductionModule)
    def _open_quick(self):
        from modules.quick_entry   import QuickEntryModule;  self._open_module(QuickEntryModule)
    def _open_alerts(self):
        from modules.alerts        import AlertsModule;      self._open_module(AlertsModule)
    def _open_search(self):
        from modules.search        import SearchModule;      self._open_module(SearchModule)
    def _open_bi(self):
        from modules.business_intel import BIModule;         self._open_module(BIModule)
    def _open_fuel(self):
        from modules.fuel_tracker    import FuelTrackerModule;  self._open_module(FuelTrackerModule)
    def _open_people(self):
        from modules.people_register import PeopleRegister;    self._open_module(PeopleRegister)

    def _send_email(self):
        from ui.report_selector import ReportSelectorDialog
        dlg = ReportSelectorDialog(action="email", parent=self)
        dlg.exec_()

    def _generate_report(self):
        from ui.report_selector import ReportSelectorDialog
        dlg = ReportSelectorDialog(action="pdf", parent=self)
        dlg.exec_()

    def _open_settings(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog(parent=self)
        dlg.exec_()