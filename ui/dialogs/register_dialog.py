"""
ui/dialogs/register_dialog.py — DataConnector register (JSON-based).
"""
from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QMessageBox
from ui.Register import Ui_RegisterDialog
from libs.DataConnector import DataConnector


class RegisterDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_RegisterDialog()
        self.ui.setupUi(self)
        self.ui.roleComboBox.addItems(["staff", "admin"])
        self.ui.createButton.clicked.connect(self._submit)
        self.ui.backButton.clicked.connect(self.reject)

    def _submit(self) -> None:
        username = self.ui.usernameInput.text().strip()
        email    = self.ui.emailInput.text().strip()
        password = self.ui.passwordInput.text()
        role     = self.ui.roleComboBox.currentText()
        if not username or not password:
            self.ui.errorLabel.setText("Username and password are required.")
            return
        user = DataConnector().register(username, email, password, role)
        if user:
            QMessageBox.information(self, "Success", f"Account '{username}' created! You can now log in.")
            self.accept()
        else:
            self.ui.errorLabel.setText(f"Username '{username}' is already taken.")
