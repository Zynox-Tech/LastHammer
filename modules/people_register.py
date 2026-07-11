"""
People Register — Individual Account Ledger
Same pattern as Truck Fleet:
  • Grid of person cards on the main screen
  • Click a card → full ledger for that person
  • Each entry: date, type (Cash Given / Cash Received / Note), description, amount
  • Running balance on every row
  • Export as individual PDF statement
  • Share / email from inside the ledger view
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QDialog, QFormLayout, QLineEdit,
    QDoubleSpinBox, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QScrollArea, QTextEdit, QGridLayout,
    QApplication
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QDate
import database, config

DARK   = config.DARK
BLUE   = "#1B4F72"
GREEN  = "#1E8449"
RED    = "#C0392B"
GOLD   = "#F39C12"
PURPLE = "#6C3483"

CATEGORIES = ["Worker", "Driver", "Contractor", "Partner", "Supplier",
               "Land Owner", "Government", "Other"]

ENTRY_TYPES = ["Cash Given", "Cash Received", "Note"]

TYPE_COLOR = {
    "Cash Given":    RED,
    "Cash Received": GREEN,
    "Note":          "#555555",
}
TYPE_ICON = {
    "Cash Given":    "💸",
    "Cash Received": "💰",
    "Note":          "📝",
}


# ══════════════════════════════════════════════════════════════
#  MAIN: PEOPLE REGISTER (card grid)
# ══════════════════════════════════════════════════════════════
class PeopleRegister(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("People Register — Individual Accounts")
        self.setMinimumSize(1280, 800)
        self._build_ui()
        self.refresh()

    # ── BUILD ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._header())
        root.addWidget(self._toolbar())
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:#EFEFEF;}")
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background:#EFEFEF;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(28, 22, 28, 22)
        self.grid_layout.setSpacing(18)
        self.scroll.setWidget(self.grid_container)
        root.addWidget(self.scroll, 1)
        root.addWidget(self._footer())

    def _header(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {BLUE};")
        f.setFixedHeight(90)
        lay = QHBoxLayout(f); lay.setContentsMargins(30, 0, 30, 0)
        if os.path.exists(config.LOGO_PATH):
            lbl = QLabel()
            lbl.setPixmap(QPixmap(config.LOGO_PATH).scaled(
                64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lay.addWidget(lbl); lay.addSpacing(12)
        accent = QFrame(); accent.setFixedSize(6, 52)
        accent.setStyleSheet(f"background:{BLUE};border-radius:3px;border:none;")
        lay.addWidget(accent); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        vb.addWidget(QLabel("People Register — Individual Accounts",
            styleSheet="color:white;font-size:22px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel(
            "Track cash given, cash received, and notes for every individual — with running balance",
            styleSheet="color:#AAAAAA;font-size:13px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Dashboard")
        btn.setFixedHeight(44); btn.setMinimumWidth(180)
        btn.setStyleSheet(
            "QPushButton{background:#444455;color:white;border-radius:8px;"
            "border:none;font-size:14px;font-weight:bold;}"
            "QPushButton:hover{background:#6666AA;}")
        btn.clicked.connect(self._back)
        lay.addWidget(btn)
        return f

    def _toolbar(self):
        f = QFrame()
        f.setStyleSheet("background:white;border-bottom:2px solid #EEEEEE;")
        f.setFixedHeight(82)
        lay = QHBoxLayout(f); lay.setContentsMargins(30, 0, 30, 0); lay.setSpacing(24)
        for attr, label, color in [
            ("lbl_total_people", "REGISTERED PEOPLE", BLUE),
            ("lbl_total_given",  "TOTAL CASH GIVEN",  RED),
            ("lbl_total_recd",   "TOTAL CASH RECEIVED", GREEN),
        ]:
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(QLabel(label,
                styleSheet="font-size:9px;font-weight:bold;color:#AAAAAA;letter-spacing:1px;border:none;"))
            lv = QLabel("—")
            lv.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;border:none;")
            col.addWidget(lv); setattr(self, attr, lv)
            lay.addLayout(col)
            div = QFrame(); div.setFrameShape(QFrame.VLine)
            div.setStyleSheet("color:#EEEEEE;"); lay.addWidget(div)
        lay.addStretch()
        btn = QPushButton("  👤   ADD NEW PERSON")
        btn.setFixedHeight(62); btn.setMinimumWidth(260)
        btn.setStyleSheet(f"""
            QPushButton{{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #2980B9, stop:1 #1B4F72);
                color:white;border-radius:12px;border:none;
                font-size:19px;font-weight:bold;}}
            QPushButton:hover{{background:#3498DB;}}""")
        btn.clicked.connect(self._add_person)
        lay.addWidget(btn)
        return f

    def _footer(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-top:4px solid {BLUE};")
        f.setFixedHeight(56)
        lay = QHBoxLayout(f); lay.setContentsMargins(30, 0, 30, 0)
        self.lbl_footer = QLabel("Click any person card to open their ledger")
        self.lbl_footer.setStyleSheet("color:#AAAAAA;font-size:14px;border:none;")
        lay.addWidget(self.lbl_footer)
        return f

    # ── REFRESH ────────────────────────────────────────────────────────────────
    def refresh(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        people = database.people_get_all()

        total_given = total_recd = 0
        for p in people:
            g, r, _ = database.people_ledger_summary(p["id"])
            total_given += g; total_recd += r

        self.lbl_total_people.setText(str(len(people)))
        self.lbl_total_given.setText(f"PKR {total_given:,.0f}")
        self.lbl_total_recd.setText(f"PKR {total_recd:,.0f}")
        self.lbl_footer.setText(
            f"{len(people)} people  •  Net: PKR {total_given - total_recd:,.0f}")

        if not people:
            empty = QLabel(
                "No people registered yet.\n\nClick  👤 ADD NEW PERSON  to get started.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color:#AAAAAA;font-size:18px;padding:80px;border:none;")
            self.grid_layout.addWidget(empty, 0, 0, 1, 4)
        else:
            for i, p in enumerate(people):
                card = self._make_card(p)
                self.grid_layout.addWidget(card, i // 4, i % 4)

        for col in range(4):
            self.grid_layout.setColumnStretch(col, 1)

    def _make_card(self, p):
        given, received, net = database.people_ledger_summary(p["id"])
        entries = database.people_ledger_get(p["id"])
        cat     = p["category"] or "Other"

        cat_colors = {
            "Worker": BLUE, "Driver": "#0E6655", "Contractor": PURPLE,
            "Partner": GOLD, "Supplier": "#CA6F1E", "Land Owner": "#2C7873",
        }
        color = cat_colors.get(cat, "#555555")

        # net > 0 → they owe us  (we gave more)
        # net < 0 → we owe them  (they gave more)
        if net > 0:
            bal_label = f"THEY OWE US  PKR {net:,.0f}"
            bal_color = RED
        elif net < 0:
            bal_label = f"WE OWE THEM  PKR {abs(net):,.0f}"
            bal_color = GREEN
        else:
            bal_label = "SETTLED  PKR 0"
            bal_color = "#888888"

        f = QFrame()
        f.setStyleSheet(f"""
            QFrame{{background:white;border-radius:14px;border:2px solid #EEEEEE;}}
            QFrame:hover{{border:2px solid {color};background:#F8FAFF;}}""")
        f.setMinimumHeight(260)
        f.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(18, 16, 18, 16); lay.setSpacing(8)

        # Top accent bar
        bar = QFrame(); bar.setFixedHeight(5)
        bar.setStyleSheet(f"background:{color};border-radius:3px;border:none;")
        lay.addWidget(bar)

        # Name + category badge
        nr = QHBoxLayout()
        nm = QLabel(f"👤  {p['name']}")
        nm.setStyleSheet(
            f"color:{color};font-size:18px;font-weight:bold;border:none;")
        cat_badge = QLabel(cat)
        cat_badge.setStyleSheet(
            f"background:{color}22;color:{color};border-radius:4px;"
            f"padding:3px 10px;font-size:11px;font-weight:bold;border:none;")
        nr.addWidget(nm); nr.addStretch(); nr.addWidget(cat_badge)
        lay.addLayout(nr)

        # Phone
        if p["phone"]:
            lay.addWidget(QLabel(f"📞  {p['phone']}",
                styleSheet="color:#666;font-size:13px;border:none;"))

        # Notes
        if p["notes"]:
            n = QLabel(p["notes"])
            n.setStyleSheet("color:#AAAAAA;font-size:12px;border:none;")
            n.setWordWrap(True)
            lay.addWidget(n)

        lay.addStretch()

        # Stats row
        stats = QHBoxLayout(); stats.setSpacing(0)
        for lbl, val, col in [
            ("GIVEN",    f"PKR {given:,.0f}",    RED),
            ("RECEIVED", f"PKR {received:,.0f}", GREEN),
            ("ENTRIES",  str(len(entries)),       BLUE),
        ]:
            sw = QWidget(); sw.setStyleSheet("background:transparent;border:none;")
            sv = QVBoxLayout(sw); sv.setContentsMargins(0, 0, 12, 0); sv.setSpacing(1)
            sv.addWidget(QLabel(lbl,
                styleSheet=f"font-size:8px;font-weight:bold;color:{col};"
                           "border:none;letter-spacing:1px;"))
            sv.addWidget(QLabel(val,
                styleSheet=f"font-size:12px;font-weight:bold;color:#1A1A2E;border:none;"))
            stats.addWidget(sw)
        stats.addStretch()
        lay.addLayout(stats)

        # Balance badge
        bal = QLabel(bal_label)
        bal.setStyleSheet(
            f"background:{bal_color}15;color:{bal_color};border-radius:6px;"
            f"padding:5px 10px;font-size:11px;font-weight:bold;border:1px solid {bal_color}40;")
        lay.addWidget(bal)

        # Buttons
        btn_open = QPushButton("Open Ledger  →")
        btn_open.setMinimumHeight(42)
        btn_open.setStyleSheet(f"""
            QPushButton{{
                background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3498DB,stop:1 #1B4F72);
                color:white;border-radius:8px;border:none;
                font-size:14px;font-weight:bold;}}
            QPushButton:hover{{background:{color};}}""")
        pid = p["id"]
        btn_open.clicked.connect(lambda _, i=pid: self._open_ledger(i))
        lay.addWidget(btn_open)

        btns2 = QHBoxLayout(); btns2.setSpacing(8)
        btn_e = QPushButton("✏  Edit")
        btn_e.setMinimumHeight(34)
        btn_e.setStyleSheet(
            "QPushButton{background:#EEE;color:#333;border-radius:6px;border:none;"
            "font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#DDD;}")
        btn_e.clicked.connect(lambda _, i=pid: self._edit_person(i))
        btn_d = QPushButton("✕  Remove")
        btn_d.setMinimumHeight(34)
        btn_d.setStyleSheet(
            "QPushButton{background:#FDEDEC;color:#C0392B;border-radius:6px;border:none;"
            "font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#FADBD8;}")
        btn_d.clicked.connect(lambda _, i=pid: self._delete_person(i))
        btns2.addWidget(btn_e); btns2.addWidget(btn_d)
        lay.addLayout(btns2)
        return f

    # ── ACTIONS ────────────────────────────────────────────────────────────────
    def _add_person(self):
        dlg = PersonDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.people_add(d["name"], d["phone"], d["category"], d["notes"])
            self.refresh()

    def _edit_person(self, pid):
        p = database.people_get_by_id(pid)
        if not p: return
        dlg = PersonDialog(row=p, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.people_edit(pid, d["name"], d["phone"], d["category"], d["notes"])
            self.refresh()

    def _delete_person(self, pid):
        p = database.people_get_by_id(pid)
        if not p: return
        if QMessageBox.question(self, "Remove",
                f"Remove {p['name']} and ALL their ledger entries?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            database.people_delete(pid)
            self.refresh()

    def _open_ledger(self, pid):
        p = database.people_get_by_id(pid)
        if not p: return
        self._ledger_win = PersonLedger(person=p, parent_register=self)
        self._ledger_win.showMaximized()
        self.hide()

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()

    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)


# ══════════════════════════════════════════════════════════════
#  PERSON LEDGER (per-person full history)
# ══════════════════════════════════════════════════════════════
class PersonLedger(QMainWindow):
    def __init__(self, person, parent_register=None):
        super().__init__()
        self.person = person
        self.parent_register = parent_register
        self.setWindowTitle(f"People Register  —  {person['name']}")
        self.setMinimumSize(1280, 800)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._header())
        root.addWidget(self._toolbar())
        root.addWidget(self._table_area(), 1)
        root.addWidget(self._footer())

    def _header(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {BLUE};")
        f.setFixedHeight(90)
        lay = QHBoxLayout(f); lay.setContentsMargins(30, 0, 30, 0)
        if os.path.exists(config.LOGO_PATH):
            lbl = QLabel()
            lbl.setPixmap(QPixmap(config.LOGO_PATH).scaled(
                64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lay.addWidget(lbl); lay.addSpacing(12)
        accent = QFrame(); accent.setFixedSize(6, 52)
        accent.setStyleSheet(f"background:{BLUE};border-radius:3px;border:none;")
        lay.addWidget(accent); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        vb.addWidget(QLabel(f"👤  {self.person['name']}  —  Individual Ledger",
            styleSheet="color:white;font-size:22px;font-weight:bold;border:none;"))
        phone_str = f"  •  📞 {self.person['phone']}" if self.person["phone"] else ""
        vb.addWidget(QLabel(
            f"{self.person['category'] or 'Other'}{phone_str}"
            + (f"  •  {self.person['notes']}" if self.person["notes"] else ""),
            styleSheet="color:#AAAAAA;font-size:13px;border:none;"))
        lay.addLayout(vb); lay.addStretch()
        btn = QPushButton("← Back to Register")
        btn.setFixedHeight(44); btn.setMinimumWidth(190)
        btn.setStyleSheet(
            "QPushButton{background:#444455;color:white;border-radius:8px;"
            "border:none;font-size:14px;font-weight:bold;}"
            "QPushButton:hover{background:#6666AA;}")
        btn.clicked.connect(self._go_back)
        lay.addWidget(btn)
        return f

    def _toolbar(self):
        f = QFrame()
        f.setStyleSheet("background:white;border-bottom:2px solid #EEEEEE;")
        f.setFixedHeight(92)
        lay = QHBoxLayout(f); lay.setContentsMargins(30, 0, 30, 0); lay.setSpacing(22)

        for attr, label, color in [
            ("lbl_given",    "TOTAL CASH GIVEN",    RED),
            ("lbl_received", "TOTAL CASH RECEIVED", GREEN),
            ("lbl_balance",  "NET BALANCE",         BLUE),
        ]:
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(QLabel(label,
                styleSheet="font-size:9px;font-weight:bold;color:#AAAAAA;"
                           "letter-spacing:1px;border:none;"))
            lv = QLabel("PKR 0")
            lv.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;border:none;")
            col.addWidget(lv); setattr(self, attr, lv)
            lay.addLayout(col)
            div = QFrame(); div.setFrameShape(QFrame.VLine)
            div.setStyleSheet("color:#EEEEEE;"); lay.addWidget(div)

        lay.addStretch()

        # Action buttons
        for label, color, fn in [
            ("💸  Cash Given",    RED,   self._add_cash_given),
            ("💰  Cash Received", GREEN, self._add_cash_received),
            ("📝  Add Note",      BLUE,  self._add_note),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(52); btn.setMinimumWidth(160)
            btn.setStyleSheet(f"""
                QPushButton{{background:{color};color:white;border-radius:10px;
                    border:none;font-size:14px;font-weight:bold;}}
                QPushButton:hover{{opacity:.85;}}""")
            btn.clicked.connect(fn)
            lay.addWidget(btn)

        # PDF + Share
        btn_pdf = QPushButton("📄  Save as PDF")
        btn_pdf.setFixedHeight(52); btn_pdf.setMinimumWidth(150)
        btn_pdf.setStyleSheet(f"""
            QPushButton{{background:#555;color:white;border-radius:10px;
                border:none;font-size:14px;font-weight:bold;}}
            QPushButton:hover{{background:#444;}}""")
        btn_pdf.clicked.connect(self._save_pdf)
        lay.addWidget(btn_pdf)

        btn_share = QPushButton("📧  Share")
        btn_share.setFixedHeight(52); btn_share.setMinimumWidth(110)
        btn_share.setStyleSheet(f"""
            QPushButton{{background:{PURPLE};color:white;border-radius:10px;
                border:none;font-size:14px;font-weight:bold;}}
            QPushButton:hover{{background:#7D3C98;}}""")
        btn_share.clicked.connect(self._share)
        lay.addWidget(btn_share)
        return f

    def _table_area(self):
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Date", "Type", "Description",
            "Cash Given", "Cash Received", "Running Balance"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self.table.setColumnWidth(0, 40)
        hh.setSectionResizeMode(1, QHeaderView.Fixed); self.table.setColumnWidth(1, 105)
        hh.setSectionResizeMode(2, QHeaderView.Fixed); self.table.setColumnWidth(2, 130)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Fixed); self.table.setColumnWidth(4, 130)
        hh.setSectionResizeMode(5, QHeaderView.Fixed); self.table.setColumnWidth(5, 130)
        hh.setSectionResizeMode(6, QHeaderView.Fixed); self.table.setColumnWidth(6, 150)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { border:none; font-size:13px; background:white; }
            QHeaderView::section {
                background:#1A1A2E; color:white; font-weight:bold;
                font-size:11px; padding:8px 4px; border:none;
                border-right:1px solid #2A2A4A;
            }
            QTableWidget::item { padding:6px 4px; }
            QTableWidget::item:alternate { background:#F5F8FF; }
            QTableWidget::item:selected { background:#1B4F72; color:white; }
        """)
        scroll = QScrollArea(); scroll.setWidget(self.table)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        return scroll

    def _footer(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-top:2px solid {BLUE};")
        f.setFixedHeight(52)
        lay = QHBoxLayout(f); lay.setContentsMargins(24, 0, 24, 0)
        self.lbl_foot = QLabel("")
        self.lbl_foot.setStyleSheet(
            f"color:{BLUE};font-size:14px;font-weight:bold;border:none;")
        lay.addWidget(self.lbl_foot); lay.addStretch()
        btn_edit = QPushButton("✏  Edit Selected")
        btn_edit.setFixedHeight(38); btn_edit.setMinimumWidth(140)
        btn_edit.setStyleSheet(
            "QPushButton{background:#2C2C4E;color:white;border-radius:6px;"
            "border:none;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#3D3D6E;}")
        btn_edit.clicked.connect(self._edit_entry)
        btn_del = QPushButton("✕  Delete Selected")
        btn_del.setFixedHeight(38); btn_del.setMinimumWidth(150)
        btn_del.setStyleSheet(
            "QPushButton{background:#7B241C;color:white;border-radius:6px;"
            "border:none;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#C0392B;}")
        btn_del.clicked.connect(self._delete_entry)
        lay.addWidget(btn_edit); lay.addSpacing(8); lay.addWidget(btn_del)
        return f

    # ── DATA ───────────────────────────────────────────────────────────────────
    def refresh(self):
        entries = database.people_ledger_get(self.person["id"])
        self._entries = entries
        self.table.setRowCount(len(entries))

        running = 0.0
        for i, e in enumerate(entries):
            given    = float(e["cash_given"]    or 0)
            received = float(e["cash_received"] or 0)
            running  = running + given - received
            etype    = e["entry_type"] or "Note"
            tcolor   = TYPE_COLOR.get(etype, "#555555")

            # Running balance color
            if running > 0:   bal_col = RED     # they owe us
            elif running < 0: bal_col = GREEN   # we owe them
            else:             bal_col = "#888"

            vals = [
                str(i + 1),
                e["date"] or "—",
                f"{TYPE_ICON.get(etype,'•')}  {etype}",
                e["description"] or "—",
                f"PKR {given:,.0f}"    if given    else "—",
                f"PKR {received:,.0f}" if received else "—",
                f"PKR {running:,.0f}",
            ]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if j == 3:  # description left-align
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if j == 2:  # type — coloured
                    item.setForeground(QColor(tcolor))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                if j == 4 and given:    # given — red
                    item.setForeground(QColor(RED))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                if j == 5 and received: # received — green
                    item.setForeground(QColor(GREEN))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                if j == 6:  # balance
                    item.setForeground(QColor(bal_col))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table.setItem(i, j, item)

        given_t, recd_t, net = database.people_ledger_summary(self.person["id"])
        self.lbl_given.setText(f"PKR {given_t:,.0f}")
        self.lbl_received.setText(f"PKR {recd_t:,.0f}")

        if net > 0:
            self.lbl_balance.setText(f"PKR {net:,.0f}  (they owe us)")
            self.lbl_balance.setStyleSheet(
                f"color:{RED};font-size:18px;font-weight:bold;border:none;")
        elif net < 0:
            self.lbl_balance.setText(f"PKR {abs(net):,.0f}  (we owe them)")
            self.lbl_balance.setStyleSheet(
                f"color:{GREEN};font-size:18px;font-weight:bold;border:none;")
        else:
            self.lbl_balance.setText("PKR 0  (settled)")
            self.lbl_balance.setStyleSheet(
                "color:#888;font-size:18px;font-weight:bold;border:none;")

        self.lbl_foot.setText(f"{len(entries)} entries  •  Net: PKR {net:,.0f}")

    # ── ENTRY ACTIONS ──────────────────────────────────────────────────────────
    def _add_cash_given(self):
        dlg = LedgerEntryDialog("Cash Given", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.people_ledger_add(self.person["id"], d["date"],
                "Cash Given", d["desc"], d["amount"], 0)
            self.refresh()

    def _add_cash_received(self):
        dlg = LedgerEntryDialog("Cash Received", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.people_ledger_add(self.person["id"], d["date"],
                "Cash Received", d["desc"], 0, d["amount"])
            self.refresh()

    def _add_note(self):
        dlg = LedgerEntryDialog("Note", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            database.people_ledger_add(self.person["id"], d["date"],
                "Note", d["desc"], 0, 0)
            self.refresh()

    def _selected_entry(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self._entries[row]

    def _edit_entry(self):
        e = self._selected_entry()
        if not e:
            QMessageBox.warning(self, "Select", "Select an entry first."); return
        dlg = LedgerEntryDialog(e["entry_type"], row=e, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            etype = e["entry_type"]
            given    = d["amount"] if etype == "Cash Given"    else 0
            received = d["amount"] if etype == "Cash Received" else 0
            database.people_ledger_edit(e["id"], d["date"], etype,
                                        d["desc"], given, received)
            self.refresh()

    def _delete_entry(self):
        e = self._selected_entry()
        if not e:
            QMessageBox.warning(self, "Select", "Select an entry first."); return
        if QMessageBox.question(self, "Delete", "Delete this entry?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            database.people_ledger_delete(e["id"])
            self.refresh()

    # ── PDF / SHARE ────────────────────────────────────────────────────────────
    def _save_pdf(self):
        try:
            from reports.invoice_generator import generate_person_statement
            out_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            path = generate_person_statement(self.person["id"], out_dir)
            QMessageBox.information(self, "PDF Saved",
                f"✅  Statement saved:\n\n{os.path.basename(path)}\n\n"
                f"Location: {path}")
            # Open automatically
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not generate PDF:\n{e}")

    def _share(self):
        """Generate PDF then open email client with it attached."""
        try:
            from reports.invoice_generator import generate_person_statement
            out_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            path = generate_person_statement(self.person["id"], out_dir)
            # Try to send via the existing email system
            try:
                from reports.email_sender import send_email_with_attachment
                company = database.get_setting("company_name") or "Last Hammer"
                subject = f"{company} — Account Statement: {self.person['name']}"
                body    = (f"Dear {self.person['name']},\n\n"
                           f"Please find attached your account statement from {company}.\n\n"
                           f"Regards,\n{company}")
                recipient = database.get_setting("owner_email") or ""
                send_email_with_attachment(
                    to_email=recipient, subject=subject,
                    body=body, attachment_path=path)
                QMessageBox.information(self, "Sent",
                    f"✅  Statement emailed successfully!\n\n{os.path.basename(path)}")
            except Exception:
                # Fallback: just open the PDF
                import subprocess, sys
                if sys.platform == "win32": os.startfile(path)
                elif sys.platform == "darwin": subprocess.call(["open", path])
                else: subprocess.call(["xdg-open", path])
                QMessageBox.information(self, "PDF Ready",
                    f"Statement PDF is ready:\n{path}\n\n"
                    "Configure email in Settings to send automatically.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _go_back(self):
        if self.parent_register:
            self.parent_register.refresh()
            self.parent_register.show()
        self.close()

    def closeEvent(self, e):
        if self.parent_register:
            self.parent_register.refresh()
            self.parent_register.show()
        super().closeEvent(e)


# ══════════════════════════════════════════════════════════════
#  DIALOGS
# ══════════════════════════════════════════════════════════════
class PersonDialog(QDialog):
    """Add / edit a person."""
    def __init__(self, row=None, parent=None):
        super().__init__(parent)
        self._row = row
        self.setWindowTitle("New Person" if not row else "Edit Person")
        self.setFixedSize(440, 380)
        self.setStyleSheet("QDialog{background:white;} QLabel{border:none;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22); lay.setSpacing(12)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{BLUE}15;border-radius:8px;"
            f"border-left:4px solid {BLUE};"
            "border-top:none;border-right:none;border-bottom:none;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14, 10, 14, 10)
        hl.addWidget(QLabel(
            "👤  " + ("NEW PERSON" if not row else "EDIT PERSON"),
            styleSheet=f"font-size:14px;font-weight:bold;color:{BLUE};border:none;"))
        lay.addWidget(hdr)

        form = QFormLayout(); form.setSpacing(10); form.setLabelAlignment(Qt.AlignRight)

        def L(t): return QLabel(t, styleSheet="font-weight:bold;font-size:12px;")
        def inp(ph=""): w = QLineEdit(); w.setPlaceholderText(ph); w.setMinimumHeight(42); return w

        self.inp_name  = inp("Full name  e.g. Malik Rehman, Shoukat Ali...")
        self.inp_phone = inp("Phone number  (optional)")
        self.inp_cat   = QComboBox(); self.inp_cat.addItems(CATEGORIES)
        self.inp_cat.setMinimumHeight(42)
        self.inp_notes = QTextEdit(); self.inp_notes.setFixedHeight(70)
        self.inp_notes.setPlaceholderText("Any notes about this person...")

        form.addRow(L("Name:"),     self.inp_name)
        form.addRow(L("Phone:"),    self.inp_phone)
        form.addRow(L("Category:"), self.inp_cat)
        form.addRow(L("Notes:"),    self.inp_notes)
        lay.addLayout(form)

        if row:
            self.inp_name.setText(row["name"] or "")
            self.inp_phone.setText(row["phone"] or "")
            ci = self.inp_cat.findText(row["category"] or "Other")
            self.inp_cat.setCurrentIndex(max(ci, 0))
            self.inp_notes.setPlainText(row["notes"] or "")

        lay.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setMinimumHeight(46)
        cancel.setStyleSheet(
            "background:#DDD;color:#333;border-radius:8px;border:none;font-size:13px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("👤  Save"); save.setMinimumHeight(46)
        save.setStyleSheet(
            f"background:{BLUE};color:white;border-radius:8px;"
            "border:none;font-size:14px;font-weight:bold;")
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save, 1)
        lay.addLayout(btns)

    def _save(self):
        if not self.inp_name.text().strip():
            QMessageBox.warning(self, "Required", "Enter a name."); return
        self.accept()

    def data(self):
        return {"name":     self.inp_name.text().strip(),
                "phone":    self.inp_phone.text().strip(),
                "category": self.inp_cat.currentText(),
                "notes":    self.inp_notes.toPlainText().strip()}


class LedgerEntryDialog(QDialog):
    """Add / edit a ledger entry (Cash Given / Cash Received / Note)."""
    def __init__(self, entry_type="Cash Given", row=None, parent=None):
        super().__init__(parent)
        self._etype = entry_type
        self._row   = row
        color = TYPE_COLOR.get(entry_type, BLUE)
        icon  = TYPE_ICON.get(entry_type, "•")
        self.setWindowTitle(
            f"{'Edit' if row else 'New'} {entry_type}")
        self.setFixedSize(440, 340)
        self.setStyleSheet("QDialog{background:white;} QLabel{border:none;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22); lay.setSpacing(12)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{color}15;border-radius:8px;"
            f"border-left:4px solid {color};"
            "border-top:none;border-right:none;border-bottom:none;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14, 10, 14, 10)
        hl.addWidget(QLabel(f"{icon}  {entry_type.upper()}",
            styleSheet=f"font-size:14px;font-weight:bold;color:{color};border:none;"))
        lay.addWidget(hdr)

        form = QFormLayout(); form.setSpacing(10); form.setLabelAlignment(Qt.AlignRight)
        def L(t): return QLabel(t, styleSheet="font-weight:bold;font-size:12px;")

        self.inp_date = QDateEdit(QDate.currentDate())
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setMinimumHeight(42)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Description / reason...")
        self.inp_desc.setMinimumHeight(42)

        self.inp_amount = QDoubleSpinBox()
        self.inp_amount.setRange(0, 99999999); self.inp_amount.setDecimals(0)
        self.inp_amount.setSuffix(" PKR"); self.inp_amount.setMinimumHeight(42)

        form.addRow(L("Date:"),        self.inp_date)
        form.addRow(L("Description:"), self.inp_desc)
        if entry_type != "Note":
            form.addRow(L("Amount:"),  self.inp_amount)
        lay.addLayout(form)

        if row:
            self.inp_date.setDate(QDate.fromString(row["date"], "yyyy-MM-dd"))
            self.inp_desc.setText(row["description"] or "")
            if entry_type == "Cash Given":
                self.inp_amount.setValue(float(row["cash_given"] or 0))
            elif entry_type == "Cash Received":
                self.inp_amount.setValue(float(row["cash_received"] or 0))

        lay.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setMinimumHeight(46)
        cancel.setStyleSheet(
            "background:#DDD;color:#333;border-radius:8px;border:none;font-size:13px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton(f"{icon}  Save"); save.setMinimumHeight(46)
        save.setStyleSheet(
            f"background:{color};color:white;border-radius:8px;"
            "border:none;font-size:14px;font-weight:bold;")
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save, 1)
        lay.addLayout(btns)

    def _save(self):
        if not self.inp_desc.text().strip() and self._etype == "Note":
            QMessageBox.warning(self, "Required", "Enter a description."); return
        if self._etype != "Note" and self.inp_amount.value() <= 0:
            QMessageBox.warning(self, "Required", "Enter amount > 0."); return
        self.accept()

    def data(self):
        return {
            "date":   self.inp_date.date().toString("yyyy-MM-dd"),
            "desc":   self.inp_desc.text().strip(),
            "amount": self.inp_amount.value() if self._etype != "Note" else 0,
        }