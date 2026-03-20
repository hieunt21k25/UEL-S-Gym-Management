"""
ui/pages/customers_page.py
──────────────────────────
Customers page — CRUD via DataConnector / JsonFileFactory.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from libs.DataConnector import DataConnector
from model.Customer import Customer


class CustomersPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dc = DataConnector()
        self._data: list[Customer] = []
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍  Search by name or code…")
        self.search_in.setMinimumHeight(36)
        self.search_in.setMinimumWidth(240)
        self.search_in.textChanged.connect(self._filter)

        add_btn = QPushButton("＋  Add Customer")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._add)

        toolbar.addWidget(self.search_in)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        lay.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Phone", "Email", "Identity"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)

        # Bottom bar
        bot = QHBoxLayout()
        self.status_lbl = QLabel("")
        edit_btn = QPushButton("✏  Edit")
        edit_btn.setMinimumHeight(34)
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("🗑  Delete")
        del_btn.setObjectName("dangerBtn")
        del_btn.setMinimumHeight(34)
        del_btn.clicked.connect(self._delete)

        bot.addWidget(self.status_lbl)
        bot.addStretch()
        bot.addWidget(edit_btn)
        bot.addWidget(del_btn)
        lay.addLayout(bot)

    def refresh(self) -> None:
        self._data = self._dc.get_all_customers()
        self._populate(self._data)

    def _populate(self, customers: list) -> None:
        self.table.setRowCount(0)
        for c in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(c.customer_code)))
            self.table.setItem(row, 1, QTableWidgetItem(str(c.customer_name)))
            self.table.setItem(row, 2, QTableWidgetItem(str(c.customer_phone)))
            self.table.setItem(row, 3, QTableWidgetItem(str(c.customer_email)))
            self.table.setItem(row, 4, QTableWidgetItem(str(c.customer_identity)))
        self.status_lbl.setText(f"{len(customers)} customer(s)")

    def _filter(self, text: str) -> None:
        t = text.lower()
        filtered = [c for c in self._data
                    if t in str(c.customer_code).lower()
                    or t in str(c.customer_name).lower()]
        self._populate(filtered)

    def _selected_index(self) -> int | None:
        if not self.table.selectedItems():
            return None
        return self.table.currentRow()

    def _add(self) -> None:
        dlg = _CustomerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result_customer())
            self._dc.save_customers(self._data)
            self.refresh()

    def _edit(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a customer first.")
            return
        dlg = _CustomerDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result_customer()
            self._dc.save_customers(self._data)
            self.refresh()

    def _delete(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a customer first.")
            return
        c = self._data[idx]
        if QMessageBox.question(
            self, "Delete", f"Delete customer '{c.customer_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx)
            self._dc.save_customers(self._data)
            self.refresh()


class _CustomerDialog(QDialog):
    def __init__(self, parent=None, c: Customer = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Customer" if c else "Add Customer")
        self.setMinimumWidth(360)
        self._build()
        if c:
            self._load(c)

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        form = QFormLayout()

        self.code_in     = QLineEdit(); self.code_in.setMinimumHeight(36)
        self.name_in     = QLineEdit(); self.name_in.setMinimumHeight(36)
        self.phone_in    = QLineEdit(); self.phone_in.setMinimumHeight(36)
        self.email_in    = QLineEdit(); self.email_in.setMinimumHeight(36)
        self.identity_in = QLineEdit(); self.identity_in.setMinimumHeight(36)

        form.addRow("Code",     self.code_in)
        form.addRow("Name",     self.name_in)
        form.addRow("Phone",    self.phone_in)
        form.addRow("Email",    self.email_in)
        form.addRow("Identity", self.identity_in)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load(self, c: Customer) -> None:
        self.code_in.setText(str(c.customer_code))
        self.name_in.setText(str(c.customer_name))
        self.phone_in.setText(str(c.customer_phone))
        self.email_in.setText(str(c.customer_email))
        self.identity_in.setText(str(c.customer_identity))

    def result_customer(self) -> Customer:
        return Customer(
            customer_code     = self.code_in.text().strip(),
            customer_name     = self.name_in.text().strip(),
            customer_phone    = self.phone_in.text().strip(),
            customer_email    = self.email_in.text().strip(),
            customer_identity = self.identity_in.text().strip(),
        )
