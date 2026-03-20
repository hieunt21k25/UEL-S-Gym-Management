"""Dashboard page — metric cards + revenue chart + top members (JSON-based)."""
from __future__ import annotations
from collections import Counter

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.pages.base_page import BasePage
from libs.DataConnector import DataConnector


class _DashWorker(QThread):
    done  = pyqtSignal(dict, list, list)
    error = pyqtSignal(str)

    def run(self):
        try:
            dc    = DataConnector()
            stats = dc.get_dashboard_stats()
            rev   = stats.pop("monthly_revenue", [])

            # Top members by check-ins this month
            from datetime import date
            mo = date.today().strftime("%Y-%m")
            cis = dc.get_all_checkins()
            members = {m.member_id: m.full_name for m in dc.get_all_members()}
            monthly = [c for c in cis if c.timestamp[:7] == mo]
            counts  = Counter(c.member_id for c in monthly)
            top = [
                {"member_id": mid, "full_name": members.get(mid, mid), "count": cnt}
                for mid, cnt in counts.most_common(8)
            ]
            self.done.emit(stats, rev, top)
        except Exception as e:
            self.error.emit(str(e))


class DashboardPage(BasePage):
    PAGE_TITLE = "Dashboard"

    def build(self):
        # ── Metric row ────────────────────────────────────────────────────────
        self._metrics_row = QHBoxLayout()
        self._metrics_row.setSpacing(16)
        self.layout_.addLayout(self._metrics_row)

        self._metric_widgets = []
        for icon, label, color in [
            ("👥", "Total Members",           "#111827"),
            ("✨", "New Members Today",       "#111827"),
            ("📅", "New Members This Month",  "#111827"),
            ("💰", "Monthly Revenue",         "#111827"),
            ("⏰", "Expired Memberships",     "#111827"),
        ]:
            card, val_lbl = self._make_metric_card(icon, label, "—", color)
            self._metrics_row.addWidget(card)
            self._metric_widgets.append(val_lbl)

        # ── Bottom row: chart + top members ───────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        # Chart card
        self._chart_frame = QFrame()
        self._chart_frame.setObjectName("bottomCard")
        self._chart_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart_layout = QVBoxLayout(self._chart_frame)
        self._chart_layout.setContentsMargins(20, 16, 20, 16)
        chart_title = QLabel("📈  Monthly Revenue (VND)")
        chart_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        chart_title.setStyleSheet("color: #F8FAFC;")  # White header for dark card
        self._chart_layout.addWidget(chart_title)

        # Top members card
        self._top_frame = QFrame()
        self._top_frame.setObjectName("bottomCard")
        self._top_frame.setFixedWidth(280)
        top_layout = QVBoxLayout(self._top_frame)
        top_layout.setContentsMargins(20, 16, 20, 16)
        top_title = QLabel("🏆  Top Members")
        top_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        top_title.setStyleSheet("color: #F8FAFC;")  # White header for dark card
        top_layout.addWidget(top_title)
        self._top_list_layout = QVBoxLayout()
        self._top_list_layout.setSpacing(8)
        top_layout.addLayout(self._top_list_layout)
        top_layout.addStretch()

        bottom.addWidget(self._chart_frame, 3)
        bottom.addWidget(self._top_frame, 1)
        self.layout_.addLayout(bottom)

        self._status = QLabel("")
        self._status.setObjectName("subtitleLabel")
        self.layout_.addWidget(self._status)

    def refresh(self):
        self._status.setText("Loading…")
        self._worker = _DashWorker()
        self._worker.done.connect(self._populate)
        self._worker.error.connect(lambda e: self._status.setText(f"Error: {e}"))
        self._worker.start()

    def _populate(self, stats: dict, rev: list, top: list):
        self._status.setText("")

        # Update metric cards
        vals = [
            str(stats.get("total_members",         "0")),
            str(stats.get("new_members_today",     "0")),
            str(stats.get("new_members_month",     "0")),
            str(stats.get("total_revenue",         "0")),
            str(stats.get("expired_subscriptions", "0")),
        ]
        for lbl, val in zip(self._metric_widgets, vals):
            lbl.setText(val)

        # Revenue bar chart (matplotlib)
        while self._chart_layout.count() > 1:
            item = self._chart_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
            from matplotlib.figure import Figure

            months   = [r["month"] for r in rev]
            revenues = [r["revenue"] for r in rev]

            fig = Figure(facecolor="none", tight_layout=True)
            ax  = fig.add_subplot(111, facecolor="none")
            
            # Smooth area line chart
            ax.plot(range(len(months)), revenues, color="#AEE8CB", marker='o', linestyle='-', linewidth=4, markersize=9, zorder=3)
            ax.fill_between(range(len(months)), revenues, color="#AEE8CB", alpha=0.15, zorder=2)
            
            peak = max(revenues) if revenues else 1
            margin = peak * 0.20 if peak > 0 else 1
            ax.set_ylim(0, peak + margin)
            
            for x, val in enumerate(revenues):
                if val > 0:
                    ax.text(x, val + (peak * 0.05),
                            f"{val:,.0f}", ha="center", va="bottom",
                            color="#F8FAFC", fontsize=8, fontweight='bold', zorder=4)
                            
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=0, ha="center")
            ax.tick_params(colors="#e2e8f0", labelsize=8, pad=6)
            ax.spines[:].set_color("none")
            ax.yaxis.grid(True, color="#F8FAFC", alpha=0.1, linewidth=1, linestyle='--')
            
            canvas = Canvas(fig)
            canvas.setStyleSheet("background: transparent;")
            canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            canvas.updateGeometry()
            self._chart_layout.addWidget(canvas)
            self._chart_layout.setStretch(1, 1)
        except Exception as ex:
            self._chart_layout.addWidget(QLabel(f"Chart unavailable: {ex}"))

        # Top members list
        while self._top_list_layout.count():
            item = self._top_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not top:
            no_data = QLabel("No check-ins this month yet.")
            no_data.setStyleSheet("color:#94A3B8; font-size:11px;")
            self._top_list_layout.addWidget(no_data)
        else:
            for i, m in enumerate(top, 1):
                row = QHBoxLayout()
                rank = QLabel(f"#{i}"); rank.setFixedWidth(30)
                rank.setStyleSheet("color:#059669; font-weight:700;")
                name = QLabel(str(m.get("full_name", m.get("member_id", ""))))
                name.setStyleSheet("")  # Use default text color
                count = QLabel(f"{m.get('count', 0)} check-ins")
                count.setStyleSheet("color:#374151; font-size:11px;")
                row.addWidget(rank); row.addWidget(name)
                row.addStretch(); row.addWidget(count)
                self._top_list_layout.addLayout(row)

    @staticmethod
    def _make_metric_card(icon, label, value, color):
        card = QFrame(); card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay = QVBoxLayout(card); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(4)
        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("Segoe UI", 28, QFont.Weight.Black))
        val_lbl.setStyleSheet(f"color: {color};")  
        lbl_lbl = QLabel(f"{icon}  {label}")
        lbl_lbl.setWordWrap(True)
        lbl_lbl.setStyleSheet("color: #111827; font-size:11px; font-weight:700;") # Match exact dark text from image
        lay.addWidget(val_lbl); lay.addWidget(lbl_lbl)
        return card, val_lbl
