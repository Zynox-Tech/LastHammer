from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QDateEdit, QComboBox,
    QButtonGroup, QRadioButton,
    QMessageBox, QApplication, QProgressDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import os
import config


class ReportSelectorDialog(QDialog):
    """
    Shown when user clicks 'Generate PDF' or 'Send Email'.
    Lets them pick: Specific Day / Specific Month / All Records.
    action = 'pdf' or 'email'
    """

    MONTHS = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    def __init__(self, action="pdf", parent=None):
        super().__init__(parent)
        self.action = action   # 'pdf' or 'email'
        title = "Generate PDF Report" if action == "pdf" else "Send Report by Email"
        self.setWindowTitle(f"Last Hammer — {title}")
        self.setFixedWidth(540)
        self.setModal(True)
        self._build_ui(title)

    # ─────────────────────────────────────────────────────────
    def _build_ui(self, title):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        bar = QFrame()
        bar.setStyleSheet(f"background-color: {config.DARK};")
        bar.setFixedHeight(70)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(24, 0, 24, 0)
        icon = "📄" if self.action == "pdf" else "📧"
        lbl = QLabel(f"{icon}   {title}")
        lbl.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        bl.addWidget(lbl)
        root.addWidget(bar)

        # Body
        body = QWidget()
        body.setStyleSheet("background-color: #F5F5F5;")
        bl2 = QVBoxLayout(body)
        bl2.setContentsMargins(30, 24, 30, 24)
        bl2.setSpacing(20)

        # ── Radio buttons ─────────────────────────────────────
        lbl_q = QLabel("Select report type:")
        lbl_q.setStyleSheet("font-size: 16px; font-weight: bold; color: #1A1A2E;")
        bl2.addWidget(lbl_q)

        self.btn_group = QButtonGroup(self)

        self.rb_day   = self._radio("📅   Specific Day",   "#1E8449")
        self.rb_month = self._radio("📆   Specific Month", "#1B4F72")
        self.rb_all   = self._radio("📋   All Records (Complete History)", "#C0392B")

        self.rb_day.setChecked(True)
        self.btn_group.addButton(self.rb_day,   0)
        self.btn_group.addButton(self.rb_month, 1)
        self.btn_group.addButton(self.rb_all,   2)

        bl2.addWidget(self.rb_day)
        bl2.addWidget(self.rb_month)
        bl2.addWidget(self.rb_all)

        # ── Date picker (day mode) ────────────────────────────
        self.day_frame = QFrame()
        self.day_frame.setStyleSheet(
            "background: white; border-radius: 8px; border: 1px solid #DDDDDD;")
        dfl = QHBoxLayout(self.day_frame)
        dfl.setContentsMargins(16, 12, 16, 12)
        lbl_d = QLabel("Select Date:")
        lbl_d.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(44)
        self.date_edit.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 6px 12px; "
            "border: 2px solid #CCCCCC; border-radius: 8px; background: white;")
        dfl.addWidget(lbl_d)
        dfl.addSpacing(10)
        dfl.addWidget(self.date_edit)
        dfl.addStretch()
        bl2.addWidget(self.day_frame)

        # ── Month + year pickers (month mode) ─────────────────
        self.month_frame = QFrame()
        self.month_frame.setStyleSheet(
            "background: white; border-radius: 8px; border: 1px solid #DDDDDD;")
        mfl = QHBoxLayout(self.month_frame)
        mfl.setContentsMargins(16, 12, 16, 12)
        lbl_m = QLabel("Month:")
        lbl_m.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.combo_month = QComboBox()
        self.combo_month.addItems(self.MONTHS)
        self.combo_month.setCurrentIndex(QDate.currentDate().month() - 1)
        self.combo_month.setFixedHeight(44)
        self.combo_month.setMinimumWidth(160)
        self.combo_month.setStyleSheet(
            "font-size: 14px; padding: 6px 12px; border: 2px solid #CCCCCC; "
            "border-radius: 8px; background: white;")
        lbl_y = QLabel("Year:")
        lbl_y.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.combo_year = QComboBox()
        current_year = QDate.currentDate().year()
        for y in range(current_year - 3, current_year + 2):
            self.combo_year.addItem(str(y))
        self.combo_year.setCurrentText(str(current_year))
        self.combo_year.setFixedHeight(44)
        self.combo_year.setMinimumWidth(110)
        self.combo_year.setStyleSheet(
            "font-size: 14px; padding: 6px 12px; border: 2px solid #CCCCCC; "
            "border-radius: 8px; background: white;")
        mfl.addWidget(lbl_m)
        mfl.addSpacing(8)
        mfl.addWidget(self.combo_month)
        mfl.addSpacing(20)
        mfl.addWidget(lbl_y)
        mfl.addSpacing(8)
        mfl.addWidget(self.combo_year)
        mfl.addStretch()
        self.month_frame.setVisible(False)
        bl2.addWidget(self.month_frame)

        # Wire radio buttons to show/hide frames
        self.rb_day.toggled.connect(
            lambda c: self.day_frame.setVisible(c))
        self.rb_month.toggled.connect(
            lambda c: self.month_frame.setVisible(c))

        bl2.addStretch()
        root.addWidget(body, 1)

        # ── Buttons ───────────────────────────────────────────
        btn_bar = QFrame()
        btn_bar.setStyleSheet(
            f"background-color: {config.DARK}; border-top: 3px solid {config.RED};")
        btn_bar.setFixedHeight(72)
        bbl = QHBoxLayout(btn_bar)
        bbl.setContentsMargins(24, 0, 24, 0)
        bbl.setSpacing(14)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(46)
        btn_cancel.setMinimumWidth(120)
        btn_cancel.setStyleSheet("""
            QPushButton { background:#555; color:white; border-radius:8px;
                border:none; font-size:14px; font-weight:bold; }
            QPushButton:hover { background:#888; }
        """)
        btn_cancel.clicked.connect(self.reject)

        label = "Generate PDF" if self.action == "pdf" else "Send by Email"
        icon2  = "📄" if self.action == "pdf" else "📧"
        btn_go = QPushButton(f"{icon2}   {label}")
        btn_go.setFixedHeight(46)
        btn_go.setMinimumWidth(220)
        color = "#C0392B" if self.action == "pdf" else "#1B4F72"
        hover = "#E74C3C" if self.action == "pdf" else "#2980B9"
        btn_go.setStyleSheet(f"""
            QPushButton {{ background:{color}; color:white; border-radius:8px;
                border:none; font-size:15px; font-weight:bold; }}
            QPushButton:hover {{ background:{hover}; }}
        """)
        btn_go.clicked.connect(self._execute)

        bbl.addWidget(btn_cancel)
        bbl.addStretch()
        bbl.addWidget(btn_go)
        root.addWidget(btn_bar)

    def _radio(self, text, color):
        rb = QRadioButton(text)
        rb.setStyleSheet(f"""
            QRadioButton {{
                font-size: 15px; font-weight: bold; color: #1A1A2E;
                padding: 8px 0;
            }}
            QRadioButton::indicator {{ width: 20px; height: 20px; }}
            QRadioButton::indicator:checked {{
                background-color: {color};
                border: 3px solid {color};
                border-radius: 10px;
            }}
            QRadioButton::indicator:unchecked {{
                background-color: white;
                border: 2px solid #CCCCCC;
                border-radius: 10px;
            }}
        """)
        return rb

    def _get_mode_value(self):
        if self.rb_day.isChecked():
            return "day", self.date_edit.date().toString("yyyy-MM-dd")
        elif self.rb_month.isChecked():
            month_num = str(self.combo_month.currentIndex() + 1).zfill(2)
            year      = self.combo_year.currentText()
            return "month", f"{year}-{month_num}"
        else:
            return "all", None

    def _get_period_label(self, mode, value):
        if mode == "day":
            from datetime import datetime
            return datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y (%A)")
        elif mode == "month":
            from datetime import datetime
            return datetime.strptime(value + "-01", "%Y-%m-%d").strftime("%B %Y")
        else:
            return "All Records (Complete History)"

    def _execute(self):
        mode, value = self._get_mode_value()
        period_label = self._get_period_label(mode, value)

        prog = QProgressDialog("Generating PDF report...", None, 0, 0, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setWindowTitle("Please Wait")
        prog.setCancelButton(None)
        prog.show()
        QApplication.processEvents()

        try:
            from reports.daily_report import generate_report
            pdf_path = generate_report(mode=mode, value=value)
        except Exception as e:
            prog.close()
            QMessageBox.critical(self, "PDF Error",
                f"Could not generate PDF:\n{str(e)}\n\n"
                "Make sure reportlab is installed:\n  pip install reportlab")
            return

        prog.close()

        if self.action == "pdf":
            QMessageBox.information(self, "PDF Ready",
                f"PDF generated!\n\nPeriod: {period_label}\n\nSaved to:\n{pdf_path}")
            try:
                import subprocess
                subprocess.Popen([pdf_path], shell=True)
            except Exception:
                pass
            self.accept()

        else:
            prog2 = QProgressDialog("Sending email...", None, 0, 0, self)
            prog2.setWindowModality(Qt.WindowModal)
            prog2.setWindowTitle("Sending")
            prog2.setCancelButton(None)
            prog2.show()
            QApplication.processEvents()

            try:
                from reports.email_sender import send_report
                ok, msg = send_report(pdf_path, mode, value, period_label)
            except Exception as e:
                prog2.close()
                QMessageBox.critical(self, "Email Error", f"Error:\n{str(e)}")
                return

            prog2.close()

            if ok:
                QMessageBox.information(self, "Email Sent", msg)
                self.accept()
            else:
                QMessageBox.critical(self, "Email Failed", msg)