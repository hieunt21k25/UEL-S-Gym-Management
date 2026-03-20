"""
App/MainWindow.py
─────────────────
UI-ONLY layer — Ui_MainWindow class with setupUi().
Defines the main window skeleton: sidebar, stackedWidget, topbar.
NO logic. NO signals. NO API calls.

Sidebar pages:
  - Employees   (btnEmployees)
  - Customers   (btnCustomers)
  - Bookings    (btnBookings)
  - Rooms       (btnRooms)
"""
from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QStackedWidget,
    QVBoxLayout, QWidget,
)


class Ui_MainWindow:
    """Programmatic equivalent of a Qt Designer .ui file."""

    def setupUi(self, window: QMainWindow) -> None:
        window.setObjectName("MainWindow")
        window.setWindowTitle("Gym Manager")
        window.resize(1200, 760)
        window.setMinimumSize(900, 600)

        self.centralWidget = QWidget(window)
        self.centralWidget.setObjectName("centralWidget")
        window.setCentralWidget(self.centralWidget)

        root = QHBoxLayout(self.centralWidget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        sbl = QVBoxLayout(self.sidebar)
        sbl.setContentsMargins(12, 28, 12, 20)
        sbl.setSpacing(4)

        # Brand
        self.brandLabel = QLabel("💪 Gym Manager")
        self.brandLabel.setObjectName("brandLabel")
        self.brandLabel.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        # User pill
        self.userPill = QFrame()
        self.userPill.setObjectName("userPill")
        pill = QVBoxLayout(self.userPill)
        pill.setContentsMargins(12, 8, 12, 8)
        pill.setSpacing(2)
        self.userNameLabel = QLabel("—")
        self.userNameLabel.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.userRoleLabel = QLabel("—")
        self.userRoleLabel.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        pill.addWidget(self.userNameLabel)
        pill.addWidget(self.userRoleLabel)

        # Nav section label
        navLabel = QLabel("NAVIGATION")
        navLabel.setObjectName("navSectionLabel")
        navLabel.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))

        # Nav buttons
        self.btnEmployees = self._nav("👤", "Employees")
        self.btnCustomers = self._nav("👥", "Customers")
        self.btnBookings  = self._nav("📅", "Bookings")
        self.btnRooms     = self._nav("🏠", "Rooms")

        # Logout
        self.btnLogout = QPushButton("⏻   Logout")
        self.btnLogout.setObjectName("dangerBtn")
        self.btnLogout.setMinimumHeight(42)
        self.btnLogout.setFont(QFont("Segoe UI", 12))

        sbl.addWidget(self.brandLabel)
        sbl.addWidget(self.userPill)
        sbl.addWidget(navLabel)
        for btn in self._all_nav():
            sbl.addWidget(btn)
        sbl.addStretch()
        sbl.addWidget(self.btnLogout)

        # ── Content area ──────────────────────────────────────────────────────
        self.contentArea = QWidget()
        self.contentArea.setObjectName("contentArea")
        cl = QVBoxLayout(self.contentArea)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Top bar
        self.topBar = QFrame()
        self.topBar.setObjectName("topBar")
        self.topBar.setFixedHeight(56)
        tbl = QHBoxLayout(self.topBar)
        tbl.setContentsMargins(24, 0, 24, 0)
        self.pageTitleLabel = QLabel("Employees")
        self.pageTitleLabel.setObjectName("pageTitleLabel")
        self.pageTitleLabel.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        tbl.addWidget(self.pageTitleLabel)
        tbl.addStretch()

        # Stacked widget
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.setObjectName("stackedWidget")

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(24, 16, 24, 16)
        wl.setSpacing(0)
        wl.addWidget(self.stackedWidget)

        cl.addWidget(self.topBar)
        cl.addWidget(wrapper)

        root.addWidget(self.sidebar)
        root.addWidget(self.contentArea)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _nav(self, icon: str, label: str) -> QPushButton:
        btn = QPushButton(f"   {icon}   {label}")
        btn.setObjectName("navBtn")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setMinimumHeight(44)
        btn.setFont(QFont("Segoe UI", 12))
        return btn

    def _all_nav(self) -> list:
        return [self.btnEmployees, self.btnCustomers,
                self.btnBookings,  self.btnRooms]
