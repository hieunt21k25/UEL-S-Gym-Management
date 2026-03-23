"""
ui/pages/rooms_page.py
──────────────────────
Rooms page — CRUD via DataConnector / JsonFileFactory.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from libs.DataConnector import DataConnector
from model.Room import Room


class RoomsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dc = DataConnector()
        self._data: list[Room] = []
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍  Search by room code or name…")
        self.search_in.setMinimumHeight(36)
        self.search_in.setMinimumWidth(240)
        self.search_in.textChanged.connect(self._filter)

        add_btn = QPushButton("＋  Add Room")
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
            ["Room Code", "Room Name", "Capacity", "Description"])
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
        self._data = self._dc.get_all_rooms()
        self._populate(self._data)

    def _populate(self, rooms: list) -> None:
        self.table.setRowCount(0)
        for r in rooms:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r.room_code)))
            self.table.setItem(row, 1, QTableWidgetItem(str(r.room_name)))
            self.table.setItem(row, 2, QTableWidgetItem(str(r.capacity)))
            self.table.setItem(row, 3, QTableWidgetItem(str(r.description)))
        self.status_lbl.setText(f"{len(rooms)} room(s)")

    def _filter(self, text: str) -> None:
        t = text.lower()
        filtered = [r for r in self._data
                    if t in str(r.room_code).lower()
                    or t in str(r.room_name).lower()]
        self._populate(filtered)

    def _selected_index(self) -> int | None:
        if not self.table.selectedItems():
            return None
        return self.table.currentRow()

    def _add(self) -> None:
        dlg = _RoomDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result_room())
            self._dc.save_rooms(self._data)
            self.refresh()

    def _edit(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a room first.")
            return
        dlg = _RoomDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result_room()
            self._dc.save_rooms(self._data)
            self.refresh()

    def _delete(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a room first.")
            return
        r = self._data[idx]
        if QMessageBox.question(
            self, "Delete", f"Delete room '{r.room_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx)
            self._dc.save_rooms(self._data)
            self.refresh()


class _RoomDialog(QDialog):
    def __init__(self, parent=None, r: Room = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Room" if r else "Add Room")
        self.setMinimumWidth(360)
        self._build()
        if r:
            self._load(r)

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        form = QFormLayout()

        self.code_in = QLineEdit(); self.code_in.setMinimumHeight(36)
        self.name_in = QLineEdit(); self.name_in.setMinimumHeight(36)
        self.cap_in  = QLineEdit(); self.cap_in.setMinimumHeight(36)
        self.desc_in = QLineEdit(); self.desc_in.setMinimumHeight(36)

        form.addRow("Room Code",   self.code_in)
        form.addRow("Room Name",   self.name_in)
        form.addRow("Capacity",    self.cap_in)
        form.addRow("Description", self.desc_in)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load(self, r: Room) -> None:
        self.code_in.setText(str(r.room_code))
        self.name_in.setText(str(r.room_name))
        self.cap_in.setText(str(r.capacity))
        self.desc_in.setText(str(r.description))

    def result_room(self) -> Room:
        return Room(
            room_code   = self.code_in.text().strip(),
            room_name   = self.name_in.text().strip(),
            capacity    = self.cap_in.text().strip(),
            description = self.desc_in.text().strip(),
        )
