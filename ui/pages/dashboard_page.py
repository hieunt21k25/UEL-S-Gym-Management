"""Dashboard page — metric cards + toggled charts + top members (JSON-based)."""
from __future__ import annotations
from collections import Counter
from datetime import date, datetime

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton,
    QStackedWidget,
)

from ui.pages.base_page import BasePage
from libs.DataConnector import DataConnector


class _DashWorker(QThread):
    done  = pyqtSignal(dict, list, list, dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            dc    = DataConnector()
            stats = dc.get_dashboard_stats()
            rev   = stats.pop("monthly_revenue", [])

            # Top members by check-ins this month
            mo = date.today().strftime("%Y-%m")
            cis = dc.get_all_checkins()
            members = {m.member_id: m.full_name for m in dc.get_all_members()}
            monthly = [c for c in cis if c.timestamp[:7] == mo]
            counts  = Counter(c.member_id for c in monthly)
            top = [
                {"member_id": mid, "full_name": members.get(mid, mid), "count": cnt}
                for mid, cnt in counts.most_common(8)
            ]

            # Extra data for new charts
            all_members = dc.get_all_members()
            gender_counts = Counter(getattr(m, "gender", "Unknown") for m in all_members)

            today_str = date.today().isoformat()
            today_cis = [c for c in cis if c.timestamp[:10] == today_str]
            hourly_counts = Counter(
                datetime.fromisoformat(c.timestamp).hour for c in today_cis
            )

            extra = {
                "gender": dict(gender_counts),
                "hourly_checkins": dict(hourly_counts),
            }

            self.done.emit(stats, rev, top, extra)
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

        # ── Bottom row: chart panel + top members ──────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        # ── Chart panel card ───────────────────────────────────────────────────
        self._chart_frame = QFrame()
        self._chart_frame.setObjectName("bottomCard")
        self._chart_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_outer = QVBoxLayout(self._chart_frame)
        chart_outer.setContentsMargins(20, 16, 20, 16)
        chart_outer.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        self._chart_title = QLabel("📈  Monthly Revenue (VND)")
        self._chart_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._chart_title.setStyleSheet("color: #F8FAFC;")
        title_row.addWidget(self._chart_title)
        title_row.addStretch()
        chart_outer.addLayout(title_row)

        # Toggle buttons
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)

        btn_style_active = (
            "QPushButton { background:#B0EFCD; color:#111827; border:none; border-radius:8px;"
            " padding:6px 14px; font-weight:700; font-size:12px; }"
        )
        btn_style_inactive = (
            "QPushButton { background:rgba(255,255,255,0.07); color:#b8c2cc; border:none;"
            " border-radius:8px; padding:6px 14px; font-weight:600; font-size:12px; }"
            "QPushButton:hover { background:rgba(255,255,255,0.12); color:#fff; }"
        )
        self._btn_style_active   = btn_style_active
        self._btn_style_inactive = btn_style_inactive

        self._btn_revenue  = QPushButton("📈 Revenue")
        self._btn_gender   = QPushButton("🥧 Gender Ratio")
        self._btn_checkins = QPushButton("📊 Daily Check-ins")
        for b in (self._btn_revenue, self._btn_gender, self._btn_checkins):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_row.addWidget(b)
        toggle_row.addStretch()
        chart_outer.addLayout(toggle_row)

        # Stacked pages: 0=revenue, 1=gender, 2=checkins
        self._chart_stack = QStackedWidget()
        self._chart_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_outer.addWidget(self._chart_stack)

        # Create three placeholder containers
        self._rev_widget  = QWidget(); self._rev_layout  = QVBoxLayout(self._rev_widget);  self._rev_layout.setContentsMargins(0,0,0,0)
        self._gen_widget  = QWidget(); self._gen_layout  = QVBoxLayout(self._gen_widget);  self._gen_layout.setContentsMargins(0,0,0,0)
        self._ci_widget   = QWidget(); self._ci_layout   = QVBoxLayout(self._ci_widget);   self._ci_layout.setContentsMargins(0,0,0,0)

        self._chart_stack.addWidget(self._rev_widget)
        self._chart_stack.addWidget(self._gen_widget)
        self._chart_stack.addWidget(self._ci_widget)

        self._btn_revenue.clicked.connect(lambda: self._switch_chart(0))
        self._btn_gender.clicked.connect(lambda:  self._switch_chart(1))
        self._btn_checkins.clicked.connect(lambda: self._switch_chart(2))
        self._switch_chart(0)  # default

        # ── Top members card ───────────────────────────────────────────────────
        self._top_frame = QFrame()
        self._top_frame.setObjectName("bottomCard")
        self._top_frame.setFixedWidth(280)
        top_layout = QVBoxLayout(self._top_frame)
        top_layout.setContentsMargins(20, 16, 20, 16)
        top_title = QLabel("🏆  Top Members")
        top_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        top_title.setStyleSheet("color: #F8FAFC;")
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

        # Store data for re-rendering on toggle
        self._rev_data  = []
        self._extra     = {}

    # ── Toggle ─────────────────────────────────────────────────────────────────

    def _switch_chart(self, idx: int):
        titles = ["📈  Monthly Revenue (VND)", "🥧  Gender Ratio", "📊  Daily Check-ins"]
        self._chart_title.setText(titles[idx])
        self._chart_stack.setCurrentIndex(idx)
        btns = [self._btn_revenue, self._btn_gender, self._btn_checkins]
        for i, b in enumerate(btns):
            b.setStyleSheet(self._btn_style_active if i == idx else self._btn_style_inactive)

    # ── Worker ─────────────────────────────────────────────────────────────────

    def refresh(self):
        self._status.setText("Loading…")
        self._worker = _DashWorker()
        self._worker.done.connect(self._populate)
        self._worker.error.connect(lambda e: self._status.setText(f"Error: {e}"))
        self._worker.start()

    def _populate(self, stats: dict, rev: list, top: list, extra: dict):
        self._status.setText("")
        self._rev_data = rev
        self._extra    = extra

        # Metric cards
        vals = [
            str(stats.get("total_members",         "0")),
            str(stats.get("new_members_today",     "0")),
            str(stats.get("new_members_month",     "0")),
            str(stats.get("total_revenue",         "0")),
            str(stats.get("expired_subscriptions", "0")),
        ]
        for lbl, val in zip(self._metric_widgets, vals):
            lbl.setText(val)

        self._render_revenue(rev)
        self._render_gender(extra.get("gender", {}))
        self._render_checkins(extra.get("hourly_checkins", {}))

        # Top members
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
                count = QLabel(f"{m.get('count', 0)} check-ins")
                count.setStyleSheet("color:#94A3B8; font-size:11px;")
                row.addWidget(rank); row.addWidget(name)
                row.addStretch(); row.addWidget(count)
                self._top_list_layout.addLayout(row)

    # ── Chart renderers ────────────────────────────────────────────────────────

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_revenue(self, rev: list):
        self._clear_layout(self._rev_layout)
        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
            from matplotlib.figure import Figure

            months   = [r["month"] for r in rev]
            revenues = [r["revenue"] for r in rev]

            fig = Figure(facecolor="none", tight_layout=True)
            ax  = fig.add_subplot(111, facecolor="none")

            ax.plot(range(len(months)), revenues,
                    color="#AEE8CB", marker="o", linestyle="-",
                    linewidth=3, markersize=8, zorder=3)
            ax.fill_between(range(len(months)), revenues,
                            color="#AEE8CB", alpha=0.12, zorder=2)

            if revenues:
                peak   = max(revenues, default=1)
                margin = peak * 0.20 if peak > 0 else 1
                ax.set_ylim(0, peak + margin)
                for x, val in enumerate(revenues):
                    if val > 0:
                        ax.text(x, val + peak * 0.05, f"{val:,.0f}",
                                ha="center", va="bottom",
                                color="#F8FAFC", fontsize=8, fontweight="bold")

            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=0, ha="center")
            ax.tick_params(colors="#e2e8f0", labelsize=8, pad=6)
            ax.spines[:].set_color("none")
            ax.yaxis.grid(True, color="#F8FAFC", alpha=0.1, linewidth=1, linestyle="--")

            canvas = Canvas(fig)
            canvas.setStyleSheet("background: transparent;")
            canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._rev_layout.addWidget(canvas)
        except Exception as ex:
            self._rev_layout.addWidget(QLabel(f"Chart unavailable: {ex}"))

    def _render_gender(self, gender: dict):
        self._clear_layout(self._gen_layout)
        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
            from matplotlib.figure import Figure

            labels = list(gender.keys())
            sizes  = list(gender.values())

            if not sizes or sum(sizes) == 0:
                lbl = QLabel("No member gender data available.")
                lbl.setStyleSheet("color:#94A3B8;")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._gen_layout.addWidget(lbl)
                return

            palette = ["#B0EFCD", "#7DA5FF", "#FFCD82", "#FF8FA3", "#C4B5FD"]
            colors  = [palette[i % len(palette)] for i in range(len(labels))]

            fig = Figure(facecolor="none", tight_layout=True)
            ax  = fig.add_subplot(111)
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors,
                autopct="%1.1f%%", startangle=140,
                textprops={"color": "#F8FAFC", "fontsize": 11},
                wedgeprops={"linewidth": 2, "edgecolor": "#1E2532"},
            )
            for at in autotexts:
                at.set_fontsize(10)
                at.set_fontweight("bold")
                at.set_color("#111827")
            ax.set_facecolor("none")

            canvas = Canvas(fig)
            canvas.setStyleSheet("background: transparent;")
            canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._gen_layout.addWidget(canvas)
        except Exception as ex:
            self._gen_layout.addWidget(QLabel(f"Chart unavailable: {ex}"))

    def _render_checkins(self, hourly: dict):
        self._clear_layout(self._ci_layout)
        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
            from matplotlib.figure import Figure

            # Show all 24 hours
            hours  = list(range(24))
            counts = [hourly.get(h, 0) for h in hours]
            total  = sum(counts)

            fig = Figure(facecolor="none", tight_layout=True)
            ax  = fig.add_subplot(111, facecolor="none")

            bar_colors = ["#B0EFCD" if c > 0 else (1, 1, 1, 0.05) for c in counts]
            bars = ax.bar(hours, counts, color=bar_colors, width=0.65, zorder=3)

            ax.set_xlim(-0.5, 23.5)
            ax.set_xticks(range(0, 24, 2))
            ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)], fontsize=7, rotation=45, ha="right")
            ax.tick_params(colors="#e2e8f0", labelsize=7, pad=4)
            ax.spines[:].set_color("none")
            ax.yaxis.grid(True, color="#F8FAFC", alpha=0.08, linewidth=1, linestyle="--")
            ax.set_ylabel("Check-ins", color="#b8c2cc", fontsize=9)

            # Annotate non-zero bars
            peak = max(counts, default=1)
            for bar, cnt in zip(bars, counts):
                if cnt > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, cnt + peak * 0.03,
                            str(cnt), ha="center", va="bottom",
                            color="#F8FAFC", fontsize=8, fontweight="bold")

            # Total label
            ax.set_title(f"Today's Check-ins — Total: {total}",
                         color="#F8FAFC", fontsize=10, pad=8, fontweight="bold")

            canvas = Canvas(fig)
            canvas.setStyleSheet("background: transparent;")
            canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._ci_layout.addWidget(canvas)
        except Exception as ex:
            self._ci_layout.addWidget(QLabel(f"Chart unavailable: {ex}"))

    # ── Metric card ────────────────────────────────────────────────────────────

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
        lbl_lbl.setStyleSheet("color: #111827; font-size:11px; font-weight:700;")
        lay.addWidget(val_lbl); lay.addWidget(lbl_lbl)
        return card, val_lbl
