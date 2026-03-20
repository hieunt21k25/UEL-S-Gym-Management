"""ui/pages/checkins_page.py — Check-in by member ID + history + stats."""
from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit, QPushButton, QLabel, QMessageBox, QFrame)
from libs.DataConnector import DataConnector


class CheckInsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector(); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(12)

        # Stats cards row
        self.stats_row = QHBoxLayout(); lay.addLayout(self.stats_row)
        self._today_lbl  = self._stat_card("Today",   "0")
        self._weekly_lbl = self._stat_card("This Week","0")
        self._month_lbl  = self._stat_card("This Month","0")
        self._total_lbl  = self._stat_card("All Time", "0")

        # Check-in toolbar
        tb = QHBoxLayout()
        self.member_in = QLineEdit(); self.member_in.setPlaceholderText("Member ID (e.g. M001)"); self.member_in.setMinimumHeight(36)
        self.member_in.returnPressed.connect(self._do_checkin)
        ci_btn   = QPushButton("✅  Check In");       ci_btn.setObjectName("primaryBtn");   ci_btn.setMinimumHeight(36); ci_btn.clicked.connect(self._do_checkin)
        face_btn = QPushButton("📷  Face Check-in"); face_btn.setObjectName("secondaryBtn"); face_btn.setMinimumHeight(36); face_btn.clicked.connect(self._do_face_checkin)
        tb.addWidget(QLabel("Member ID:")); tb.addWidget(self.member_in); tb.addWidget(ci_btn); tb.addWidget(face_btn); tb.addStretch()
        lay.addLayout(tb)

        # History table
        lay.addWidget(QLabel("Check-in History:"))
        self.table = QTableWidget(); self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Check-in ID","Member ID","Timestamp"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        self.lbl = QLabel(""); lay.addWidget(self.lbl)

    def _stat_card(self, title: str, value: str) -> QLabel:
        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 12)
        t = QLabel(title); t.setObjectName("metricLabel")
        v = QLabel(value); v.setObjectName("metricValue")
        cl.addWidget(t); cl.addWidget(v)
        self.stats_row.addWidget(card)
        return v

    def refresh(self):
        cis = self._dc.get_all_checkins()
        self.table.setRowCount(0)
        for ci in reversed(cis):
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([ci.checkin_id, ci.member_id, ci.timestamp]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.lbl.setText(f"{len(cis)} total check-in(s)")
        stats = self._dc.get_checkin_stats()
        self._today_lbl.setText(str(stats["today"]))
        self._weekly_lbl.setText(str(stats["weekly"]))
        self._month_lbl.setText(str(stats["monthly"]))
        self._total_lbl.setText(str(stats["total"]))

    def _do_checkin(self):
        mid = self.member_in.text().strip()
        if not mid: QMessageBox.warning(self, "Input", "Please enter a Member ID."); return
        ok, msg = self._dc.checkin_member(mid)
        if ok:
            QMessageBox.information(self, "Check-in", msg)
            self.member_in.clear(); self.refresh()
        else:
            QMessageBox.warning(self, "Check-in Failed", msg)

    def _do_face_checkin(self):
        from ui.dialogs.face_checkin_dialog import FaceCheckinDialog
        dlg = FaceCheckinDialog(self)
        dlg.exec()
        self.refresh()   # always refresh — check-in may have occurred
