"""App/MainWindowEx.py — JSON-based, 9-page navigation."""
from __future__ import annotations
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QMainWindow, QMessageBox
from ui.MainWindow import Ui_MainWindow
from ui.pages.dashboard_page     import DashboardPage
from ui.pages.members_page       import MembersPage
from ui.pages.packages_page      import PackagesPage
from ui.pages.subscriptions_page import SubscriptionsPage
from ui.pages.checkins_page      import CheckInsPage
from ui.pages.payments_page      import PaymentsPage
from ui.pages.trainers_page      import TrainersPage
from ui.pages.plans_page         import PlansPage
from ui.pages.reports_page       import ReportsPage


class MainWindowEx(QMainWindow):
    def __init__(self, logged_in_user=None):
        super().__init__()
        self._user = logged_in_user
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.removeWidget(self.ui.placeholderPage)

        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(False)
        self.bg_label.lower()
        self.bg_pixmap = QPixmap("ui/new_bg2.jpg")
        if not self.bg_pixmap.isNull():
            self.bg_label.setPixmap(self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))
            
            # Apply opacity to lower the visual weight of the image without darkening
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.35)
            self.bg_label.setGraphicsEffect(effect)

        pages = [
            (self.ui.btnDashboard,     DashboardPage(),     "Dashboard"),
            (self.ui.btnMembers,       MembersPage(),       "Members"),
            (self.ui.btnPackages,      PackagesPage(),      "Packages"),
            (self.ui.btnSubscriptions, SubscriptionsPage(), "Subscriptions"),
            (self.ui.btnCheckins,      CheckInsPage(),      "Check-ins"),
            (self.ui.btnPayments,      PaymentsPage(),      "Payments & Invoices"),
            (self.ui.btnTrainers,      TrainersPage(),      "Trainers"),
            (self.ui.btnPlans,         PlansPage(),         "Training Plans"),
            (self.ui.btnReports,       ReportsPage(),       "Reports & Analytics"),
        ]
        self._pages = pages
        for _, page, _ in pages:
            self.ui.stackedWidget.addWidget(page)
        for idx, (btn, _, title) in enumerate(pages):
            btn.clicked.connect(lambda _, i=idx, t=title: self._navigate(i, t))

        self.ui.btnLogout.clicked.connect(self._logout)

        if self._user:
            self.ui.userNameLabel.setText(str(self._user.username))
            self.ui.userRoleLabel.setText(str(self._user.role).upper())

        self._navigate(0, "Dashboard")
        self.ui.btnDashboard.setChecked(True)

        # Auto-expire in background
        from PyQt6.QtCore import QThread
        class _W(QThread):
            def run(self_):
                try: from libs.DataConnector import DataConnector; DataConnector().auto_expire_subscriptions()
                except: pass
        self._bg = _W(); self._bg.start()

    def _navigate(self, index: int, title: str):
        self.ui.stackedWidget.setCurrentIndex(index)
        self.ui.pageTitleLabel.setText(title)
        self._pages[index][1].refresh()

    def _logout(self):
        if QMessageBox.question(self, "Logout", "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.close()
            from App.MyApp import show_login
            show_login()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'bg_label') and hasattr(self, 'bg_pixmap') and not self.bg_pixmap.isNull():
            from PyQt6.QtCore import Qt
            self.bg_label.resize(self.size())
            self.bg_label.setPixmap(self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))
