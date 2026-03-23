"""
ui/dialogs/login_dialog.py — DataConnector auth (JSON-based).
"""
from __future__ import annotations
from PyQt6.QtWidgets import QDialog
from ui.Login import Ui_LoginDialog
from libs.DataConnector import DataConnector


class LoginDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)
        self.logged_in_user = None
        self.ui.signInButton.clicked.connect(self._submit)
        self.ui.passwordInput.returnPressed.connect(self._submit)
        self.ui.registerButton.clicked.connect(self._open_register)

        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(False)
        self.bg_label.lower()
        self.bg_pixmap = QPixmap("ui/bg.png")
        if not self.bg_pixmap.isNull():
            self.bg_label.setPixmap(self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))

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

    def _submit(self) -> None:
        username = self.ui.usernameInput.text().strip()
        password = self.ui.passwordInput.text()
        if not username or not password:
            self.ui.errorLabel.setText("Please enter username and password.")
            return
        user = DataConnector().login(username, password)
        if user:
            self.logged_in_user = user
            self.ui.errorLabel.setText("")
            self.accept()
        else:
            self.ui.errorLabel.setText("Invalid username or password.")

    def _open_register(self) -> None:
        from ui.dialogs.register_dialog import RegisterDialog
        dlg = RegisterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.ui.usernameInput.setText(dlg.ui.usernameInput.text().strip())
            self.ui.passwordInput.clear()
            self.ui.passwordInput.setFocus()
