"""
Invoice Review Dialog — Last Hammer EMS
Shows full breakdown BEFORE generating PDF.
User can add notes, verify every figure, then confirm or cancel.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QTextEdit, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
import config

GOLD   = "#F39C12"
RED    = "#C0392B"
GREEN  = "#1E8449"
DARK   = "#1A1A2E"
ORANGE = "#CA6F1E"
TEAL   = "#0E6655"
BLUE   = "#1B4F72"
PURPLE = "#6C3483"


class InvoiceReviewDialog(QDialog):
    """
    Pass in a dict with all financial figures already computed.
    User reviews, optionally adds notes, then clicks Confirm or Cancel.
    .notes property returns whatever the user typed.
    """

    def __init__(self, review_data: dict, parent=None):
        super().__init__(parent)
        self.review_data = review_data
        self.setWindowTitle("⚠  Review Invoice Before Generating")
        self.setMinimumSize(820, 680)
        self.setModal(True)
        self._confirmed = False
        self._build_ui()

    @property
    def confirmed(self):
        return self._confirmed

    @property
    def notes(self):
        return self.notes_edit.toPlainText().strip()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Warning header ──
        hdr = QFrame()
        hdr.setStyleSheet(f"background:{DARK}; border-bottom:3px solid {GOLD};")
        hdr.setFixedHeight(72)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24, 0, 24, 0)
        ico = QLabel("⚠"); ico.setStyleSheet(f"font-size:28px;color:{GOLD};border:none;")
        vb  = QVBoxLayout(); vb.setSpacing(1)
        t1  = QLabel("REVIEW BEFORE GENERATING INVOICE")
        t1.setStyleSheet("color:white;font-size:16px;font-weight:bold;border:none;")
        t2  = QLabel("Check every figure carefully — verify WE OWE THEM vs THEY OWE US before proceeding")
        t2.setStyleSheet(f"color:{GOLD};font-size:11px;border:none;")
        vb.addWidget(t1); vb.addWidget(t2)
        hl.addWidget(ico); hl.addSpacing(10); hl.addLayout(vb); hl.addStretch()
        root.addWidget(hdr)

        # ── Scrollable body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#F5F5F5;}")
        body_w = QWidget(); body_w.setStyleSheet("background:#F5F5F5;")
        body = QVBoxLayout(body_w)
        body.setContentsMargins(24, 20, 24, 10)
        body.setSpacing(14)

        rd = self.review_data
        inv_type = rd.get("inv_type", "")
        color    = {"dumprei":ORANGE,"excavator":TEAL,"dumper":BLUE,
                    "loader":GREEN,"royalty":PURPLE}.get(inv_type, DARK)

        # ── Person / period ──
        body.addWidget(self._info_card(rd, color))

        # ── Line items table ──
        body.addWidget(self._make_section_label("📋  LINE ITEMS BREAKDOWN"))
        body.addWidget(self._items_table(rd, color))

        # ── Financial summary ──
        body.addWidget(self._make_section_label("💰  FINANCIAL SUMMARY — VERIFY CAREFULLY"))
        body.addWidget(self._financial_summary(rd, color))

        # ── Balance verification (the critical one) ──
        body.addWidget(self._make_section_label("⚖  BALANCE VERIFICATION"))
        body.addWidget(self._balance_verify(rd))

        # ── Notes ──
        body.addWidget(self._make_section_label("📝  ADD NOTES / REMARKS (optional)"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(80)
        self.notes_edit.setPlaceholderText(
            "Add any corrections, notes or remarks to appear on the invoice...")
        self.notes_edit.setStyleSheet(
            "background:white;border:1px solid #DDDDDD;border-radius:6px;"
            "font-size:13px;padding:8px;")
        body.addWidget(self.notes_edit)
        body.addStretch()

        scroll.setWidget(body_w)
        root.addWidget(scroll, 1)

        # ── Buttons ──
        btn_bar = QFrame()
        btn_bar.setStyleSheet(
            f"background:{DARK};border-top:2px solid {GOLD};")
        btn_bar.setFixedHeight(72)
        bl = QHBoxLayout(btn_bar); bl.setContentsMargins(24, 0, 24, 0); bl.setSpacing(12)

        btn_cancel = QPushButton("✕  Cancel — Go Back and Correct")
        btn_cancel.setFixedHeight(50); btn_cancel.setMinimumWidth(260)
        btn_cancel.setStyleSheet("""
            QPushButton{background:#922B21;color:white;border-radius:8px;
                border:none;font-size:14px;font-weight:bold;}
            QPushButton:hover{background:#E74C3C;}""")
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("✓  All Figures Correct — Generate PDF")
        btn_confirm.setFixedHeight(50); btn_confirm.setMinimumWidth(280)
        btn_confirm.setStyleSheet(f"""
            QPushButton{{background:{GOLD};color:{DARK};border-radius:8px;
                border:none;font-size:14px;font-weight:bold;}}
            QPushButton:hover{{background:#F5B041;}}""")
        btn_confirm.clicked.connect(self._confirm)

        bl.addWidget(btn_cancel); bl.addStretch(); bl.addWidget(btn_confirm)
        root.addWidget(btn_bar)

    def _confirm(self):
        self._confirmed = True
        self.accept()

    def _make_section_label(self, text):
        l = QLabel(text)
        l.setStyleSheet(
            "font-size:11px;font-weight:bold;color:#888888;"
            "letter-spacing:1px;background:transparent;border:none;")
        return l

    def _card(self, color=None):
        f = QFrame()
        f.setStyleSheet(
            f"background:white;border-radius:10px;"
            f"{'border-left:4px solid '+color+';' if color else ''}"
            f"border-top:1px solid #EEEEEE;"
            f"border-right:1px solid #EEEEEE;"
            f"border-bottom:1px solid #EEEEEE;")
        return f

    def _info_card(self, rd, color):
        f = self._card(color)
        lay = QHBoxLayout(f); lay.setContentsMargins(18,14,18,14); lay.setSpacing(24)

        def kv(k, v):
            w = QWidget(); w.setStyleSheet("background:transparent;border:none;")
            vb = QVBoxLayout(w); vb.setSpacing(2); vb.setContentsMargins(0,0,0,0)
            lk = QLabel(k); lk.setStyleSheet(f"font-size:10px;font-weight:bold;color:{color};border:none;letter-spacing:1px;")
            lv = QLabel(str(v)); lv.setStyleSheet("font-size:14px;font-weight:bold;color:#1A1A2E;border:none;")
            vb.addWidget(lk); vb.addWidget(lv)
            return w

        lay.addWidget(kv("INVOICE TYPE",  rd.get("type_label","—")))
        lay.addWidget(kv("PAYEE",         rd.get("payee_name","—")))
        lay.addWidget(kv("VEHICLE / REG", rd.get("payee_detail","—")))
        lay.addWidget(kv("FROM DATE",     rd.get("date_from","—")))
        lay.addWidget(kv("TO DATE",       rd.get("date_to","—")))
        lay.addWidget(kv("TOTAL ENTRIES", str(rd.get("entry_count", 0))))
        lay.addStretch()
        return f

    def _items_table(self, rd, color):
        rows    = rd.get("line_items", [])
        headers = rd.get("headers", [])
        if not rows:
            l = QLabel("  No entries found for this period.")
            l.setStyleSheet("font-size:13px;color:#AAAAAA;background:transparent;border:none;")
            return l

        f = self._card()
        lay = QVBoxLayout(f); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(min(40 + len(rows)*32, 280))
        scroll.setStyleSheet("QScrollArea{border:none;}")

        inner = QWidget()
        grid  = QGridLayout(inner)
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)

        # Header row
        for c, h in enumerate(headers):
            lbl = QLabel(str(h))
            lbl.setStyleSheet(
                f"background:{color};color:white;font-size:11px;font-weight:bold;"
                f"padding:6px 8px;border:none;")
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, c)

        # Data rows
        for r, row in enumerate(rows):
            bg = "white" if r % 2 == 0 else "#F9F9F9"
            for c, val in enumerate(row):
                lbl = QLabel(str(val))
                lbl.setStyleSheet(
                    f"background:{bg};font-size:11px;padding:5px 8px;border:none;"
                    f"border-bottom:1px solid #EEEEEE;")
                lbl.setAlignment(Qt.AlignCenter)
                grid.addWidget(lbl, r+1, c)

        scroll.setWidget(inner)
        lay.addWidget(scroll)
        return f

    def _financial_summary(self, rd, color):
        f = self._card(color)
        grid = QGridLayout(f); grid.setContentsMargins(18,14,18,14); grid.setSpacing(10)

        def stat(label, value, highlight=False, big=False):
            w  = QFrame()
            w.setStyleSheet(
                f"background:#FAFAFA;border-radius:6px;"
                f"border:1px solid {'#DDDDDD' if not highlight else color};")
            vb = QVBoxLayout(w); vb.setContentsMargins(10,8,10,8); vb.setSpacing(2)
            lk = QLabel(label)
            lk.setStyleSheet(f"font-size:9px;font-weight:bold;color:{color if highlight else '#888'};border:none;letter-spacing:1px;")
            lv = QLabel(value)
            lv.setStyleSheet(f"font-size:{'16px' if big else '13px'};font-weight:bold;color:{DARK};border:none;")
            vb.addWidget(lk); vb.addWidget(lv)
            return w

        fin = rd.get("financials", {})
        items = list(fin.items())
        for i, (k, v) in enumerate(items):
            big = (k.upper() in ("GRAND TOTAL","TOTAL WORK","WORK EARNED","TOTAL PAID"))
            grid.addWidget(stat(k, str(v), highlight=big, big=big), i//3, i%3)
        return f

    def _balance_verify(self, rd):
        we_owe   = rd.get("we_still_owe", 0)
        they_owe = rd.get("they_owe_us",  0)

        f = QFrame()
        f.setStyleSheet("background:transparent;border:none;")
        lay = QHBoxLayout(f); lay.setContentsMargins(0,0,0,0); lay.setSpacing(14)

        # WE OWE THEM box
        we_active = we_owe > 0
        we_f = QFrame()
        we_f.setStyleSheet(
            f"background:{'#FEF0F0' if we_active else '#FAFAFA'};"
            f"border-radius:10px;"
            f"border:{'2px solid '+RED if we_active else '1px solid #DDDDDD'};")
        we_lay = QVBoxLayout(we_f); we_lay.setContentsMargins(20,16,20,16); we_lay.setSpacing(4)
        we_lbl = QLabel("⚠  WE OWE THEM" if we_active else "WE OWE THEM")
        we_lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{'#C0392B' if we_active else '#AAAAAA'};border:none;")
        we_val = QLabel(f"PKR {we_owe:,.2f}")
        we_val.setStyleSheet(f"font-size:26px;font-weight:bold;color:{'#C0392B' if we_active else '#CCCCCC'};border:none;")
        we_sub = QLabel("Amount we still need to pay them")
        we_sub.setStyleSheet("font-size:10px;color:#888888;border:none;")
        if we_active:
            note = QLabel("✓ CORRECT — this means they worked/delivered more than we paid")
            note.setStyleSheet(f"font-size:10px;color:{RED};font-weight:bold;border:none;")
            note.setWordWrap(True)
            we_lay.addWidget(note)
        we_lay.addWidget(we_lbl); we_lay.addWidget(we_val); we_lay.addWidget(we_sub)

        # THEY OWE US box
        th_active = they_owe > 0
        th_f = QFrame()
        th_f.setStyleSheet(
            f"background:{'#EAFAF1' if th_active else '#FAFAFA'};"
            f"border-radius:10px;"
            f"border:{'2px solid '+GREEN if th_active else '1px solid #DDDDDD'};")
        th_lay = QVBoxLayout(th_f); th_lay.setContentsMargins(20,16,20,16); th_lay.setSpacing(4)
        th_lbl = QLabel("✓  THEY OWE US" if th_active else "THEY OWE US")
        th_lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{'#1E8449' if th_active else '#AAAAAA'};border:none;")
        th_val = QLabel(f"PKR {they_owe:,.2f}")
        th_val.setStyleSheet(f"font-size:26px;font-weight:bold;color:{'#1E8449' if th_active else '#CCCCCC'};border:none;")
        th_sub = QLabel("We overpaid — they must return this amount")
        th_sub.setStyleSheet("font-size:10px;color:#888888;border:none;")
        if th_active:
            note2 = QLabel("✓ CORRECT — this means we gave more advance than work done")
            note2.setStyleSheet(f"font-size:10px;color:{GREEN};font-weight:bold;border:none;")
            note2.setWordWrap(True)
            th_lay.addWidget(note2)
        th_lay.addWidget(th_lbl); th_lay.addWidget(th_val); th_lay.addWidget(th_sub)

        lay.addWidget(we_f, 1)
        lay.addWidget(th_f, 1)
        return f