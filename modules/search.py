"""
CH 13 — Global Search
Searches across every chapter simultaneously.
Robust: each table query is independently wrapped so one bad table never
blocks results from the others.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QAbstractItemView, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
import database, config

DARK  = config.DARK
BLUE  = "#2980B9"
GOLD  = "#F39C12"

# Colour per chapter source
SRC_META = {
    "CH1 General":  {"color": "#C0392B",  "icon": "📦"},
    "CH2 Royalty":  {"color": "#6C3483",  "icon": "⛏"},
    "CH3 Excavator":{"color": "#0E6655",  "icon": "🦺"},
    "CH4 Dumprei":  {"color": "#CA6F1E",  "icon": "🚛"},
    "CH5 Truck":    {"color": "#1B4F72",  "icon": "🚚"},
    "CH5 Loader":   {"color": "#1E8449",  "icon": "🏗"},
    "CH6 Memo":     {"color": "#27AE60",  "icon": "📝"},
    "CH9 Advance":  {"color": "#E67E22",  "icon": "💰"},
}


class SearchModule(QMainWindow):
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("CH 13 — Global Search")
        self.setMinimumSize(1280, 820)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_search)
        self._last_results = []
        self._build_ui()

    # ── BUILD ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._topbar())
        root.addWidget(self._search_bar())
        root.addWidget(self._chapter_chips())
        root.addWidget(self._content_area(), 1)
        root.addWidget(self._footer())

    def _topbar(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-bottom:3px solid {BLUE};")
        f.setFixedHeight(72)
        lay = QHBoxLayout(f); lay.setContentsMargins(28, 0, 28, 0)
        bar = QFrame(); bar.setFixedSize(6, 44)
        bar.setStyleSheet(f"background:{BLUE};border-radius:3px;border:none;")
        lay.addWidget(bar); lay.addSpacing(14)
        vb = QVBoxLayout(); vb.setSpacing(2)
        vb.addWidget(QLabel("Chapter 13 — Global Search",
            styleSheet="color:white;font-size:20px;font-weight:bold;border:none;"))
        vb.addWidget(QLabel(
            "Search by name, registration, amount or description — across all chapters at once",
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

    def _search_bar(self):
        f = QFrame()
        f.setStyleSheet(f"background:#1E1E38;border-bottom:1px solid #2A2A4A;")
        f.setFixedHeight(76)
        lay = QHBoxLayout(f); lay.setContentsMargins(28, 0, 28, 0); lay.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "🔍   Type to search...  e.g.  Shoukat   JU-1234   50000   diesel   royalty")
        self.search_box.setMinimumHeight(52)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                font-size: 16px; font-weight: bold;
                padding: 8px 18px;
                border: 2px solid #3A3A5A;
                border-radius: 10px;
                background: #12122A;
                color: white;
            }}
            QLineEdit:focus {{
                border-color: {BLUE};
                background: #1A1A35;
            }}
        """)
        self.search_box.textChanged.connect(self._on_text)
        lay.addWidget(self.search_box, 1)

        btn_clear = QPushButton("✕  Clear")
        btn_clear.setFixedHeight(52); btn_clear.setFixedWidth(100)
        btn_clear.setStyleSheet(
            "QPushButton{background:#2C2C4E;color:#AAAAAA;border-radius:8px;"
            "border:none;font-size:13px;}"
            "QPushButton:hover{background:#3D3D6E;color:white;}")
        btn_clear.clicked.connect(self._clear)
        lay.addWidget(btn_clear)
        return f

    def _chapter_chips(self):
        """Filter chips — click to filter by chapter."""
        f = QFrame()
        f.setStyleSheet("background:#F5F5F5;border-bottom:1px solid #E0E0E0;")
        f.setFixedHeight(50)
        lay = QHBoxLayout(f); lay.setContentsMargins(20, 0, 20, 0); lay.setSpacing(8)
        lay.addWidget(QLabel("Filter:",
            styleSheet="font-size:11px;font-weight:bold;color:#888;border:none;"))

        self._chip_btns = {}
        chips = [("All", BLUE)] + [(k, v["color"]) for k, v in SRC_META.items()]
        for label, color in chips:
            btn = QPushButton(label)
            btn.setFixedHeight(32); btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #EEEEEE; color: #555555;
                    border-radius: 16px; border: 1.5px solid #DDDDDD;
                    font-size: 11px; font-weight: bold; padding: 0 12px;
                }}
                QPushButton:checked {{
                    background: {color}; color: white; border-color: {color};
                }}
                QPushButton:hover {{ background: {color}22; border-color: {color}; }}
            """)
            btn.clicked.connect(lambda checked, lbl=label: self._filter_chip(lbl))
            self._chip_btns[label] = btn
            lay.addWidget(btn)

        self._chip_btns["All"].setChecked(True)
        self._active_chip = "All"
        lay.addStretch()
        return f

    def _content_area(self):
        # Use a plain QWidget with proper layout — no nested scroll traps
        container = QWidget()
        container.setStyleSheet("background:#FAFAFA;")
        self._content_lay = QVBoxLayout(container)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        self._content_lay.setSpacing(0)

        # Welcome screen
        self._welcome_widget = self._build_welcome()
        self._content_lay.addWidget(self._welcome_widget)

        # Results table (hidden initially)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Chapter", "Date", "Person / Description", "Extra Info", "Amount (PKR)", "ID"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self.table.setColumnWidth(0, 120)
        hh.setSectionResizeMode(1, QHeaderView.Fixed); self.table.setColumnWidth(1, 100)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Fixed); self.table.setColumnWidth(3, 130)
        hh.setSectionResizeMode(4, QHeaderView.Fixed); self.table.setColumnWidth(4, 130)
        hh.setSectionResizeMode(5, QHeaderView.Fixed); self.table.setColumnWidth(5, 60)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 13px;
                background: white;
                gridline-color: #F0F0F0;
            }
            QHeaderView::section {
                background: #1A1A2E; color: white;
                font-weight: bold; font-size: 11px;
                padding: 8px 6px; border: none;
                border-right: 1px solid #2A2A4A;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:alternate { background: #F8F8FF; }
            QTableWidget::item:selected { background: #2980B9; color: white; }
        """)
        self.table.hide()
        self._content_lay.addWidget(self.table, 1)

        # No results screen (hidden initially)
        self._no_results_widget = self._build_no_results()
        self._no_results_widget.hide()
        self._content_lay.addWidget(self._no_results_widget)

        return container

    def _build_welcome(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 40, 0, 0)
        lay.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        ico = QLabel("🔍")
        ico.setStyleSheet("font-size:64px;border:none;background:transparent;")
        ico.setAlignment(Qt.AlignCenter)
        lay.addWidget(ico)
        lay.addSpacing(16)

        title = QLabel("Search Across Everything")
        title.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{DARK};border:none;background:transparent;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        lay.addSpacing(10)

        sub = QLabel("Type any name, reg number, amount, or keyword above")
        sub.setStyleSheet("font-size:14px;color:#AAAAAA;border:none;background:transparent;")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        lay.addSpacing(32)

        # Example chips
        ex_row = QHBoxLayout(); ex_row.setAlignment(Qt.AlignCenter); ex_row.setSpacing(10)
        examples = ["Shoukat", "JU-1234", "50000", "diesel", "advance", "royalty"]
        for ex in examples:
            btn = QPushButton(f'"{ex}"')
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: white; color: {BLUE};
                    border: 1.5px solid {BLUE}; border-radius: 18px;
                    font-size: 13px; font-weight: bold; padding: 0 16px;
                }}
                QPushButton:hover {{ background: {BLUE}; color: white; }}
            """)
            btn.clicked.connect(lambda _, t=ex: self._search_example(t))
            ex_row.addWidget(btn)
        w2 = QWidget(); w2.setLayout(ex_row); w2.setStyleSheet("background:transparent;")
        lay.addWidget(w2)
        lay.addSpacing(32)

        # Chapter guide
        grid = QGridLayout(); grid.setSpacing(10); grid.setContentsMargins(60, 0, 60, 0)
        for i, (src, meta) in enumerate(SRC_META.items()):
            card = QFrame()
            card.setStyleSheet(
                f"background:white;border-radius:8px;"
                f"border-left:3px solid {meta['color']};"
                f"border-top:1px solid #EEE;border-right:1px solid #EEE;border-bottom:1px solid #EEE;")
            ch = QHBoxLayout(card); ch.setContentsMargins(10, 8, 10, 8); ch.setSpacing(8)
            ch.addWidget(QLabel(meta["icon"],
                styleSheet="font-size:18px;border:none;background:transparent;"))
            ch.addWidget(QLabel(src,
                styleSheet=f"font-size:12px;font-weight:bold;color:{meta['color']};border:none;"))
            grid.addWidget(card, i // 4, i % 4)
        gw = QWidget(); gw.setLayout(grid); gw.setStyleSheet("background:transparent;")
        lay.addWidget(gw)
        lay.addStretch()
        return w

    def _build_no_results(self):
        w = QWidget(); w.setStyleSheet("background:#FAFAFA;")
        lay = QVBoxLayout(w); lay.setAlignment(Qt.AlignCenter)
        ico = QLabel("🔎")
        ico.setStyleSheet("font-size:56px;border:none;background:transparent;")
        ico.setAlignment(Qt.AlignCenter)
        self._no_res_lbl = QLabel("No results found")
        self._no_res_lbl.setStyleSheet(
            f"font-size:18px;font-weight:bold;color:{DARK};border:none;background:transparent;")
        self._no_res_lbl.setAlignment(Qt.AlignCenter)
        tip = QLabel("Try a shorter keyword, or search by vehicle reg, person name, or amount")
        tip.setStyleSheet("font-size:13px;color:#AAAAAA;border:none;background:transparent;")
        tip.setAlignment(Qt.AlignCenter)
        lay.addWidget(ico); lay.addSpacing(12)
        lay.addWidget(self._no_res_lbl); lay.addSpacing(6)
        lay.addWidget(tip)
        return w

    def _footer(self):
        f = QFrame()
        f.setStyleSheet(f"background:{DARK};border-top:2px solid {BLUE};")
        f.setFixedHeight(52)
        lay = QHBoxLayout(f); lay.setContentsMargins(24, 0, 24, 0)
        self.lbl_status = QLabel("Start typing to search")
        self.lbl_status.setStyleSheet(
            f"color:{BLUE};font-size:14px;font-weight:bold;border:none;")
        lay.addWidget(self.lbl_status); lay.addStretch()
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet("color:#AAAAAA;font-size:13px;border:none;")
        lay.addWidget(self.lbl_total)
        return f

    # ── SEARCH LOGIC ───────────────────────────────────────────────────────────
    def _on_text(self):
        q = self.search_box.text().strip()
        if len(q) < 2:
            self._show_state("welcome")
            self.lbl_status.setText("Type at least 2 characters")
            return
        self._timer.start(300)

    def _do_search(self):
        q = self.search_box.text().strip()
        if len(q) < 2:
            return
        try:
            results = database.global_search(q)
        except Exception as e:
            self._show_state("welcome")
            self.lbl_status.setText(f"Search error: {e}")
            return

        self._last_results = results
        self._display(results, q)

    def _filter_chip(self, label):
        self._active_chip = label
        for k, b in self._chip_btns.items():
            b.setChecked(k == label)
        if not self._last_results:
            return
        if label == "All":
            filtered = self._last_results
        else:
            filtered = [r for r in self._last_results if r.get("source") == label]
        self._display(filtered, self.search_box.text().strip(), from_chip=True)

    def _display(self, results, query, from_chip=False):
        if not results:
            self._show_state("no_results")
            q = self.search_box.text().strip()
            self._no_res_lbl.setText(f'No results for  "{q}"')
            self.lbl_status.setText(f'No results for  "{q}"')
            self.lbl_total.setText("")
            return

        self._show_state("table")
        self.table.setRowCount(len(results))
        total_amount = 0

        for i, r in enumerate(results):
            src   = r.get("source", "—")
            meta  = SRC_META.get(src, {"color": "#555555", "icon": "•"})
            color = meta["color"]
            icon  = meta["icon"]
            amt   = float(r.get("amount") or 0)
            total_amount += amt
            extra = r.get("extra", "") or "—"

            row_vals = [
                f"{icon}  {src}",
                r.get("date", "—"),
                r.get("description", "—"),
                extra,
                f"PKR {amt:,.0f}" if amt else "—",
                str(r.get("id", "—")),
            ]
            for j, v in enumerate(row_vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if j == 2:  # description left-aligned
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if j == 0:
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                if j == 4 and amt > 0:
                    item.setForeground(QColor("#1E8449"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table.setItem(i, j, item)

        # Alternate row tints by source
        for i, r in enumerate(results):
            src   = r.get("source", "—")
            meta  = SRC_META.get(src, {"color": "#555555", "icon": "•"})
            color = meta["color"]
            # Subtle background tint
            tint = QColor(color); tint.setAlpha(18)
            for j in range(6):
                item = self.table.item(i, j)
                if item:
                    item.setBackground(tint)

        n = len(results)
        self.lbl_status.setText(
            f"Found  {n}  result{'s' if n != 1 else ''}  for  \"{query}\"")
        self.lbl_total.setText(f"Total amount:  PKR {total_amount:,.0f}")

    def _show_state(self, state):
        """Switch between welcome / table / no_results."""
        self._welcome_widget.setVisible(state == "welcome")
        self.table.setVisible(state == "table")
        self._no_results_widget.setVisible(state == "no_results")

    def _search_example(self, text):
        self.search_box.setText(text)
        self._do_search()

    def _clear(self):
        self.search_box.clear()
        self._last_results = []
        self._show_state("welcome")
        self.lbl_status.setText("Start typing to search")
        self.lbl_total.setText("")
        for k, b in self._chip_btns.items():
            b.setChecked(k == "All")
        self._active_chip = "All"

    def _back(self):
        if self.parent_dashboard: self.parent_dashboard.show()
        self.close()

    def closeEvent(self, e):
        if self.parent_dashboard: self.parent_dashboard.show()
        super().closeEvent(e)