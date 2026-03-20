"""ui/pages/reports_page.py — Reports with CSV export for payments and check-ins."""
from __future__ import annotations
import csv
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QFileDialog, QMessageBox)
from libs.DataConnector import DataConnector


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._dc = DataConnector(); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(16)

        # Export buttons
        tb = QHBoxLayout()
        exp_pay = QPushButton("⬇  Export Payments CSV"); exp_pay.setObjectName("secondaryBtn")
        exp_pay.setMinimumHeight(36); exp_pay.clicked.connect(self._export_payments)
        exp_ci  = QPushButton("⬇  Export Check-ins CSV"); exp_ci.setObjectName("secondaryBtn")
        exp_ci.setMinimumHeight(36); exp_ci.clicked.connect(self._export_checkins)
        tb.addWidget(exp_pay); tb.addWidget(exp_ci); tb.addStretch()
        lay.addLayout(tb)

        # Monthly revenue
        lay.addWidget(QLabel("Monthly Revenue"))
        self.rev_table = QTableWidget(); self.rev_table.setColumnCount(2)
        self.rev_table.setHorizontalHeaderLabels(["Month","Revenue (VND)"])
        self.rev_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rev_table.setAlternatingRowColors(True)
        self.rev_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.rev_table)

        # Summary stats
        self.summary_lbl = QLabel(""); lay.addWidget(self.summary_lbl)

    def refresh(self):
        rev = self._dc.monthly_revenue()
        self.rev_table.setRowCount(0)
        total = 0
        for item in reversed(rev):
            r = self.rev_table.rowCount(); self.rev_table.insertRow(r)
            self.rev_table.setItem(r, 0, QTableWidgetItem(item["month"]))
            self.rev_table.setItem(r, 1, QTableWidgetItem(f"{item['revenue']:,.0f}"))
            total += item["revenue"]
        stats = self._dc.get_dashboard_stats()
        self.summary_lbl.setText(
            f"Total Revenue: {total:,.0f} VND  |  "
            f"Active Members: {stats['active_members']}  |  "
            f"Active Subscriptions: {stats['active_subscriptions']}"
        )

    def _export_payments(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Payments", "payments.csv", "CSV (*.csv)")
        if not path: return
        pays = self._dc.get_all_payments()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["payment_id","member_id","amount","method","date","note","related_subscription_id"])
            for p in pays:
                w.writerow([p.payment_id, p.member_id, p.amount, p.method, p.date, p.note, p.related_subscription_id])
        QMessageBox.information(self, "Exported", f"Payments exported to:\n{path}")

    def _export_checkins(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Check-ins", "checkins.csv", "CSV (*.csv)")
        if not path: return
        cis = self._dc.get_all_checkins()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["checkin_id","member_id","timestamp"])
            for ci in cis:
                w.writerow([ci.checkin_id, ci.member_id, ci.timestamp])
        QMessageBox.information(self, "Exported", f"Check-ins exported to:\n{path}")
