"""ui/pages/checkins_page.py — Check-in with remaining days display + low-days alert."""
from __future__ import annotations
from datetime import date

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit, QPushButton, QLabel, QMessageBox, QFrame,
)
from libs.DataConnector import DataConnector


def _days_remaining(end_date_str: str) -> int:
    try:
        return (date.fromisoformat(end_date_str) - date.today()).days
    except Exception:
        return -1


class CheckInsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # ── Stats cards ───────────────────────────────────────────────────────
        self.stats_row = QHBoxLayout()
        lay.addLayout(self.stats_row)
        self._today_lbl  = self._stat_card("Today",      "0")
        self._weekly_lbl = self._stat_card("This Week",  "0")
        self._month_lbl  = self._stat_card("This Month", "0")
        self._total_lbl  = self._stat_card("All Time",   "0")

        # ── Check-in toolbar ──────────────────────────────────────────────────
        tb = QHBoxLayout()
        self.member_in = QLineEdit()
        self.member_in.setPlaceholderText("Member ID (e.g. M001)")
        self.member_in.setMinimumHeight(36)
        self.member_in.returnPressed.connect(self._do_checkin)
        ci_btn   = QPushButton("✅  Check In");       ci_btn.setObjectName("primaryBtn");   ci_btn.setMinimumHeight(36); ci_btn.clicked.connect(self._do_checkin)
        face_btn = QPushButton("📷  Face Check-in"); face_btn.setObjectName("secondaryBtn"); face_btn.setMinimumHeight(36); face_btn.clicked.connect(self._do_face_checkin)
        tb.addWidget(QLabel("Member ID:"))
        tb.addWidget(self.member_in)
        tb.addWidget(ci_btn)
        tb.addWidget(face_btn)
        tb.addStretch()
        lay.addLayout(tb)

        # ── Subscription alert banner (hidden by default) ─────────────────────
        self._alert_frame = QFrame()
        self._alert_frame.setObjectName("bottomCard")
        self._alert_frame.setVisible(False)
        alert_lay = QVBoxLayout(self._alert_frame)
        alert_lay.setContentsMargins(18, 10, 18, 10)
        alert_lay.setSpacing(4)
        self._alert_title = QLabel("")
        self._alert_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._alert_detail = QLabel("")
        self._alert_detail.setStyleSheet("font-size:12px;")
        alert_lay.addWidget(self._alert_title)
        alert_lay.addWidget(self._alert_detail)
        lay.addWidget(self._alert_frame)

        # ── History table (with "Days Left" column) ───────────────────────────
        lay.addWidget(QLabel("Check-in History:"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Check-in ID", "Member ID", "Timestamp", "Days Left"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)

        self.lbl = QLabel("")
        lay.addWidget(self.lbl)

    def _stat_card(self, title: str, value: str) -> QLabel:
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        t = QLabel(title); t.setObjectName("metricLabel")
        v = QLabel(value); v.setObjectName("metricValue")
        cl.addWidget(t); cl.addWidget(v)
        self.stats_row.addWidget(card)
        return v

    def refresh(self):
        cis = self._dc.get_all_checkins()

        # Build member → active sub map
        subs = self._dc.get_all_subscriptions()
        sub_map: dict[str, object] = {}
        for s in subs:
            if s.status == "active":
                sub_map[s.member_id] = s

        self.table.setRowCount(0)
        for ci in reversed(cis):
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, v in enumerate([ci.checkin_id, ci.member_id, ci.timestamp]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))

            # Days Left column
            sub = sub_map.get(ci.member_id)
            if sub:
                days = _days_remaining(sub.end_date)
                days_item = QTableWidgetItem(f"{days}d" if days >= 0 else "Expired")
                days_item.setForeground(QColor(
                    "#34D399" if days > 30 else "#FBBF24" if days >= 0 else "#F87171"
                ))
            else:
                days_item = QTableWidgetItem("—")
                days_item.setForeground(QColor("#94A3B8"))
            self.table.setItem(r, 3, days_item)

        self.lbl.setText(f"{len(cis)} total check-in(s)")
        stats = self._dc.get_checkin_stats()
        self._today_lbl.setText(str(stats["today"]))
        self._weekly_lbl.setText(str(stats["weekly"]))
        self._month_lbl.setText(str(stats["monthly"]))
        self._total_lbl.setText(str(stats["total"]))

    def _do_checkin(self):
        mid = self.member_in.text().strip()
        if not mid:
            QMessageBox.warning(self, "Input", "Please enter a Member ID.")
            return
        ok, msg = self._dc.checkin_member(mid)
        if ok:
            self._show_checkin_banner(mid)
            self.member_in.clear()
            self.refresh()
        else:
            QMessageBox.warning(self, "Check-in Failed", msg)

    def _show_checkin_banner(self, member_id: str):
        """Display remaining subscription days after a successful check-in; warn if < 30."""
        subs    = self._dc.get_all_subscriptions()
        members = {m.member_id: m for m in self._dc.get_all_members()}
        packages = {p.package_id: p for p in self._dc.get_all_packages()}

        active_subs = [s for s in subs if s.member_id == member_id and s.status == "active"]
        m   = members.get(member_id)
        name = m.full_name if m else member_id

        if not active_subs:
            self._alert_frame.setVisible(False)
            return

        sub  = active_subs[0]
        pkg  = packages.get(sub.package_id)
        days = _days_remaining(sub.end_date)

        if days <= 0:
            color  = "#F87171"
            icon   = "🔴"
            title  = f"{icon}  {name}'s subscription has EXPIRED!"
        elif days <= 30:
            color  = "#FBBF24"
            icon   = "⚠️"
            title  = f"{icon}  LOW SUBSCRIPTION ALERT — {name} has only {days} day(s) left!"
        else:
            color  = "#34D399"
            icon   = "✅"
            title  = f"{icon}  Checked in: {name}"

        pkg_name = pkg.name if pkg else sub.package_id
        detail   = f"Package: {pkg_name}   |   Expires: {sub.end_date}   |   Remaining: {days} day(s)"

        self._alert_title.setText(title)
        self._alert_title.setStyleSheet(f"color:{color}; font-size:13px; font-weight:700;")
        self._alert_detail.setText(detail)
        self._alert_detail.setStyleSheet(f"color:#94A3B8; font-size:11px;")
        self._alert_frame.setVisible(True)

    def _do_face_checkin(self):
        from ui.dialogs.face_checkin_dialog import FaceCheckinDialog
        dlg = FaceCheckinDialog(self)
        dlg.exec()
        self.refresh()
