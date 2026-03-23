"""ui/pages/subscriptions_page.py — Subscriptions CRUD + member info panel on ID click."""
from __future__ import annotations
from datetime import date

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QMessageBox, QFrame,
)
from libs.DataConnector import DataConnector
from model.Subscription import Subscription


def _days_remaining(end_date_str: str) -> int:
    try:
        return (date.fromisoformat(end_date_str) - date.today()).days
    except Exception:
        return -1


class SubscriptionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector()
        self._data: list[Subscription] = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # Toolbar
        tb = QHBoxLayout()
        expire_btn = QPushButton("⟳  Run Auto-Expire")
        expire_btn.setObjectName("secondaryBtn")
        expire_btn.setMinimumHeight(36)
        expire_btn.clicked.connect(self._auto_expire)
        add_btn = QPushButton("＋  Add Subscription")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._add)
        tb.addWidget(expire_btn)
        tb.addStretch()
        tb.addWidget(add_btn)
        lay.addLayout(tb)

        # Table — added "Days Left" column
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Sub ID", "Member ID", "Package ID", "Start Date", "End Date", "Status", "Days Left"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self._on_cell_click)
        lay.addWidget(self.table)

        # Bottom buttons
        bot = QHBoxLayout()
        self.lbl = QLabel("")
        edit_btn   = QPushButton("✏  Edit");        edit_btn.setMinimumHeight(34);   edit_btn.clicked.connect(self._edit)
        cancel_btn = QPushButton("✕  Cancel Sub");  cancel_btn.setObjectName("dangerBtn"); cancel_btn.setMinimumHeight(34); cancel_btn.clicked.connect(self._cancel)
        bot.addWidget(self.lbl)
        bot.addStretch()
        bot.addWidget(edit_btn)
        bot.addWidget(cancel_btn)
        lay.addLayout(bot)

        # ── Member Detail Panel ───────────────────────────────────────────────
        self._detail_frame = QFrame()
        self._detail_frame.setObjectName("bottomCard")
        self._detail_frame.setVisible(False)
        detail_lay = QVBoxLayout(self._detail_frame)
        detail_lay.setContentsMargins(20, 14, 20, 14)
        detail_lay.setSpacing(6)

        detail_title = QLabel("👤  Member Details")
        detail_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        detail_title.setStyleSheet("color: #B0EFCD;")
        detail_lay.addWidget(detail_title)

        self._detail_row = QHBoxLayout()
        self._detail_row.setSpacing(32)
        detail_lay.addLayout(self._detail_row)
        lay.addWidget(self._detail_frame)

    # ── Data ─────────────────────────────────────────────────────────────────

    def refresh(self):
        self._data = self._dc.get_all_subscriptions()
        self._populate()
        self._detail_frame.setVisible(False)

    def _populate(self):
        self.table.setRowCount(0)
        for s in self._data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, v in enumerate([s.sub_id, s.member_id, s.package_id, s.start_date, s.end_date, s.status]):
                item = QTableWidgetItem(str(v))
                if v == "expired":
                    item.setForeground(QColor("#F87171"))
                elif v == "active":
                    item.setForeground(QColor("#34D399"))
                self.table.setItem(r, c, item)

            # Days Left
            if s.status == "active":
                days = _days_remaining(s.end_date)
                days_item = QTableWidgetItem(f"{days}d" if days >= 0 else "Expired")
                days_item.setForeground(QColor("#34D399" if days > 30 else "#FBBF24" if days >= 0 else "#F87171"))
            else:
                days_item = QTableWidgetItem("—")
                days_item.setForeground(QColor("#94A3B8"))
            self.table.setItem(r, 6, days_item)

        self.lbl.setText(f"{len(self._data)} subscription(s)")

    def _sel(self):
        return self.table.currentRow() if self.table.selectedItems() else None

    # ── Click on ID column → show member info ─────────────────────────────────

    def _on_cell_click(self, row: int, col: int):
        # Trigger on Member ID column (col 1) or Sub ID col (col 0)
        mid_item = self.table.item(row, 1)
        if not mid_item:
            return
        self._show_member_detail(mid_item.text())

    def _show_member_detail(self, member_id: str):
        # Clear
        while self._detail_row.count():
            item = self._detail_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        members = {m.member_id: m for m in self._dc.get_all_members()}
        packages = {p.package_id: p for p in self._dc.get_all_packages()}
        m = members.get(member_id)

        if not m:
            lbl = QLabel(f"  Member '{member_id}' not found.")
            lbl.setStyleSheet("color:#94A3B8;")
            self._detail_row.addWidget(lbl)
        else:
            # Find their active sub for package + days info
            subs = [s for s in self._data if s.member_id == member_id and s.status == "active"]
            sub = subs[0] if subs else None
            pkg = packages.get(sub.package_id) if sub else None
            days = _days_remaining(sub.end_date) if sub else None

            fields = [
                ("Full Name",  m.full_name,               "#F8FAFC"),
                ("Phone",      m.phone,                   "#94A3B8"),
                ("Email",      m.email,                   "#94A3B8"),
                ("Gender",     m.gender,                  "#94A3B8"),
                ("Join Date",  m.join_date,               "#94A3B8"),
                ("Status",     m.status.upper(),          "#34D399" if m.status == "active" else "#F87171"),
            ]
            if sub:
                days_label = f"{days} days" if days and days >= 0 else "EXPIRED"
                days_color = "#34D399" if days and days > 30 else "#FBBF24" if days and days >= 0 else "#F87171"
                fields += [
                    ("Package",        pkg.name if pkg else sub.package_id, "#B0EFCD"),
                    ("Days Remaining", days_label,                          days_color),
                ]

            for label, value, color in fields:
                col_w = QWidget()
                col_l = QVBoxLayout(col_w)
                col_l.setContentsMargins(0, 0, 0, 0)
                col_l.setSpacing(2)
                lbl_key = QLabel(label)
                lbl_key.setStyleSheet("color:#64748B; font-size:10px; font-weight:700;")
                lbl_val = QLabel(str(value))
                lbl_val.setStyleSheet(f"color:{color}; font-size:12px; font-weight:600;")
                col_l.addWidget(lbl_key)
                col_l.addWidget(lbl_val)
                self._detail_row.addWidget(col_w)

        self._detail_row.addStretch()
        self._detail_frame.setVisible(True)

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def _auto_expire(self):
        n = self._dc.auto_expire_subscriptions()
        QMessageBox.information(self, "Auto-Expire", f"{n} subscription(s) marked as expired.")
        self.refresh()

    def _add(self):
        dlg = _SubDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result())
            self._dc.save_subscriptions(self._data)
            self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a subscription.")
            return
        dlg = _SubDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result()
            self._dc.save_subscriptions(self._data)
            self.refresh()

    def _cancel(self):
        idx = self._sel()
        if idx is None:
            QMessageBox.information(self, "Select", "Please select a subscription.")
            return
        self._data[idx].status = "cancelled"
        self._dc.save_subscriptions(self._data)
        self.refresh()


class _SubDialog(QDialog):
    def __init__(self, parent=None, s: Subscription = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Subscription" if s else "Add Subscription")
        self.setMinimumWidth(420)

        dc = DataConnector()
        self._packages = dc.get_all_packages()
        self._members  = dc.get_all_members()

        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        lay.addLayout(form)

        self.id_in = QLineEdit(); self.id_in.setMinimumHeight(36)
        form.addRow("Sub ID", self.id_in)

        self.mem_cb = QComboBox(); self.mem_cb.setMinimumHeight(36)
        for m in self._members:
            self.mem_cb.addItem(f"{m.member_id} — {m.full_name}", userData=m.member_id)
        form.addRow("Member", self.mem_cb)

        self.pkg_cb = QComboBox(); self.pkg_cb.setMinimumHeight(36)
        for p in self._packages:
            label = f"{p.package_id} — {p.name}  ({p.duration_value} {p.duration_unit} · {float(p.price):,.0f} VND)"
            self.pkg_cb.addItem(label, userData=p.package_id)
        self.pkg_cb.currentIndexChanged.connect(self._auto_end_date)
        form.addRow("Package", self.pkg_cb)

        self.start_in = QLineEdit(); self.start_in.setPlaceholderText("YYYY-MM-DD"); self.start_in.setMinimumHeight(36)
        self.start_in.textChanged.connect(self._auto_end_date)
        form.addRow("Start Date", self.start_in)

        self.end_in = QLineEdit(); self.end_in.setPlaceholderText("YYYY-MM-DD (auto)"); self.end_in.setMinimumHeight(36)
        form.addRow("End Date", self.end_in)

        self.status_cb = QComboBox(); self.status_cb.setMinimumHeight(36)
        self.status_cb.addItems(["active", "expired", "cancelled"])
        form.addRow("Status", self.status_cb)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        if s:
            self.id_in.setText(s.sub_id)
            for i in range(self.mem_cb.count()):
                if self.mem_cb.itemData(i) == s.member_id:
                    self.mem_cb.setCurrentIndex(i); break
            for i in range(self.pkg_cb.count()):
                if self.pkg_cb.itemData(i) == s.package_id:
                    self.pkg_cb.setCurrentIndex(i); break
            self.start_in.setText(s.start_date)
            self.end_in.setText(s.end_date)
            self.status_cb.setCurrentText(s.status)

    def _auto_end_date(self):
        from datetime import date
        from dateutil.relativedelta import relativedelta
        try:
            start = date.fromisoformat(self.start_in.text().strip())
            pkg_id = self.pkg_cb.currentData()
            pkg = next((p for p in self._packages if p.package_id == pkg_id), None)
            if pkg:
                val = int(pkg.duration_value)
                end = start + relativedelta(months=val) if pkg.duration_unit == "months" else start + __import__('datetime').timedelta(days=val)
                self.end_in.setText(end.isoformat())
        except (ValueError, TypeError):
            pass

    def result(self) -> Subscription:
        return Subscription(
            self.id_in.text().strip(),
            self.mem_cb.currentData(),
            self.pkg_cb.currentData(),
            self.start_in.text().strip(),
            self.end_in.text().strip(),
            self.status_cb.currentText(),
        )
