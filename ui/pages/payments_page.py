"""ui/pages/payments_page.py — Payments CRUD + CSV export."""
from __future__ import annotations
import csv, io
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit, QPushButton, QLabel, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QFileDialog)
from libs.DataConnector import DataConnector
from model.Payment import Payment


class PaymentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector(); self._data: list[Payment] = []; self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        tb = QHBoxLayout()
        self.search_in = QLineEdit(); self.search_in.setPlaceholderText("🔍  Search member ID…"); self.search_in.setMinimumHeight(36)
        self.search_in.textChanged.connect(self._filter)
        export_btn = QPushButton("⬇  Export CSV"); export_btn.setObjectName("secondaryBtn"); export_btn.setMinimumHeight(36); export_btn.clicked.connect(self._export)
        add_btn = QPushButton("＋  Add Payment"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addWidget(self.search_in); tb.addStretch(); tb.addWidget(export_btn); tb.addWidget(add_btn)
        lay.addLayout(tb)
        self.table = QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Payment ID","Member ID","Amount","Method","Date","Note","Sub ID"])
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
        self._data = self._dc.get_all_payments(); self._populate(self._data)

    def _populate(self, data):
        self.table.setRowCount(0)
        total = 0
        for p in data:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([p.payment_id, p.member_id, f"{float(p.amount):,.0f}", p.method, p.date, p.note, p.related_subscription_id]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
            total += float(p.amount)
        self.lbl.setText(f"{len(data)} payment(s)  |  Total: {total:,.0f} VND")

    def _filter(self):
        s = self.search_in.text().strip()
        self._populate([p for p in self._data if not s or s.lower() in p.member_id.lower()])

    def _sel(self): return self.table.currentRow() if self.table.selectedItems() else None

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Payments CSV", "payments.csv", "CSV (*.csv)")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Payment ID","Member ID","Amount","Method","Date","Note","Sub ID"])
            for p in self._data:
                w.writerow([p.payment_id, p.member_id, p.amount, p.method, p.date, p.note, p.related_subscription_id])
        QMessageBox.information(self, "Exported", f"Saved to:\n{path}")

    def _add(self):
        dlg = _PayDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_payments(self._data); self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a payment."); return
        dlg = _PayDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result(); self._dc.save_payments(self._data); self.refresh()

    def _delete(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a payment."); return
        if QMessageBox.question(self, "Delete", "Delete this payment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx); self._dc.save_payments(self._data); self.refresh()


class _PayDialog(QDialog):
    def __init__(self, parent=None, p: Payment = None):
        super().__init__(parent); self.setWindowTitle("Edit Payment" if p else "Add Payment"); self.setMinimumWidth(380)
        lay = QVBoxLayout(self); form = QFormLayout(); lay.addLayout(form)
        self.id_in  = QLineEdit(); self.id_in.setMinimumHeight(34)
        self.mem_in = QLineEdit(); self.mem_in.setMinimumHeight(34)
        self.amt_in = QLineEdit(); self.amt_in.setMinimumHeight(34)
        self.meth_cb= QComboBox(); self.meth_cb.addItems(["cash","bank","card"]); self.meth_cb.setMinimumHeight(34)
        self.date_in= QLineEdit(); self.date_in.setPlaceholderText("YYYY-MM-DD"); self.date_in.setMinimumHeight(34)
        self.note_in= QLineEdit(); self.note_in.setMinimumHeight(34)
        self.sub_in = QLineEdit(); self.sub_in.setMinimumHeight(34)
        form.addRow("Payment ID", self.id_in); form.addRow("Member ID", self.mem_in)
        form.addRow("Amount",     self.amt_in); form.addRow("Method",    self.meth_cb)
        form.addRow("Date",       self.date_in); form.addRow("Note",     self.note_in)
        form.addRow("Sub ID",     self.sub_in)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
        if p:
            self.id_in.setText(p.payment_id); self.mem_in.setText(p.member_id)
            self.amt_in.setText(str(p.amount)); self.meth_cb.setCurrentText(p.method)
            self.date_in.setText(p.date); self.note_in.setText(p.note); self.sub_in.setText(p.related_subscription_id)

    def result(self) -> Payment:
        return Payment(self.id_in.text().strip(), self.mem_in.text().strip(),
                       self.amt_in.text().strip(), self.meth_cb.currentText(),
                       self.date_in.text().strip(), self.note_in.text().strip(), self.sub_in.text().strip())
