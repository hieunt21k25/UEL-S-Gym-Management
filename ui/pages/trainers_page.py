"""ui/pages/trainers_page.py — CRUD for Trainers."""
from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QDialog, QFormLayout,
    QDialogButtonBox, QLineEdit, QMessageBox)
from libs.DataConnector import DataConnector
from model.Trainer import Trainer


class TrainersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._dc = DataConnector(); self._data: list[Trainer] = []; self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        tb = QHBoxLayout()
        add_btn = QPushButton("＋  Add Trainer"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addStretch(); tb.addWidget(add_btn); lay.addLayout(tb)
        self.table = QTableWidget(); self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","Full Name","Phone","Specialty","Schedule"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        bot = QHBoxLayout(); self.lbl = QLabel("")
        edit_btn = QPushButton("✏  Edit"); edit_btn.setMinimumHeight(34); edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("🗑  Delete"); del_btn.setObjectName("dangerBtn"); del_btn.setMinimumHeight(34); del_btn.clicked.connect(self._delete)
        bot.addWidget(self.lbl); bot.addStretch(); bot.addWidget(edit_btn); bot.addWidget(del_btn); lay.addLayout(bot)

    def refresh(self):
        self._data = self._dc.get_all_trainers(); self._populate()

    def _populate(self):
        self.table.setRowCount(0)
        for t in self._data:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([t.trainer_id, t.full_name, t.phone, t.specialty, t.availability_schedule]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.lbl.setText(f"{len(self._data)} trainer(s)")

    def _sel(self): return self.table.currentRow() if self.table.selectedItems() else None

    def _add(self):
        dlg = _TrainerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_trainers(self._data); self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a trainer."); return
        dlg = _TrainerDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result(); self._dc.save_trainers(self._data); self.refresh()

    def _delete(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a trainer."); return
        if QMessageBox.question(self, "Delete", f"Delete '{self._data[idx].full_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx); self._dc.save_trainers(self._data); self.refresh()


class _TrainerDialog(QDialog):
    def __init__(self, parent=None, t: Trainer = None):
        super().__init__(parent); self.setWindowTitle("Edit Trainer" if t else "Add Trainer"); self.setMinimumWidth(380)
        lay = QVBoxLayout(self); form = QFormLayout(); lay.addLayout(form)
        self.id_in   = QLineEdit(); self.id_in.setMinimumHeight(34)
        self.name_in = QLineEdit(); self.name_in.setMinimumHeight(34)
        self.phone_in= QLineEdit(); self.phone_in.setMinimumHeight(34)
        self.spec_in = QLineEdit(); self.spec_in.setMinimumHeight(34)
        self.sched_in= QLineEdit(); self.sched_in.setMinimumHeight(34)
        form.addRow("Trainer ID", self.id_in); form.addRow("Full Name", self.name_in)
        form.addRow("Phone",      self.phone_in); form.addRow("Specialty", self.spec_in)
        form.addRow("Schedule",   self.sched_in)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
        if t:
            self.id_in.setText(t.trainer_id); self.name_in.setText(t.full_name)
            self.phone_in.setText(t.phone); self.spec_in.setText(t.specialty); self.sched_in.setText(t.availability_schedule)

    def result(self) -> Trainer:
        return Trainer(self.id_in.text().strip(), self.name_in.text().strip(),
                       self.phone_in.text().strip(), self.spec_in.text().strip(), self.sched_in.text().strip())
