"""
ui/pages/settings_page.py
─────────────────────────
Settings page — shows current user info, API status, and logout shortcut.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ui.api_client import client
from ui.pages.base_page import BasePage


class _CheckWorker(QThread):
    result = pyqtSignal(bool)
    def run(self): self.result.emit(client.is_alive())


class SettingsPage(BasePage):
    PAGE_TITLE = "Settings"

    def build(self):
        # ── Account card ──────────────────────────────────────────────────────
        acc_card = QFrame(); acc_card.setObjectName("card")
        acl = QVBoxLayout(acc_card); acl.setContentsMargins(28, 24, 28, 24); acl.setSpacing(14)

        acc_title = QLabel("👤  Account")
        acc_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        acc_title.setStyleSheet("color:#e2e8f0;")

        self._user_lbl = QLabel("—")
        self._user_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Black))
        self._user_lbl.setStyleSheet("color:#34D399;")

        self._role_lbl = QLabel("—")
        self._role_lbl.setStyleSheet("color:#64748b;font-size:12px;font-weight:700;letter-spacing:1px;")

        acl.addWidget(acc_title)
        acl.addWidget(self._user_lbl)
        acl.addWidget(self._role_lbl)
        self.layout_.addWidget(acc_card)

        # ── Backend status card ───────────────────────────────────────────────
        api_card = QFrame(); api_card.setObjectName("card")
        apl = QVBoxLayout(api_card); apl.setContentsMargins(28, 24, 28, 24); apl.setSpacing(14)

        api_title = QLabel("🔌  Backend Connection")
        api_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        api_title.setStyleSheet("color:#e2e8f0;")

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("API URL:"))
        self._url_lbl = QLabel(client.base_url)
        self._url_lbl.setStyleSheet("color:#818CF8;")
        url_row.addWidget(self._url_lbl); url_row.addStretch()

        status_row = QHBoxLayout()
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet("color:#64748b;font-size:18px;")
        self._status_lbl = QLabel("Checking…")
        self._status_lbl.setStyleSheet("color:#64748b;font-size:13px;")
        check_btn = QPushButton("Re-check")
        check_btn.setObjectName("secondaryBtn"); check_btn.clicked.connect(self._check_backend)
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        status_row.addWidget(check_btn)

        apl.addWidget(api_title)
        apl.addLayout(url_row)
        apl.addLayout(status_row)
        self.layout_.addWidget(api_card)

        self.layout_.addStretch()

    def refresh(self):
        self._user_lbl.setText(client.username or "—")
        self._role_lbl.setText((client.role or "—").upper())
        self._check_backend()

    def _check_backend(self):
        self._status_dot.setStyleSheet("color:#FBBF24;font-size:18px;")
        self._status_lbl.setText("Checking…")
        self._w = _CheckWorker()
        self._w.result.connect(self._set_status)
        self._w.start()

    def _set_status(self, alive: bool):
        if alive:
            self._status_dot.setStyleSheet("color:#34D399;font-size:18px;")
            self._status_lbl.setText("Connected  ✓")
        else:
            self._status_dot.setStyleSheet("color:#F87171;font-size:18px;")
            self._status_lbl.setText("Not reachable  ✗")
