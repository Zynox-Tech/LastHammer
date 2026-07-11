import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QMessageBox, QFrame, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import database
import config


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Last Hammer — Settings")
        self.setMinimumWidth(580)
        self.setMinimumHeight(500)
        self.setModal(True)
        self._build_ui()
        self._load_settings()

    # ─────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title bar ─────────────────────────────────────────
        title_bar = QFrame()
        title_bar.setStyleSheet(f"background-color: {config.DARK};")
        title_bar.setFixedHeight(72)
        tl = QHBoxLayout(title_bar)
        tl.setContentsMargins(28, 0, 28, 0)

        lbl = QLabel("⚙   Application Settings")
        lbl.setStyleSheet(
            f"color: {config.WHITE}; font-size: 22px; font-weight: bold;")
        tl.addWidget(lbl)
        root.addWidget(title_bar)

        # ── Tabs ──────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #F5F5F5;
            }
            QTabBar::tab {
                background: #DDDDDD;
                color: #333333;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1A1A2E;
                color: white;
            }
            QTabBar::tab:hover {
                background: #BBBBBB;
            }
        """)
        self.tabs.addTab(self._make_email_tab(),   "📧  Email")
        self.tabs.addTab(self._make_company_tab(), "🏢  Company")
        self.tabs.addTab(self._make_site_tab(),    "⚙  Site Settings")

        root.addWidget(self.tabs, 1)

        # ── Save / Close buttons ──────────────────────────────
        btn_frame = QFrame()
        btn_frame.setStyleSheet(
            f"background-color: {config.DARK}; "
            f"border-top: 3px solid {config.RED};")
        btn_frame.setFixedHeight(72)
        bl = QHBoxLayout(btn_frame)
        bl.setContentsMargins(28, 0, 28, 0)
        bl.setSpacing(16)

        btn_cancel = QPushButton("Close without Saving")
        btn_cancel.setMinimumHeight(44)
        btn_cancel.setMinimumWidth(200)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #555555; color: white;
                border-radius: 8px; border: none;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #888888; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾   Save All Settings")
        btn_save.setMinimumHeight(44)
        btn_save.setMinimumWidth(220)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #1E8449; color: white;
                border-radius: 8px; border: none;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #27AE60; }
        """)
        btn_save.clicked.connect(self._save_all)

        bl.addWidget(btn_cancel)
        bl.addStretch()
        bl.addWidget(btn_save)
        root.addWidget(btn_frame)

    # ── Email Tab ─────────────────────────────────────────────
    def _make_email_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #F5F5F5;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(20)

        # Info box
        info = QFrame()
        info.setStyleSheet("""
            QFrame {
                background-color: #EBF5FB;
                border: 2px solid #AED6F1;
                border-radius: 8px;
            }
        """)
        il = QVBoxLayout(info)
        il.setContentsMargins(16, 12, 16, 12)
        lbl_info = QLabel(
            "📌  The app uses Gmail to send daily reports.\n"
            "You need a Gmail 'App Password' (not your normal Gmail password).\n"
            "Go to: myaccount.google.com → Security → App Passwords → Create one.")
        lbl_info.setStyleSheet(
            "color: #1B4F72; font-size: 13px; background: transparent; border: none;")
        lbl_info.setWordWrap(True)
        il.addWidget(lbl_info)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)

        def L(text):
            l = QLabel(text)
            l.setStyleSheet("font-size: 15px; font-weight: bold; color: #1A1A2E;")
            return l

        def inp(placeholder=""):
            f = QLineEdit()
            f.setPlaceholderText(placeholder)
            f.setMinimumHeight(44)
            f.setStyleSheet("""
                QLineEdit {
                    font-size: 14px; padding: 8px 12px;
                    border: 2px solid #CCCCCC; border-radius: 8px;
                    background: white;
                }
                QLineEdit:focus { border: 2px solid #C0392B; }
            """)
            return f

        self.inp_sender_email = inp("e.g. lasthammer.reports@gmail.com")
        form.addRow(L("Sender Gmail:"), self.inp_sender_email)

        self.inp_app_password = inp("16-character App Password from Google")
        self.inp_app_password.setEchoMode(QLineEdit.Password)
        form.addRow(L("Gmail App Password:"), self.inp_app_password)

        # Toggle show/hide password
        btn_show = QPushButton("Show Password")
        btn_show.setCheckable(True)
        btn_show.setMinimumHeight(36)
        btn_show.setStyleSheet("""
            QPushButton {
                background: #DDDDDD; color: #333; border-radius: 6px;
                border: none; font-size: 13px; padding: 6px 14px;
            }
            QPushButton:checked { background: #1B4F72; color: white; }
        """)
        btn_show.toggled.connect(
            lambda checked: self.inp_app_password.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password))
        form.addRow("", btn_show)

        self.inp_owner_email = inp("e.g. owner@gmail.com  (report goes here)")
        form.addRow(L("Owner's Email:"), self.inp_owner_email)

        layout.addLayout(form)
        layout.addStretch()
        return tab

    # ── Company Tab ───────────────────────────────────────────
    def _make_company_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #F5F5F5;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(20)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)

        def L(text):
            l = QLabel(text)
            l.setStyleSheet("font-size: 15px; font-weight: bold; color: #1A1A2E;")
            return l

        def inp(placeholder=""):
            f = QLineEdit()
            f.setPlaceholderText(placeholder)
            f.setMinimumHeight(44)
            f.setStyleSheet("""
                QLineEdit {
                    font-size: 14px; padding: 8px 12px;
                    border: 2px solid #CCCCCC; border-radius: 8px;
                    background: white;
                }
                QLineEdit:focus { border: 2px solid #C0392B; }
            """)
            return f

        self.inp_company_name = inp("e.g. Last Hammer")
        form.addRow(L("Company Name:"), self.inp_company_name)

        self.inp_company_address = inp("e.g. Office No 28, Sherpawo Plaza, Abbottabad")
        form.addRow(L("Address:"), self.inp_company_address)

        self.inp_company_phone = inp("e.g. 0314-5014407")
        form.addRow(L("Phone:"), self.inp_company_phone)

        self.inp_manager_name = inp("e.g. Site Manager Name")
        form.addRow(L("Site Manager:"), self.inp_manager_name)

        layout.addLayout(form)
        layout.addStretch()
        return tab

    # ── Site Settings Tab ─────────────────────────────────────
    def _make_site_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #F5F5F5;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(20)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)

        def L(text):
            l = QLabel(text)
            l.setStyleSheet("font-size: 15px; font-weight: bold; color: #1A1A2E;")
            return l

        # Excavator rate
        lbl_exc = L("Excavator Rate (PKR/hr):")
        self.inp_exc_rate = QDoubleSpinBox()
        self.inp_exc_rate.setRange(0, 99999)
        self.inp_exc_rate.setDecimals(0)
        self.inp_exc_rate.setPrefix("PKR ")
        self.inp_exc_rate.setSuffix(" / hr")
        self.inp_exc_rate.setMinimumHeight(44)
        self.inp_exc_rate.setStyleSheet(
            "font-size: 14px; padding: 8px 12px; "
            "border: 2px solid #CCCCCC; border-radius: 8px; background: white;")
        form.addRow(lbl_exc, self.inp_exc_rate)

        info = QLabel(
            "This rate is used as the default when adding\n"
            "new Excavator entries. You can still change it per entry.")
        info.setStyleSheet("color: #888888; font-size: 13px; font-style: italic;")
        form.addRow("", info)

        layout.addLayout(form)
        layout.addStretch()
        return tab

    # ─────────────────────────────────────────────────────────
    def _load_settings(self):
        self.inp_sender_email.setText(database.get_setting("sender_email"))
        self.inp_app_password.setText(database.get_setting("gmail_app_password"))
        self.inp_owner_email.setText(database.get_setting("owner_email"))
        self.inp_company_name.setText(
            database.get_setting("company_name") or "Last Hammer")
        self.inp_company_address.setText(
            database.get_setting("company_address") or "")
        self.inp_company_phone.setText(
            database.get_setting("company_phone") or "")
        self.inp_manager_name.setText(
            database.get_setting("manager_name") or "")
        rate = database.get_setting("excavator_rate") or "2200"
        self.inp_exc_rate.setValue(float(rate))

    def _save_all(self):
        database.save_setting("sender_email",       self.inp_sender_email.text().strip())
        database.save_setting("gmail_app_password", self.inp_app_password.text().strip())
        database.save_setting("owner_email",        self.inp_owner_email.text().strip())
        database.save_setting("company_name",       self.inp_company_name.text().strip())
        database.save_setting("company_address",    self.inp_company_address.text().strip())
        database.save_setting("company_phone",      self.inp_company_phone.text().strip())
        database.save_setting("manager_name",       self.inp_manager_name.text().strip())
        database.save_setting("excavator_rate",     str(int(self.inp_exc_rate.value())))

        QMessageBox.information(
            self, "Saved",
            "✅  All settings saved successfully!")
        self.accept()