"""ui/pages/packages_page.py — CRUD for Packages (admin only visible note)."""
from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit, QPushButton, QLabel, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox)
from libs.DataConnector import DataConnector
from model.Package import Package


class PackagesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector(); self._data: list[Package] = []; self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        tb = QHBoxLayout()
        add_btn = QPushButton("＋  Add Package"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addStretch(); tb.addWidget(add_btn); lay.addLayout(tb)
        self.table = QTableWidget(); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID","Name","Duration Unit","Duration","Price (VND)","Description"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        bot = QHBoxLayout(); self.lbl = QLabel("")
        edit_btn = QPushButton("✏  Edit"); edit_btn.setMinimumHeight(34); edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("🗑  Delete"); del_btn.setObjectName("dangerBtn"); del_btn.setMinimumHeight(34); del_btn.clicked.connect(self._delete)
        bot.addWidget(self.lbl); bot.addStretch(); bot.addWidget(edit_btn); bot.addWidget(del_btn)
        lay.addLayout(bot)

    def refresh(self):
        self._data = self._dc.get_all_packages(); self._populate()

    def _populate(self):
        self.table.setRowCount(0)
        for p in self._data:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([p.package_id, p.name, p.duration_unit, p.duration_value, f"{float(p.price):,.0f}", p.description]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.lbl.setText(f"{len(self._data)} package(s)")

    def _sel(self): return self.table.currentRow() if self.table.selectedItems() else None

    def _add(self):
        dlg = _PackageDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_packages(self._data); self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a package."); return
        dlg = _PackageDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result(); self._dc.save_packages(self._data); self.refresh()

    def _delete(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a package."); return
        if QMessageBox.question(self, "Delete", f"Delete '{self._data[idx].name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx); self._dc.save_packages(self._data); self.refresh()


class _PackageDialog(QDialog):
    def __init__(self, parent=None, p: Package = None):
        super().__init__(parent); self.setWindowTitle("Edit Package" if p else "Add Package"); self.setMinimumWidth(380)
        lay = QVBoxLayout(self); form = QFormLayout(); lay.addLayout(form)
        self.id_in  = QLineEdit(); self.id_in.setMinimumHeight(34)
        self.name_in= QLineEdit(); self.name_in.setMinimumHeight(34)
        self.unit_cb= QComboBox(); self.unit_cb.addItems(["months","days"]); self.unit_cb.setMinimumHeight(34)
        self.dur_in = QLineEdit(); self.dur_in.setMinimumHeight(34)
        self.price_in=QLineEdit(); self.price_in.setMinimumHeight(34)
        self.desc_in= QLineEdit(); self.desc_in.setMinimumHeight(34)
        form.addRow("Package ID",    self.id_in); form.addRow("Name",          self.name_in)
        form.addRow("Duration Unit", self.unit_cb); form.addRow("Duration Value",self.dur_in)
        form.addRow("Price (VND)",   self.price_in); form.addRow("Description",  self.desc_in)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
        if p:
            self.id_in.setText(p.package_id); self.name_in.setText(p.name)
            self.unit_cb.setCurrentText(p.duration_unit); self.dur_in.setText(str(p.duration_value))
            self.price_in.setText(str(p.price)); self.desc_in.setText(p.description)

    def result(self) -> Package:
        return Package(self.id_in.text().strip(), self.name_in.text().strip(),
                       self.unit_cb.currentText(), self.dur_in.text().strip(),
                       self.price_in.text().strip(), self.desc_in.text().strip())
