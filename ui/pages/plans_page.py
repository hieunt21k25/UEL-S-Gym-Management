"""ui/pages/plans_page.py — Training Plans CRUD."""
from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QDialog, QFormLayout,
    QDialogButtonBox, QLineEdit, QTextEdit, QMessageBox)
from libs.DataConnector import DataConnector
from model.Plan import Plan


class PlansPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._dc = DataConnector(); self._data: list[Plan] = []; self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        tb = QHBoxLayout()
        add_btn = QPushButton("＋  Add Plan"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addStretch(); tb.addWidget(add_btn); lay.addLayout(tb)
        self.table = QTableWidget(); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Plan ID","Member ID","Trainer ID","Goal","Schedule","Notes"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        bot = QHBoxLayout(); self.lbl = QLabel("")
        edit_btn = QPushButton("✏  Edit"); edit_btn.setMinimumHeight(34); edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("🗑  Delete"); del_btn.setObjectName("dangerBtn"); del_btn.setMinimumHeight(34); del_btn.clicked.connect(self._delete)
        bot.addWidget(self.lbl); bot.addStretch(); bot.addWidget(edit_btn); bot.addWidget(del_btn); lay.addLayout(bot)

    def refresh(self):
        self._data = self._dc.get_all_plans(); self._populate()

    def _populate(self):
        self.table.setRowCount(0)
        for p in self._data:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([p.plan_id, p.member_id, p.trainer_id, p.goal, p.weekly_schedule_json, p.notes]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.lbl.setText(f"{len(self._data)} plan(s)")

    def _sel(self): return self.table.currentRow() if self.table.selectedItems() else None

    def _add(self):
        dlg = _PlanDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_plans(self._data); self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a plan."); return
        dlg = _PlanDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result(); self._dc.save_plans(self._data); self.refresh()

    def _delete(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a plan."); return
        if QMessageBox.question(self, "Delete", "Delete this training plan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx); self._dc.save_plans(self._data); self.refresh()


class _PlanDialog(QDialog):
    def __init__(self, parent=None, p: Plan = None):
        super().__init__(parent); self.setWindowTitle("Edit Plan" if p else "Add Plan"); self.setMinimumWidth(420)
        lay = QVBoxLayout(self); form = QFormLayout(); lay.addLayout(form)
        self.id_in    = QLineEdit(); self.id_in.setMinimumHeight(34)
        self.mem_in   = QLineEdit(); self.mem_in.setMinimumHeight(34)
        self.train_in = QLineEdit(); self.train_in.setMinimumHeight(34)
        self.goal_in  = QLineEdit(); self.goal_in.setMinimumHeight(34)
        self.sched_in = QTextEdit(); self.sched_in.setPlaceholderText('{"Mon":"Chest","Wed":"Back","Fri":"Legs"}'); self.sched_in.setMaximumHeight(80)
        self.notes_in = QLineEdit(); self.notes_in.setMinimumHeight(34)
        form.addRow("Plan ID",    self.id_in); form.addRow("Member ID",  self.mem_in)
        form.addRow("Trainer ID", self.train_in); form.addRow("Goal",    self.goal_in)
        form.addRow("Schedule (JSON)", self.sched_in); form.addRow("Notes", self.notes_in)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
        if p:
            self.id_in.setText(p.plan_id); self.mem_in.setText(p.member_id)
            self.train_in.setText(p.trainer_id); self.goal_in.setText(p.goal)
            self.sched_in.setPlainText(p.weekly_schedule_json); self.notes_in.setText(p.notes)

    def result(self) -> Plan:
        return Plan(self.id_in.text().strip(), self.mem_in.text().strip(),
                    self.train_in.text().strip(), self.goal_in.text().strip(),
                    self.sched_in.toPlainText().strip(), self.notes_in.text().strip())
