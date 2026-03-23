"""
ui/pages/employees_page.py
──────────────────────────
Employees page — CRUD via DataConnector / JsonFileFactory.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from libs.DataConnector import DataConnector
from model.Employee import Employee


class EmployeesPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dc = DataConnector()
        self._build()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍  Search by username or ID…")
        self.search_in.setMinimumHeight(36)
        self.search_in.setMinimumWidth(240)
        self.search_in.textChanged.connect(self._filter)

        add_btn = QPushButton("＋  Add Employee")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._add)

        toolbar.addWidget(self.search_in)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        lay.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Employee ID", "Role", "Username", "Password"])
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

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._data = self._dc.get_all_employees()
        self._populate(self._data)

    def _populate(self, employees: list) -> None:
        self.table.setRowCount(0)
        for emp in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(emp.EmployeeId)))
            self.table.setItem(row, 1, QTableWidgetItem(str(emp.EmployeeRole)))
            self.table.setItem(row, 2, QTableWidgetItem(str(emp.UserName)))
            self.table.setItem(row, 3, QTableWidgetItem(str(emp.Password)))
        self.status_lbl.setText(f"{len(employees)} employee(s)")

    def _filter(self, text: str) -> None:
        t = text.lower()
        filtered = [e for e in self._data
                    if t in str(e.EmployeeId).lower() or t in str(e.UserName).lower()]
        self._populate(filtered)

    def _selected_index(self) -> int | None:
        rows = self.table.selectedItems()
        if not rows:
            return None
        return self.table.currentRow()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add(self) -> None:
        dlg = _EmployeeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            emp = dlg.result_employee()
            self._data.append(emp)
            self._dc.save_employees(self._data)
            self.refresh()

    def _edit(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select an employee first.")
            return
        dlg = _EmployeeDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result_employee()
            self._dc.save_employees(self._data)
            self.refresh()

    def _delete(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select an employee first.")
            return
        emp = self._data[idx]
        if QMessageBox.question(
            self, "Delete",
            f"Delete employee '{emp.UserName}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx)
            self._dc.save_employees(self._data)
            self.refresh()


class _EmployeeDialog(QDialog):
    def __init__(self, parent=None, emp: Employee = None) -> None:
        super().__init__(parent)
        self._emp = emp
        self.setWindowTitle("Edit Employee" if emp else "Add Employee")
        self.setMinimumWidth(360)
        self._build()
        if emp:
            self._load(emp)

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        form = QFormLayout()

        self.id_in   = QLineEdit(); self.id_in.setMinimumHeight(36)
        self.role_in = QLineEdit(); self.role_in.setMinimumHeight(36)
        self.user_in = QLineEdit(); self.user_in.setMinimumHeight(36)
        self.pass_in = QLineEdit(); self.pass_in.setMinimumHeight(36)

        form.addRow("Employee ID", self.id_in)
        form.addRow("Role",        self.role_in)
        form.addRow("Username",    self.user_in)
        form.addRow("Password",    self.pass_in)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load(self, emp: Employee) -> None:
        self.id_in.setText(str(emp.EmployeeId))
        self.role_in.setText(str(emp.EmployeeRole))
        self.user_in.setText(str(emp.UserName))
        self.pass_in.setText(str(emp.Password))

    def result_employee(self) -> Employee:
        return Employee(
            EmployeeId   = self.id_in.text().strip(),
            EmployeeRole = self.role_in.text().strip(),
            UserName     = self.user_in.text().strip(),
            Password     = self.pass_in.text(),
        )
