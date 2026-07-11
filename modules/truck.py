import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QScrollArea, QRadioButton,
    QButtonGroup, QApplication
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QDate

import database
import config

TRUCK_TYPES = ["Dumper", "Loader"]


# ══════════════════════════════════════════════════════════════
#  CHAPTER 5 — FLEET VIEW
# ══════════════════════════════════════════════════════════════
class TruckModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("Last Hammer  —  Chapter 5 — Truck / Dumper / Loader Fleet")
        self.setMinimumSize(1280, 800)
        self._build_ui()
        self.refresh_fleet()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_header())
        root.addWidget(self._make_toolbar())
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:#EFEFEF;}")
        self.fleet_container = QWidget()
        self.fleet_container.setStyleSheet("background:#EFEFEF;")
        from PyQt5.QtWidgets import QGridLayout
        self.fleet_layout = QGridLayout(self.fleet_container)
        self.fleet_layout.setContentsMargins(30, 24, 30, 24)
        self.fleet_layout.setSpacing(20)
        self.scroll.setWidget(self.fleet_container)
        root.addWidget(self.scroll, 1)
        root.addWidget(self._make_footer())

    def _make_header(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color:{config.DARK};")
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)
        if os.path.exists(config.LOGO_PATH):
            lbl = QLabel()
            pix = QPixmap(config.LOGO_PATH).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl.setPixmap(pix); layout.addWidget(lbl); layout.addSpacing(12)
        accent = QFrame(); accent.setFixedWidth(6); accent.setFixedHeight(52)
        accent.setStyleSheet(f"background:{config.BLUE}; border-radius:3px;")
        layout.addWidget(accent); layout.addSpacing(14)
        vbox = QVBoxLayout(); vbox.setSpacing(2)
        lbl_t = QLabel("Chapter 5 — Truck / Dumper / Loader Fleet")
        lbl_t.setStyleSheet("color:white;font-size:24px;font-weight:bold;")
        vbox.addWidget(lbl_t)
        lbl_s = QLabel("Dumpers: record cash & diesel payments per trip   |   Loaders: track daily work + payments")
        lbl_s.setStyleSheet("color:#AAAAAA;font-size:13px;")
        vbox.addWidget(lbl_s); layout.addLayout(vbox); layout.addStretch()
        btn_back = QPushButton("←  Back to Dashboard")
        btn_back.setFixedHeight(44); btn_back.setMinimumWidth(200)
        btn_back.setStyleSheet("""QPushButton{background:#444455;color:white;border-radius:8px;
            border:none;font-size:14px;font-weight:bold;padding:0 20px;}
            QPushButton:hover{background:#6666AA;}""")
        btn_back.clicked.connect(self._go_back); layout.addWidget(btn_back)
        return frame

    def _make_toolbar(self):
        frame = QFrame()
        frame.setStyleSheet("background:white;border-bottom:2px solid #DDDDDD;")
        frame.setFixedHeight(82)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0); layout.setSpacing(20)
        for label, color, value in [
            ("REGISTERED DUMPERS", config.BLUE, "dumpers"),
            ("REGISTERED LOADERS", "#0E6655", "loaders"),
            ("TOTAL PAYMENTS", config.RED, "total"),
        ]:
            col = QVBoxLayout(); col.setSpacing(3)
            lbl_h = QLabel(label)
            lbl_h.setStyleSheet("font-size:10px;font-weight:bold;color:#AAAAAA;letter-spacing:1px;")
            lbl_v = QLabel("0")
            lbl_v.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;")
            col.addWidget(lbl_h); col.addWidget(lbl_v)
            setattr(self, f"lbl_{value}", lbl_v)
            layout.addLayout(col)
            div = QFrame(); div.setFrameShape(QFrame.VLine)
            div.setStyleSheet("color:#EEEEEE;"); layout.addWidget(div)
        layout.addStretch()
        btn_add = QPushButton("  🚛   ADD NEW VEHICLE")
        btn_add.setFixedHeight(62); btn_add.setMinimumWidth(260)
        btn_add.setStyleSheet(f"""QPushButton{{
                background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2980B9,stop:1 #1B4F72);
                color:white;border-radius:12px;border:none;font-size:19px;font-weight:bold;}}
            QPushButton:hover{{background:#3498DB;}}""")
        btn_add.clicked.connect(self._add_truck); layout.addWidget(btn_add)
        return frame

    def _make_footer(self):
        frame = QFrame()
        frame.setStyleSheet(f"background:{config.DARK};border-top:4px solid {config.BLUE};")
        frame.setFixedHeight(60)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)
        lbl = QLabel("Click any vehicle card to open its records")
        lbl.setStyleSheet("color:#AAAAAA;font-size:14px;"); layout.addWidget(lbl)
        layout.addStretch()
        self.lbl_footer = QLabel("")
        self.lbl_footer.setStyleSheet(f"color:{config.BLUE};font-size:14px;font-weight:bold;")
        layout.addWidget(self.lbl_footer); return frame

    def refresh_fleet(self):
        while self.fleet_layout.count():
            item = self.fleet_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        trucks = database.fleet_get_all()
        total  = database.fleet_grand_total()
        dumpers = [t for t in trucks if t["truck_type"] == "Dumper"]
        loaders = [t for t in trucks if t["truck_type"] == "Loader"]
        self.lbl_dumpers.setText(str(len(dumpers)))
        self.lbl_loaders.setText(str(len(loaders)))
        self.lbl_total.setText(f"PKR {total:,.0f}")
        self.lbl_footer.setText(f"{len(trucks)} vehicles  •  PKR {total:,.2f} total")
        if not trucks:
            empty = QLabel("No vehicles registered yet.\nClick  🚛 ADD NEW VEHICLE  to get started.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color:#AAAAAA;font-size:18px;padding:60px;")
            self.fleet_layout.addWidget(empty, 0, 0, 1, 4)
        else:
            for i, truck in enumerate(trucks):
                card = self._make_truck_card(truck)
                self.fleet_layout.addWidget(card, i // 4, i % 4)
        for c in range(4):
            self.fleet_layout.setColumnStretch(c, 1)
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()

    def _make_truck_card(self, truck):
        is_loader = truck["truck_type"] == "Loader"
        color     = "#0E6655" if is_loader else config.BLUE
        if is_loader:
            total_cash   = database.loader_total_cash(truck["id"])
            total_diesel = database.loader_total_diesel(truck["id"])
            total_days   = database.loader_total_days(truck["id"])
            stat1_l, stat1_v = "DAYS WORKED", f"{total_days:.1f}"
            stat2_l, stat2_v = "CASH PAID",   f"PKR {total_cash:,.0f}"
            stat3_l, stat3_v = "DIESEL PAID", f"PKR {total_diesel:,.0f}"
        else:
            total_paid    = database.truck_total_payment(truck["id"])
            total_balance = database.truck_total_balance(truck["id"])
            entry_count   = len(database.truck_entries_get(truck["id"]))
            stat1_l, stat1_v = "TOTAL PAID",    f"PKR {total_paid:,.0f}"
            stat2_l, stat2_v = "BALANCE DUE",   f"PKR {total_balance:,.0f}"
            stat3_l, stat3_v = "ENTRIES",        str(entry_count)

        frame = QFrame()
        frame.setStyleSheet(f"""QFrame{{background:white;border-radius:14px;border:2px solid #DDDDDD;}}
            QFrame:hover{{border:2px solid {color};background:#F5F8FF;}}""")
        frame.setMinimumHeight(240); frame.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16); layout.setSpacing(8)
        bar = QFrame(); bar.setFixedHeight(5)
        bar.setStyleSheet(f"background:{color};border-radius:3px;border:none;")
        layout.addWidget(bar)
        reg_row = QHBoxLayout()
        icon_map = {"Dumper": "🚚", "Loader": "🏗"}
        lbl_icon = QLabel(icon_map.get(truck["truck_type"], "🚛"))
        lbl_icon.setStyleSheet("font-size:26px;border:none;")
        reg_row.addWidget(lbl_icon); reg_row.addSpacing(6)
        lbl_reg = QLabel(truck["reg_number"])
        lbl_reg.setStyleSheet(f"color:{color};font-size:19px;font-weight:bold;border:none;")
        reg_row.addWidget(lbl_reg); reg_row.addStretch()
        lbl_type = QLabel(truck["truck_type"])
        lbl_type.setStyleSheet(
            f"background:#EBF5FB;color:{color};border-radius:4px;"
            f"padding:3px 10px;font-size:11px;font-weight:bold;border:none;")
        reg_row.addWidget(lbl_type); layout.addLayout(reg_row)
        lbl_owner = QLabel(f"👤  {truck['owner_name']}")
        lbl_owner.setStyleSheet("color:#444;font-size:15px;font-weight:bold;border:none;")
        layout.addWidget(lbl_owner)
        if truck["notes"]:
            lbl_n = QLabel(truck["notes"])
            lbl_n.setStyleSheet("color:#AAAAAA;font-size:12px;border:none;")
            layout.addWidget(lbl_n)
        layout.addStretch()
        stats = QHBoxLayout()
        for lh, lv in [(stat1_l, stat1_v), (stat2_l, stat2_v), (stat3_l, stat3_v)]:
            col = QVBoxLayout(); col.setSpacing(1)
            h = QLabel(lh); h.setStyleSheet("font-size:9px;color:#AAAAAA;font-weight:bold;border:none;")
            v = QLabel(lv); v.setStyleSheet(f"color:{color};font-size:13px;font-weight:bold;border:none;")
            col.addWidget(h); col.addWidget(v); stats.addLayout(col); stats.addStretch()
        layout.addLayout(stats); layout.addSpacing(4)
        truck_id = truck["id"]
        btn_open = QPushButton("Open Records  →")
        btn_open.setStyleSheet(f"""QPushButton{{
                background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3498DB,stop:1 #1B4F72);
                color:white;border-radius:8px;border:none;font-size:14px;font-weight:bold;padding:10px;}}
            QPushButton:hover{{background:{color};}}""")
        btn_open.setMinimumHeight(42)
        btn_open.clicked.connect(lambda _, tid=truck_id, t=truck["truck_type"]: self._open_truck(tid, t))
        layout.addWidget(btn_open)
        btns = QHBoxLayout(); btns.setSpacing(8)
        btn_e = QPushButton("✏  Edit")
        btn_e.setMinimumHeight(34)
        btn_e.setStyleSheet("QPushButton{background:#EEE;color:#333;border-radius:6px;border:none;font-size:12px;font-weight:bold;}QPushButton:hover{background:#DDD;}")
        btn_e.clicked.connect(lambda _, tid=truck_id: self._edit_truck(tid))
        btn_d = QPushButton("✕  Remove")
        btn_d.setMinimumHeight(34)
        btn_d.setStyleSheet("QPushButton{background:#FDEDEC;color:#C0392B;border-radius:6px;border:none;font-size:12px;font-weight:bold;}QPushButton:hover{background:#FADBD8;}")
        btn_d.clicked.connect(lambda _, tid=truck_id: self._delete_truck(tid))
        btns.addWidget(btn_e); btns.addWidget(btn_d); layout.addLayout(btns)
        return frame

    def _add_truck(self):
        dlg = TruckFleetDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted: self.refresh_fleet()

    def _edit_truck(self, truck_id):
        row = database.fleet_get_by_id(truck_id)
        if row:
            dlg = TruckFleetDialog(row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted: self.refresh_fleet()

    def _delete_truck(self, truck_id):
        truck = database.fleet_get_by_id(truck_id)
        if not truck: return
        reply = QMessageBox.question(self, "Remove Vehicle",
            f"Remove {truck['reg_number']} from the fleet?\nAll records will be deleted.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.fleet_delete(truck_id)
            # Also delete loader entries
            conn = database.get_connection()
            conn.execute("DELETE FROM loader_entries WHERE truck_id=?", (truck_id,))
            conn.commit(); conn.close()
            self.refresh_fleet()

    def _open_truck(self, truck_id, truck_type):
        truck = database.fleet_get_by_id(truck_id)
        if not truck: return
        if truck_type == "Loader":
            self._ledger_win = LoaderLedger(truck=truck, parent_fleet=self)
        else:
            self._ledger_win = DumperLedger(truck=truck, parent_fleet=self)
        self._ledger_win.showMaximized()
        self.hide()

    def _go_back(self):
        if self.parent_dashboard:
            self.parent_dashboard.refresh_totals()
            self.parent_dashboard.showMaximized()
        self.close()


# ══════════════════════════════════════════════════════════════
#  DUMPER LEDGER
# ══════════════════════════════════════════════════════════════
class DumperLedger(QMainWindow):
    """Per-dumper records: trips, cash paid, diesel paid, balance."""
    def __init__(self, truck, parent_fleet=None):
        super().__init__()
        self.truck = truck; self.parent_fleet = parent_fleet
        self.setWindowTitle(f"Last Hammer  —  🚚 {truck['reg_number']}  ({truck['owner_name']})")
        self.setMinimumSize(1280, 800)
        self._build_ui(); self.refresh_table()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._hdr()); root.addWidget(self._toolbar())
        root.addWidget(self._table_area(), 1); root.addWidget(self._footer())

    def _hdr(self):
        frame = QFrame(); frame.setStyleSheet(f"background:{config.DARK};"); frame.setFixedHeight(90)
        layout = QHBoxLayout(frame); layout.setContentsMargins(30,0,30,0)
        if os.path.exists(config.LOGO_PATH):
            l = QLabel(); l.setPixmap(QPixmap(config.LOGO_PATH).scaled(64,64,Qt.KeepAspectRatio,Qt.SmoothTransformation)); layout.addWidget(l); layout.addSpacing(12)
        accent = QFrame(); accent.setFixedWidth(6); accent.setFixedHeight(52)
        accent.setStyleSheet(f"background:{config.BLUE};border-radius:3px;"); layout.addWidget(accent); layout.addSpacing(14)
        vbox = QVBoxLayout(); vbox.setSpacing(2)
        vbox.addWidget(QLabel(f"🚚  {self.truck['reg_number']}  —  Dumper")  )
        vbox.children()[0] if False else None
        lbl1 = QLabel(f"🚚  {self.truck['reg_number']}  —  Dumper")
        lbl1.setStyleSheet("color:white;font-size:22px;font-weight:bold;")
        lbl2 = QLabel(f"👤  {self.truck['owner_name']}" + (f"   •   {self.truck['notes']}" if self.truck["notes"] else ""))
        lbl2.setStyleSheet("color:#AAAAAA;font-size:13px;")
        # rebuild vbox properly
        vbox2 = QVBoxLayout(); vbox2.setSpacing(2); vbox2.addWidget(lbl1); vbox2.addWidget(lbl2)
        layout.addLayout(vbox2); layout.addStretch()
        btn = QPushButton("←  Back to Fleet"); btn.setFixedHeight(44); btn.setMinimumWidth(180)
        btn.setStyleSheet("QPushButton{background:#444455;color:white;border-radius:8px;border:none;font-size:14px;font-weight:bold;padding:0 20px;}QPushButton:hover{background:#6666AA;}")
        btn.clicked.connect(self._go_back); layout.addWidget(btn)
        return frame

    def _toolbar(self):
        frame = QFrame(); frame.setStyleSheet("background:white;border-bottom:2px solid #DDDDDD;"); frame.setFixedHeight(90)
        layout = QHBoxLayout(frame); layout.setContentsMargins(30,0,30,0); layout.setSpacing(20)
        date_col = QVBoxLayout(); date_col.setSpacing(3)
        date_col.addWidget(self._hint_lbl("DATE FOR NEW ENTRIES"))
        self.date_edit = QDateEdit(); self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True); self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(46); self.date_edit.setFixedWidth(210)
        self.date_edit.setStyleSheet("font-size:16px;font-weight:bold;padding:6px 12px;border:2px solid #DDDDDD;border-radius:8px;")
        date_col.addWidget(self.date_edit); layout.addLayout(date_col)
        div = QFrame(); div.setFrameShape(QFrame.VLine); div.setStyleSheet("color:#EEE;"); layout.addWidget(div)
        t_col = QVBoxLayout(); t_col.setSpacing(3)
        t_col.addWidget(self._hint_lbl("TOTAL PAID"))
        self.lbl_total = QLabel("PKR 0"); self.lbl_total.setStyleSheet(f"color:{config.BLUE};font-size:24px;font-weight:bold;")
        t_col.addWidget(self.lbl_total); layout.addLayout(t_col)
        div2 = QFrame(); div2.setFrameShape(QFrame.VLine); div2.setStyleSheet("color:#EEE;"); layout.addWidget(div2)
        b_col = QVBoxLayout(); b_col.setSpacing(3)
        b_col.addWidget(self._hint_lbl("BALANCE DUE"))
        self.lbl_bal = QLabel("PKR 0"); self.lbl_bal.setStyleSheet(f"color:{config.RED};font-size:24px;font-weight:bold;")
        b_col.addWidget(self.lbl_bal); layout.addLayout(b_col)
        layout.addStretch()
        btn = QPushButton("  ＋   ADD NEW ENTRY"); btn.setFixedHeight(62); btn.setMinimumWidth(260)
        btn.setStyleSheet(f"""QPushButton{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2ECC71,stop:1 #1E8449);
            color:white;border-radius:12px;border:none;font-size:19px;font-weight:bold;}}
            QPushButton:hover{{background:#27AE60;}}""")
        btn.clicked.connect(self._on_add); layout.addWidget(btn)
        return frame

    def _hint_lbl(self, t):
        l = QLabel(t); l.setStyleSheet("font-size:10px;font-weight:bold;color:#AAAAAA;letter-spacing:1px;"); return l

    def _table_area(self):
        frame = QWidget(); frame.setStyleSheet("background:#EFEFEF;")
        layout = QVBoxLayout(frame); layout.setContentsMargins(24,18,24,18)
        cols = ["S.No","Date","Details","Trips","Paid Cash","Paid Diesel","Total Paid","Balance Due","Actions"]
        self.table = QTableWidget(); self.table.setColumnCount(len(cols)); self.table.setHorizontalHeaderLabels(cols)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Arial",13)); hf = QFont("Arial",12); hf.setBold(True)
        self.table.horizontalHeader().setFont(hf); self.table.horizontalHeader().setMinimumHeight(46)
        self.table.setColumnWidth(0,60); self.table.setColumnWidth(1,130); self.table.setColumnWidth(3,70); self.table.setColumnWidth(8,240)
        for i in [2,4,5,6,7]: self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.table.setStyleSheet("""QTableWidget{background:white;alternate-background-color:#F0F4FF;
            gridline-color:#E0E0E0;border:1px solid #CCC;border-radius:10px;font-size:13px;}
            QTableWidget::item{padding:8px 12px;}QTableWidget::item:selected{background:#D6EAF8;color:#1A1A2E;}
            QHeaderView::section{background:#1A1A2E;color:white;font-size:12px;font-weight:bold;
            padding:10px 8px;border:none;border-right:1px solid #2C2C4E;}""")
        layout.addWidget(self.table); return frame

    def _footer(self):
        frame = QFrame(); frame.setStyleSheet(f"background:{config.DARK};border-top:4px solid {config.BLUE};"); frame.setFixedHeight(60)
        layout = QHBoxLayout(frame); layout.setContentsMargins(30,0,30,0)
        self.lbl_footer = QLabel(f"All records — {self.truck['reg_number']}")
        self.lbl_footer.setStyleSheet(f"color:{config.BLUE};font-size:16px;font-weight:bold;"); layout.addWidget(self.lbl_footer)
        layout.addStretch(); hint = QLabel("All fields optional except Reg No")
        hint.setStyleSheet("color:#888;font-size:13px;"); layout.addWidget(hint); return frame

    def refresh_table(self):
        rows = database.truck_entries_get(self.truck["id"])
        total = database.truck_total_payment(self.truck["id"])
        bal   = database.truck_total_balance(self.truck["id"])
        self.lbl_total.setText(f"PKR {total:,.0f}")
        self.lbl_bal.setText(f"PKR {bal:,.0f}")
        self.lbl_bal.setStyleSheet(f"color:{config.RED if bal>0 else config.GREEN};font-size:24px;font-weight:bold;")
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            ri = self.table.rowCount(); self.table.insertRow(ri)
            pc = float((row["paid_cash"] if "paid_cash" in row.keys() else None) or 0)
            pd_ = float((row["paid_diesel"] if "paid_diesel" in row.keys() else None) or 0)
            tp  = float((row["payment"] if "payment" in row.keys() else None) or (pc+pd_))
            bd  = float((row["balance_due"] if "balance_due" in row.keys() else None) or 0)
            cells = [str(i+1), row["date"], (row["details"] if "details" in row.keys() else None) or "—",
                     str((row["trips"] if "trips" in row.keys() else None) or (row["total_trips"] if "total_trips" in row.keys() else None) or "—"),
                     f"PKR {pc:,.0f}" if pc else "—",
                     f"PKR {pd_:,.0f}" if pd_ else "—",
                     f"PKR {tp:,.2f}", f"PKR {bd:,.2f}"]
            for j, val in enumerate(cells):
                item = QTableWidgetItem(val); item.setTextAlignment(Qt.AlignCenter)
                if j == 1: item.setForeground(QColor("#1B4F72")); item.setFont(QFont("Arial",12,QFont.Bold))
                if j == 6: item.setForeground(QColor(config.GREEN)); item.setFont(QFont("Arial",12,QFont.Bold))
                if j == 7: item.setForeground(QColor(config.RED if bd>0 else config.GREEN))
                self.table.setItem(ri, j, item)
            aw = QWidget(); al = QHBoxLayout(aw); al.setContentsMargins(8,6,8,6); al.setSpacing(8)
            eid = row["id"]
            for txt, col_, fn in [("✏ Edit", "#2980B9", lambda _,e=eid: self._on_edit(e)),
                                   ("✕ Delete", "#C0392B", lambda _,e=eid: self._on_del(e))]:
                b = QPushButton(txt); b.setMinimumHeight(40); b.setMinimumWidth(90)
                b.setStyleSheet(f"QPushButton{{background:{col_};color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}}QPushButton:hover{{opacity:0.8;}}")
                b.clicked.connect(fn); al.addWidget(b)
            self.table.setCellWidget(ri, 8, aw); self.table.setRowHeight(ri, 60)
        if self.parent_fleet: self.parent_fleet.refresh_fleet()

    def _on_add(self):
        dlg = DumperEntryDialog(self.truck, self.date_edit.date().toString("yyyy-MM-dd"), parent=self)
        if dlg.exec_() == QDialog.Accepted: self.refresh_table()

    def _on_edit(self, eid):
        row = database.truck_entries_get_by_id(eid)
        if row:
            dlg = DumperEntryDialog(self.truck, row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted: self.refresh_table()

    def _on_del(self, eid):
        if QMessageBox.question(self,"Delete","Delete this entry?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No) == QMessageBox.Yes:
            database.truck_entries_delete(eid); self.refresh_table()

    def _go_back(self):
        if self.parent_fleet: self.parent_fleet.refresh_fleet(); self.parent_fleet.showMaximized()
        self.close()


# ══════════════════════════════════════════════════════════════
#  LOADER LEDGER
# ══════════════════════════════════════════════════════════════
class LoaderLedger(QMainWindow):
    """Per-loader: days worked + cash/diesel payments with dates."""
    def __init__(self, truck, parent_fleet=None):
        super().__init__()
        self.truck = truck; self.parent_fleet = parent_fleet
        self.setWindowTitle(f"Last Hammer  —  🏗 {truck['reg_number']}  ({truck['owner_name']})")
        self.setMinimumSize(1280, 800)
        self._build_ui(); self.refresh_table()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._hdr()); root.addWidget(self._toolbar())
        root.addWidget(self._table_area(), 1); root.addWidget(self._footer())

    def _hdr(self):
        frame = QFrame(); frame.setStyleSheet(f"background:{config.DARK};"); frame.setFixedHeight(90)
        layout = QHBoxLayout(frame); layout.setContentsMargins(30,0,30,0)
        if os.path.exists(config.LOGO_PATH):
            l = QLabel(); l.setPixmap(QPixmap(config.LOGO_PATH).scaled(64,64,Qt.KeepAspectRatio,Qt.SmoothTransformation)); layout.addWidget(l); layout.addSpacing(12)
        accent = QFrame(); accent.setFixedWidth(6); accent.setFixedHeight(52)
        accent.setStyleSheet("background:#0E6655;border-radius:3px;"); layout.addWidget(accent); layout.addSpacing(14)
        lbl1 = QLabel(f"🏗  {self.truck['reg_number']}  —  Loader")
        lbl1.setStyleSheet("color:white;font-size:22px;font-weight:bold;")
        lbl2 = QLabel(f"👤  {self.truck['owner_name']}" + (f"   •   {self.truck['notes']}" if self.truck["notes"] else ""))
        lbl2.setStyleSheet("color:#AAAAAA;font-size:13px;")
        vbox = QVBoxLayout(); vbox.setSpacing(2); vbox.addWidget(lbl1); vbox.addWidget(lbl2)
        layout.addLayout(vbox); layout.addStretch()
        btn = QPushButton("←  Back to Fleet"); btn.setFixedHeight(44); btn.setMinimumWidth(180)
        btn.setStyleSheet("QPushButton{background:#444455;color:white;border-radius:8px;border:none;font-size:14px;font-weight:bold;padding:0 20px;}QPushButton:hover{background:#6666AA;}")
        btn.clicked.connect(self._go_back); layout.addWidget(btn); return frame

    def _toolbar(self):
        frame = QFrame(); frame.setStyleSheet("background:white;border-bottom:2px solid #DDDDDD;"); frame.setFixedHeight(90)
        layout = QHBoxLayout(frame); layout.setContentsMargins(30,0,30,0); layout.setSpacing(20)
        self.date_edit = QDateEdit(); self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True); self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(46); self.date_edit.setFixedWidth(210)
        self.date_edit.setStyleSheet("font-size:16px;font-weight:bold;padding:6px 12px;border:2px solid #DDDDDD;border-radius:8px;")
        d_col = QVBoxLayout(); d_col.setSpacing(3)
        d_col.addWidget(self._hint("DATE FOR NEW ENTRIES")); d_col.addWidget(self.date_edit)
        layout.addLayout(d_col)
        div = QFrame(); div.setFrameShape(QFrame.VLine); div.setStyleSheet("color:#EEE;"); layout.addWidget(div)
        for attr, hint, color in [("lbl_days","TOTAL DAYS WORKED","#0E6655"),("lbl_cash","TOTAL CASH PAID",config.BLUE),("lbl_diesel","TOTAL DIESEL PAID",config.ORANGE)]:
            col = QVBoxLayout(); col.setSpacing(3); col.addWidget(self._hint(hint))
            lbl = QLabel("0"); lbl.setStyleSheet(f"color:{color};font-size:20px;font-weight:bold;")
            col.addWidget(lbl); setattr(self, attr, lbl); layout.addLayout(col)
            div2 = QFrame(); div2.setFrameShape(QFrame.VLine); div2.setStyleSheet("color:#EEE;"); layout.addWidget(div2)
        layout.addStretch()
        btn = QPushButton("  ＋   ADD ENTRY"); btn.setFixedHeight(62); btn.setMinimumWidth(220)
        btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2ECC71,stop:1 #1E8449);color:white;border-radius:12px;border:none;font-size:18px;font-weight:bold;}QPushButton:hover{background:#27AE60;}")
        btn.clicked.connect(self._on_add); layout.addWidget(btn); return frame

    def _hint(self, t):
        l = QLabel(t); l.setStyleSheet("font-size:10px;font-weight:bold;color:#AAAAAA;letter-spacing:1px;"); return l

    def _table_area(self):
        frame = QWidget(); frame.setStyleSheet("background:#EFEFEF;")
        layout = QVBoxLayout(frame); layout.setContentsMargins(24,18,24,18)
        cols = ["S.No","Date","Type","Description","Days Worked","Cash Paid","Diesel (PKR)","Actions"]
        self.table = QTableWidget(); self.table.setColumnCount(len(cols)); self.table.setHorizontalHeaderLabels(cols)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Arial",13)); hf = QFont("Arial",12); hf.setBold(True)
        self.table.horizontalHeader().setFont(hf); self.table.horizontalHeader().setMinimumHeight(46)
        self.table.setColumnWidth(0,60); self.table.setColumnWidth(1,130); self.table.setColumnWidth(2,110); self.table.setColumnWidth(4,110); self.table.setColumnWidth(7,230)
        for i in [3,5,6]: self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.table.setStyleSheet("""QTableWidget{background:white;alternate-background-color:#F0F4FF;
            gridline-color:#E0E0E0;border:1px solid #CCC;border-radius:10px;font-size:13px;}
            QTableWidget::item{padding:8px 10px;}QTableWidget::item:selected{background:#D6EAF8;color:#1A1A2E;}
            QHeaderView::section{background:#1A1A2E;color:white;font-size:12px;font-weight:bold;padding:10px 8px;border:none;border-right:1px solid #2C2C4E;}""")
        layout.addWidget(self.table); return frame

    def _footer(self):
        frame = QFrame(); frame.setStyleSheet("background:#1A1A2E;border-top:4px solid #0E6655;"); frame.setFixedHeight(60)
        layout = QHBoxLayout(frame); layout.setContentsMargins(30,0,30,0)
        self.lbl_footer = QLabel(f"All records — {self.truck['reg_number']}")
        self.lbl_footer.setStyleSheet("color:#0E6655;font-size:16px;font-weight:bold;"); layout.addWidget(self.lbl_footer)
        layout.addStretch(); hint = QLabel("Work entries, cash payments, and diesel payments tracked separately")
        hint.setStyleSheet("color:#888;font-size:12px;"); layout.addWidget(hint); return frame

    def refresh_table(self):
        rows    = database.loader_entries_get(self.truck["id"])
        t_cash  = database.loader_total_cash(self.truck["id"])
        t_diesel= database.loader_total_diesel(self.truck["id"])
        t_days  = database.loader_total_days(self.truck["id"])
        self.lbl_days.setText(f"{t_days:.1f} days")
        self.lbl_cash.setText(f"PKR {t_cash:,.0f}")
        self.lbl_diesel.setText(f"PKR {t_diesel:,.0f}")
        TYPE_COLORS = {"Work": "#0E6655", "Cash Payment": config.BLUE, "Diesel Payment": config.ORANGE}
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            ri = self.table.rowCount(); self.table.insertRow(ri)
            rtype = (row["entry_type"] if "entry_type" in row.keys() else "Work")
            col_ = TYPE_COLORS.get(rtype, config.DARK)
            cells = [str(i+1), row["date"], rtype, (row["description"] if "description" in row.keys() else None) or "—",
                     f"{float(row['days_worked']):.1f}" if ("days_worked" in row.keys() and row["days_worked"]) else "—",
                     f"PKR {float(row['cash_paid']):,.0f}" if ("cash_paid" in row.keys() and row["cash_paid"]) else "—",
                     f"PKR {float(row['diesel_worth']):,.0f}" if ("diesel_worth" in row.keys() and row["diesel_worth"]) else "—"]
            for j, val in enumerate(cells):
                item = QTableWidgetItem(val); item.setTextAlignment(Qt.AlignCenter)
                if j == 1: item.setForeground(QColor("#1B4F72")); item.setFont(QFont("Arial",12,QFont.Bold))
                if j == 2: item.setForeground(QColor(col_)); item.setFont(QFont("Arial",12,QFont.Bold))
                self.table.setItem(ri, j, item)
            aw = QWidget(); al = QHBoxLayout(aw); al.setContentsMargins(8,6,8,6); al.setSpacing(8)
            eid = row["id"]
            for txt, c, fn in [("✏ Edit","#2980B9",lambda _,e=eid:self._on_edit(e)),
                                ("✕ Delete","#C0392B",lambda _,e=eid:self._on_del(e))]:
                b = QPushButton(txt); b.setMinimumHeight(40); b.setMinimumWidth(90)
                b.setStyleSheet(f"QPushButton{{background:{c};color:white;border-radius:7px;border:none;font-size:13px;font-weight:bold;}}QPushButton:hover{{opacity:.8;}}")
                b.clicked.connect(fn); al.addWidget(b)
            self.table.setCellWidget(ri, 7, aw); self.table.setRowHeight(ri, 58)
        if self.parent_fleet: self.parent_fleet.refresh_fleet()

    def _on_add(self):
        dlg = LoaderEntryDialog(self.truck, self.date_edit.date().toString("yyyy-MM-dd"), parent=self)
        if dlg.exec_() == QDialog.Accepted: self.refresh_table()

    def _on_edit(self, eid):
        row = database.loader_entries_get_by_id(eid)
        if row:
            dlg = LoaderEntryDialog(self.truck, row=row, parent=self)
            if dlg.exec_() == QDialog.Accepted: self.refresh_table()

    def _on_del(self, eid):
        if QMessageBox.question(self,"Delete","Delete this entry?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No) == QMessageBox.Yes:
            database.loader_entries_delete(eid); self.refresh_table()

    def _go_back(self):
        if self.parent_fleet: self.parent_fleet.refresh_fleet(); self.parent_fleet.showMaximized()
        self.close()


# ══════════════════════════════════════════════════════════════
#  DIALOGS
# ══════════════════════════════════════════════════════════════
class TruckFleetDialog(QDialog):
    def __init__(self, row=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit Vehicle" if row else "Register New Vehicle")
        self.setFixedWidth(460); self.setModal(True)
        self._build_ui()
        if row: self._populate(row)

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(18); layout.setContentsMargins(28,28,28,28)
        lbl = QLabel("Register New Vehicle" if not self.row else "Edit Vehicle Details")
        lbl.setStyleSheet(f"font-size:16px;font-weight:bold;color:{config.DARK};"); layout.addWidget(lbl)
        form = QFormLayout(); form.setSpacing(13); form.setLabelAlignment(Qt.AlignRight)
        def L(t): l=QLabel(t); l.setStyleSheet("font-size:14px;font-weight:bold;"); return l
        def inp(ph=""): f=QLineEdit(); f.setPlaceholderText(ph); f.setMinimumHeight(44); f.setStyleSheet("font-size:14px;padding:6px 12px;border:2px solid #DDDDDD;border-radius:8px;"); return f
        self.inp_reg   = inp("e.g. LEA-2341");  form.addRow(L("Reg. Number:"), self.inp_reg)
        self.inp_owner = inp("Owner/driver name"); form.addRow(L("Owner Name:"), self.inp_owner)
        self.inp_type  = QComboBox(); self.inp_type.addItems(TRUCK_TYPES)
        self.inp_type.setMinimumHeight(44); self.inp_type.setStyleSheet("font-size:14px;padding:6px 12px;border:2px solid #DDDDDD;border-radius:8px;background:white;")
        form.addRow(L("Type:"), self.inp_type)
        self.inp_notes = inp("Optional notes (e.g. 10-wheel, blue cab)"); form.addRow(L("Notes:"), self.inp_notes)
        layout.addLayout(form)
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        btn_c = QPushButton("Cancel"); btn_c.setMinimumHeight(46)
        btn_c.setStyleSheet("QPushButton{background:#555;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#888;}")
        btn_c.clicked.connect(self.reject)
        btn_s = QPushButton("💾  Save Vehicle"); btn_s.setMinimumHeight(46); btn_s.setMinimumWidth(180)
        btn_s.setStyleSheet("QPushButton{background:#1B4F72;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#2980B9;}")
        btn_s.clicked.connect(self._save)
        btn_row.addWidget(btn_c); btn_row.addStretch(); btn_row.addWidget(btn_s); layout.addLayout(btn_row)

    def _populate(self, row):
        self.inp_reg.setText(row["reg_number"]); self.inp_owner.setText(row["owner_name"])
        idx = self.inp_type.findText(row["truck_type"])
        if idx >= 0: self.inp_type.setCurrentIndex(idx)
        self.inp_notes.setText(row["notes"] or "")

    def _save(self):
        reg = self.inp_reg.text().strip().upper(); owner = self.inp_owner.text().strip()
        if not reg: QMessageBox.warning(self,"Missing","Enter registration number."); return
        if not owner: QMessageBox.warning(self,"Missing","Enter owner name."); return
        try:
            if self.row: database.fleet_edit(self.row["id"], reg, owner, self.inp_type.currentText(), self.inp_notes.text().strip())
            else:        database.fleet_add(reg, owner, self.inp_type.currentText(), self.inp_notes.text().strip())
            self.accept()
        except Exception as e:
            if "UNIQUE" in str(e): QMessageBox.warning(self,"Duplicate",f"{reg} already registered.")
            else: QMessageBox.critical(self,"Error",str(e))


class DumperEntryDialog(QDialog):
    def __init__(self, truck, date_str=None, row=None, parent=None):
        super().__init__(parent)
        self.truck = truck; self.row = row
        self.setWindowTitle(f"{'Edit' if row else 'Add'} Entry — {truck['reg_number']}")
        self.setFixedWidth(480); self.setModal(True)
        self._build_ui(date_str or (row["date"] if row else None))
        if row: self._populate(row)

    def _build_ui(self, date_str):
        layout = QVBoxLayout(self); layout.setSpacing(14); layout.setContentsMargins(28,24,28,24)
        lbl = QLabel(f"🚚  {self.truck['reg_number']}  —  {self.truck['owner_name']}\n{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(f"font-size:15px;font-weight:bold;color:{config.DARK};"); layout.addWidget(lbl)
        info = QLabel("All fields are optional — only fill in what applies.")
        info.setStyleSheet("background:#EBF5FB;color:#1B4F72;border-radius:8px;padding:8px 12px;font-size:12px;")
        layout.addWidget(info)
        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)
        def L(t): l=QLabel(t); l.setStyleSheet("font-size:13px;font-weight:bold;"); return l
        def spin(max_=9999999, dec=2, pre="PKR ", suf=""):
            s=QDoubleSpinBox(); s.setRange(0,max_); s.setDecimals(dec)
            if pre: s.setPrefix(pre)
            if suf: s.setSuffix(suf)
            s.setMinimumHeight(42); s.setStyleSheet("font-size:13px;padding:4px 8px;border:2px solid #DDD;border-radius:8px;"); return s
        self.inp_date = QDateEdit()
        d = QDate.fromString(date_str,"yyyy-MM-dd") if date_str else QDate.currentDate()
        self.inp_date.setDate(d if d.isValid() else QDate.currentDate())
        self.inp_date.setCalendarPopup(True); self.inp_date.setDisplayFormat("dd/MM/yyyy"); self.inp_date.setMinimumHeight(42)
        self.inp_date.setStyleSheet("font-size:14px;font-weight:bold;padding:6px 12px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Date:"), self.inp_date)
        self.inp_details = QLineEdit(); self.inp_details.setPlaceholderText("e.g. Marble transport — East pit (optional)")
        self.inp_details.setMinimumHeight(42); self.inp_details.setStyleSheet("font-size:13px;padding:6px 12px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Details:"), self.inp_details)
        self.inp_trips = QSpinBox(); self.inp_trips.setRange(0,9999); self.inp_trips.setSuffix(" trips")
        self.inp_trips.setMinimumHeight(42); self.inp_trips.setStyleSheet("font-size:13px;padding:4px 8px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Trips Made:"), self.inp_trips)
        self.inp_cash   = spin(); form.addRow(L("Paid in Cash:"), self.inp_cash)
        self.inp_diesel = spin(); form.addRow(L("Paid in Diesel\n(PKR value):"), self.inp_diesel)
        self.inp_balance= spin()
        lbl_b = L("Balance Due:"); lbl_b.setStyleSheet("font-size:13px;font-weight:bold;color:#C0392B;")
        form.addRow(lbl_b, self.inp_balance)
        layout.addLayout(form)
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        btn_c = QPushButton("Cancel"); btn_c.setMinimumHeight(46)
        btn_c.setStyleSheet("QPushButton{background:#555;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#888;}")
        btn_c.clicked.connect(self.reject)
        btn_s = QPushButton("💾  Save Entry"); btn_s.setMinimumHeight(46); btn_s.setMinimumWidth(160)
        btn_s.setStyleSheet("QPushButton{background:#1E8449;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#27AE60;}")
        btn_s.clicked.connect(self._save); btn_row.addWidget(btn_c); btn_row.addStretch(); btn_row.addWidget(btn_s); layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"],"yyyy-MM-dd")
        if d.isValid(): self.inp_date.setDate(d)
        self.inp_details.setText((row["details"] if "details" in row.keys() else None) or "")
        self.inp_trips.setValue(int((row["trips"] if "trips" in row.keys() else None) or (row["total_trips"] if "total_trips" in row.keys() else None) or 0))
        self.inp_cash.setValue(float((row["paid_cash"] if "paid_cash" in row.keys() else None) or 0))
        self.inp_diesel.setValue(float((row["paid_diesel"] if "paid_diesel" in row.keys() else None) or 0))
        self.inp_balance.setValue(float((row["balance_due"] if "balance_due" in row.keys() else None) or 0))

    def _save(self):
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        pc = self.inp_cash.value(); pd_ = self.inp_diesel.value()
        total = pc + pd_
        conn = database.get_connection()
        if self.row:
            conn.execute(
                "UPDATE truck_entries SET date=?,details=?,trips=?,payment=?,paid_cash=?,paid_diesel=?,balance_due=? WHERE id=?",
                (date_str, self.inp_details.text().strip(), self.inp_trips.value(),
                 total, pc, pd_, self.inp_balance.value(), self.row["id"]))
        else:
            conn.execute(
                "INSERT INTO truck_entries (truck_id,date,details,trips,payment,paid_cash,paid_diesel,balance_due) VALUES (?,?,?,?,?,?,?,?)",
                (self.truck["id"], date_str, self.inp_details.text().strip(),
                 self.inp_trips.value(), total, pc, pd_, self.inp_balance.value()))
        conn.commit(); conn.close(); self.accept()


class LoaderEntryDialog(QDialog):
    def __init__(self, truck, date_str=None, row=None, parent=None):
        super().__init__(parent)
        self.truck = truck; self.row = row
        self.setWindowTitle(f"{'Edit' if row else 'Add'} Entry — {truck['reg_number']}")
        self.setFixedWidth(480); self.setModal(True)
        self._build_ui(date_str or (row["date"] if row else None))
        if row: self._populate(row)

    def _build_ui(self, date_str):
        layout = QVBoxLayout(self); layout.setSpacing(14); layout.setContentsMargins(28,24,28,24)
        lbl = QLabel(f"🏗  {self.truck['reg_number']}  —  {self.truck['owner_name']}\n{'Edit Entry' if self.row else 'Add New Entry'}")
        lbl.setStyleSheet(f"font-size:15px;font-weight:bold;color:{config.DARK};"); layout.addWidget(lbl)
        info = QLabel("Record each event on its own date: days worked, cash given, or diesel given.\nAll payment fields are optional.")
        info.setStyleSheet("background:#E9F7EF;color:#1E8449;border-radius:8px;padding:8px 12px;font-size:12px;")
        info.setWordWrap(True); layout.addWidget(info)
        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)
        def L(t): l=QLabel(t); l.setStyleSheet("font-size:13px;font-weight:bold;"); return l
        self.inp_date = QDateEdit()
        d = QDate.fromString(date_str,"yyyy-MM-dd") if date_str else QDate.currentDate()
        self.inp_date.setDate(d if d.isValid() else QDate.currentDate())
        self.inp_date.setCalendarPopup(True); self.inp_date.setDisplayFormat("dd/MM/yyyy"); self.inp_date.setMinimumHeight(42)
        self.inp_date.setStyleSheet("font-size:14px;font-weight:bold;padding:6px 12px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Date:"), self.inp_date)
        # Entry type
        self.inp_type = QComboBox()
        self.inp_type.addItems(["Work", "Cash Payment", "Diesel Payment"])
        self.inp_type.setMinimumHeight(42); self.inp_type.setStyleSheet("font-size:13px;padding:4px 8px;border:2px solid #DDD;border-radius:8px;background:white;")
        form.addRow(L("Entry Type:"), self.inp_type)
        self.inp_desc = QLineEdit(); self.inp_desc.setPlaceholderText("Description (optional)")
        self.inp_desc.setMinimumHeight(42); self.inp_desc.setStyleSheet("font-size:13px;padding:6px 12px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Description:"), self.inp_desc)
        self.inp_days = QDoubleSpinBox(); self.inp_days.setRange(0,999); self.inp_days.setDecimals(1); self.inp_days.setSuffix(" days")
        self.inp_days.setMinimumHeight(42); self.inp_days.setStyleSheet("font-size:13px;padding:4px 8px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Days Worked:"), self.inp_days)
        self.inp_cash = QDoubleSpinBox(); self.inp_cash.setRange(0,9999999); self.inp_cash.setDecimals(2); self.inp_cash.setPrefix("PKR ")
        self.inp_cash.setMinimumHeight(42); self.inp_cash.setStyleSheet("font-size:13px;padding:4px 8px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Cash Paid:"), self.inp_cash)
        self.inp_diesel = QDoubleSpinBox(); self.inp_diesel.setRange(0,9999999); self.inp_diesel.setDecimals(2); self.inp_diesel.setPrefix("PKR ")
        self.inp_diesel.setMinimumHeight(42); self.inp_diesel.setStyleSheet("font-size:13px;padding:4px 8px;border:2px solid #DDD;border-radius:8px;")
        form.addRow(L("Diesel (PKR value):"), self.inp_diesel)
        layout.addLayout(form)
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        btn_c = QPushButton("Cancel"); btn_c.setMinimumHeight(46)
        btn_c.setStyleSheet("QPushButton{background:#555;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#888;}")
        btn_c.clicked.connect(self.reject)
        btn_s = QPushButton("💾  Save Entry"); btn_s.setMinimumHeight(46); btn_s.setMinimumWidth(160)
        btn_s.setStyleSheet("QPushButton{background:#0E6655;color:white;border-radius:8px;border:none;font-size:15px;font-weight:bold;}QPushButton:hover{background:#17A589;}")
        btn_s.clicked.connect(self._save); btn_row.addWidget(btn_c); btn_row.addStretch(); btn_row.addWidget(btn_s); layout.addLayout(btn_row)

    def _populate(self, row):
        d = QDate.fromString(row["date"],"yyyy-MM-dd")
        if d.isValid(): self.inp_date.setDate(d)
        idx = self.inp_type.findText((row["entry_type"] if "entry_type" in row.keys() else "Work"))
        if idx >= 0: self.inp_type.setCurrentIndex(idx)
        self.inp_desc.setText((row["description"] if "description" in row.keys() else None) or "")
        self.inp_days.setValue(float((row["days_worked"] if "days_worked" in row.keys() else None) or 0))
        self.inp_cash.setValue(float((row["cash_paid"] if "cash_paid" in row.keys() else None) or 0))
        self.inp_diesel.setValue(float((row["diesel_worth"] if "diesel_worth" in row.keys() else None) or 0))

    def _save(self):
        date_str = self.inp_date.date().toString("yyyy-MM-dd")
        database.loader_entries_add(
            self.truck["id"] if not self.row else None,
            self.inp_type.currentText(), date_str,
            self.inp_desc.text().strip(),
            self.inp_days.value(), self.inp_cash.value(), self.inp_diesel.value()
        ) if not self.row else database.loader_entries_edit(
            self.row["id"], self.inp_type.currentText(), date_str,
            self.inp_desc.text().strip(),
            self.inp_days.value(), self.inp_cash.value(), self.inp_diesel.value()
        )
        self.accept()