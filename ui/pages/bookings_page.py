"""
ui/pages/bookings_page.py
─────────────────────────
Bookings page — CRUD via DataConnector / JsonFileFactory.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from libs.DataConnector import DataConnector
from model.Booking import Booking


class BookingsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dc = DataConnector()
        self._data: list[Booking] = []
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍  Search by customer code or room…")
        self.search_in.setMinimumHeight(36)
        self.search_in.setMinimumWidth(260)
        self.search_in.textChanged.connect(self._filter)

        add_btn = QPushButton("＋  Add Booking")
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
        self.table.setHorizontalHeaderLabels(
            ["Customer Code", "Room Code", "Start Date", "End Date"])
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
        self._data = self._dc.get_all_bookings()
        self._populate(self._data)

    def _populate(self, bookings: list) -> None:
        self.table.setRowCount(0)
        for b in bookings:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(b.customer_code)))
            self.table.setItem(row, 1, QTableWidgetItem(str(b.room_code)))
            self.table.setItem(row, 2, QTableWidgetItem(str(b.start_date)))
            self.table.setItem(row, 3, QTableWidgetItem(str(b.end_date)))
        self.status_lbl.setText(f"{len(bookings)} booking(s)")

    def _filter(self, text: str) -> None:
        t = text.lower()
        filtered = [b for b in self._data
                    if t in str(b.customer_code).lower()
                    or t in str(b.room_code).lower()]
        self._populate(filtered)

    def _selected_index(self) -> int | None:
        if not self.table.selectedItems():
            return None
        return self.table.currentRow()

    def _add(self) -> None:
        dlg = _BookingDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result_booking())
            self._dc.save_bookings(self._data)
            self.refresh()

    def _edit(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a booking first.")
            return
        dlg = _BookingDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result_booking()
            self._dc.save_bookings(self._data)
            self.refresh()

    def _delete(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a booking first.")
            return
        b = self._data[idx]
        if QMessageBox.question(
            self, "Delete",
            f"Delete booking for customer '{b.customer_code}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx)
            self._dc.save_bookings(self._data)
            self.refresh()


class _BookingDialog(QDialog):
    def __init__(self, parent=None, b: Booking = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Booking" if b else "Add Booking")
        self.setMinimumWidth(360)
        self._build()
        if b:
            self._load(b)

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        form = QFormLayout()

        self.cust_in  = QLineEdit(); self.cust_in.setMinimumHeight(36)
        self.room_in  = QLineEdit(); self.room_in.setMinimumHeight(36)
        self.start_in = QLineEdit(); self.start_in.setMinimumHeight(36)
        self.start_in.setPlaceholderText("YYYY-MM-DD")
        self.end_in   = QLineEdit(); self.end_in.setMinimumHeight(36)
        self.end_in.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Customer Code", self.cust_in)
        form.addRow("Room Code",     self.room_in)
        form.addRow("Start Date",    self.start_in)
        form.addRow("End Date",      self.end_in)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load(self, b: Booking) -> None:
        self.cust_in.setText(str(b.customer_code))
        self.room_in.setText(str(b.room_code))
        self.start_in.setText(str(b.start_date))
        self.end_in.setText(str(b.end_date))

    def result_booking(self) -> Booking:
        return Booking(
            customer_code = self.cust_in.text().strip(),
            room_code     = self.room_in.text().strip(),
            start_date    = self.start_in.text().strip(),
            end_date      = self.end_in.text().strip(),
        )
