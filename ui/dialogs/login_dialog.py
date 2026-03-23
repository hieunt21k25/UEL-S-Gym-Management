"""
ui/dialogs/login_dialog.py — DataConnector auth (JSON-based).
"""
from __future__ import annotations
from pathlib import Path
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

        self._Qt = Qt
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(False)
        _bg_path = str(Path(__file__).resolve().parent.parent / "bg.png")
        self.bg_pixmap = QPixmap(_bg_path)
        self._apply_bg()
        self.bg_label.lower()

    def _apply_bg(self):
        """Resize bg_label to fill the dialog and repaint."""
        if not hasattr(self, 'bg_pixmap') or self.bg_pixmap.isNull():
            return
        self.bg_label.resize(self.size())
        self.bg_label.setPixmap(self.bg_pixmap.scaled(
            self.size(),
            self._Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            self._Qt.TransformationMode.SmoothTransformation
        ))
        self.bg_label.lower()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_bg()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_bg()

    def _submit(self) -> None:
        username = self.ui.usernameInput.text().strip()
        password = self.ui.passwordInput.text()
        if not username or not password:
            self.ui.errorLabel.setText("Please enter username and password.")
            return

        selected_role = self.ui.roleCombo.currentText().lower()  # "admin" or "staff"

        user = DataConnector().login(username, password)
        if user:
            actual_role = str(user.role).lower()
            if actual_role != selected_role:
                self.ui.errorLabel.setText(
                    f"Access denied: your account role is '{actual_role.capitalize()}', "
                    f"not '{selected_role.capitalize()}'."
                )
                return
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
