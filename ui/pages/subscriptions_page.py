"""ui/pages/subscriptions_page.py — Subscriptions CRUD + auto-expire."""
from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QMessageBox)
from libs.DataConnector import DataConnector
from model.Subscription import Subscription


class SubscriptionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector(); self._data: list[Subscription] = []; self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        tb = QHBoxLayout()
        expire_btn = QPushButton("⟳  Run Auto-Expire"); expire_btn.setObjectName("secondaryBtn"); expire_btn.setMinimumHeight(36); expire_btn.clicked.connect(self._auto_expire)
        add_btn = QPushButton("＋  Add Subscription"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addWidget(expire_btn); tb.addStretch(); tb.addWidget(add_btn); lay.addLayout(tb)
        self.table = QTableWidget(); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Sub ID","Member ID","Package ID","Start Date","End Date","Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        bot = QHBoxLayout(); self.lbl = QLabel("")
        edit_btn = QPushButton("✏  Edit"); edit_btn.setMinimumHeight(34); edit_btn.clicked.connect(self._edit)
        cancel_btn = QPushButton("✕  Cancel Sub"); cancel_btn.setObjectName("dangerBtn"); cancel_btn.setMinimumHeight(34); cancel_btn.clicked.connect(self._cancel)
        bot.addWidget(self.lbl); bot.addStretch(); bot.addWidget(edit_btn); bot.addWidget(cancel_btn)
        lay.addLayout(bot)

    def refresh(self):
        self._data = self._dc.get_all_subscriptions(); self._populate()

    def _populate(self):
        self.table.setRowCount(0)
        for s in self._data:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([s.sub_id, s.member_id, s.package_id, s.start_date, s.end_date, s.status]):
                item = QTableWidgetItem(str(v))
                if v == "expired":   item.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor("#F87171"))
                elif v == "active":  item.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor("#34D399"))
                self.table.setItem(r, c, item)
        self.lbl.setText(f"{len(self._data)} subscription(s)")

    def _sel(self): return self.table.currentRow() if self.table.selectedItems() else None

    def _auto_expire(self):
        n = self._dc.auto_expire_subscriptions()
        QMessageBox.information(self, "Auto-Expire", f"{n} subscription(s) marked as expired.")
        self.refresh()

    def _add(self):
        dlg = _SubDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_subscriptions(self._data); self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a subscription."); return
        dlg = _SubDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result(); self._dc.save_subscriptions(self._data); self.refresh()

    def _cancel(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a subscription."); return
        self._data[idx].status = "cancelled"
        self._dc.save_subscriptions(self._data); self.refresh()


class _SubDialog(QDialog):
    def __init__(self, parent=None, s: Subscription = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Subscription" if s else "Add Subscription")
        self.setMinimumWidth(420)

        # Load live data
        dc = DataConnector()
        self._packages = dc.get_all_packages()
        self._members  = dc.get_all_members()

        lay = QVBoxLayout(self); form = QFormLayout(); form.setSpacing(10); lay.addLayout(form)

        # Sub ID
        self.id_in = QLineEdit(); self.id_in.setMinimumHeight(36)
        form.addRow("Sub ID", self.id_in)

        # Member — dropdown: "M001 — Nguyen Van An"
        self.mem_cb = QComboBox(); self.mem_cb.setMinimumHeight(36)
        for m in self._members:
            self.mem_cb.addItem(f"{m.member_id} — {m.full_name}", userData=m.member_id)
        form.addRow("Member", self.mem_cb)

        # Package — dropdown: "P001 — Monthly Basic (1 months · 299,000 VND)"
        self.pkg_cb = QComboBox(); self.pkg_cb.setMinimumHeight(36)
        for p in self._packages:
            label = f"{p.package_id} — {p.name}  ({p.duration_value} {p.duration_unit} · {float(p.price):,.0f} VND)"
            self.pkg_cb.addItem(label, userData=p.package_id)
        self.pkg_cb.currentIndexChanged.connect(self._auto_end_date)
        form.addRow("Package", self.pkg_cb)

        # Start Date
        self.start_in = QLineEdit(); self.start_in.setPlaceholderText("YYYY-MM-DD"); self.start_in.setMinimumHeight(36)
        self.start_in.textChanged.connect(self._auto_end_date)
        form.addRow("Start Date", self.start_in)

        # End Date (auto-calculated, still editable)
        self.end_in = QLineEdit(); self.end_in.setPlaceholderText("YYYY-MM-DD (auto)"); self.end_in.setMinimumHeight(36)
        form.addRow("End Date", self.end_in)

        # Status
        self.status_cb = QComboBox(); self.status_cb.setMinimumHeight(36)
        self.status_cb.addItems(["active", "expired", "cancelled"])
        form.addRow("Status", self.status_cb)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)

        # Pre-fill when editing
        if s:
            self.id_in.setText(s.sub_id)
            # Select matching member
            for i in range(self.mem_cb.count()):
                if self.mem_cb.itemData(i) == s.member_id:
                    self.mem_cb.setCurrentIndex(i); break
            # Select matching package
            for i in range(self.pkg_cb.count()):
                if self.pkg_cb.itemData(i) == s.package_id:
                    self.pkg_cb.setCurrentIndex(i); break
            self.start_in.setText(s.start_date)
            self.end_in.setText(s.end_date)
            self.status_cb.setCurrentText(s.status)

    def _auto_end_date(self):
        """Auto-calculate end date from start date + package duration."""
        from datetime import date
        from dateutil.relativedelta import relativedelta
        try:
            start = date.fromisoformat(self.start_in.text().strip())
            pkg_id = self.pkg_cb.currentData()
            pkg = next((p for p in self._packages if p.package_id == pkg_id), None)
            if pkg:
                unit = pkg.duration_unit   # "months" | "days"
                val  = int(pkg.duration_value)
                if unit == "months":
                    end = start + relativedelta(months=val)
                else:
                    from datetime import timedelta
                    end = start + timedelta(days=val)
                self.end_in.setText(end.isoformat())
        except (ValueError, TypeError):
            pass   # invalid date — leave end_in as-is

    def result(self) -> Subscription:
        return Subscription(
            self.id_in.text().strip(),
            self.mem_cb.currentData(),     # member_id from dropdown
            self.pkg_cb.currentData(),     # package_id from dropdown
            self.start_in.text().strip(),
            self.end_in.text().strip(),
            self.status_cb.currentText(),
        )
