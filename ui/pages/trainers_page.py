"""ui/pages/trainers_page.py — Card-based trainer gallery with stats & rating (pure PyQt6)."""
from __future__ import annotations
import math

from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QBrush, QPen,
    QLinearGradient, QRadialGradient, QPolygonF,
)
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QFrame, QGridLayout, QDoubleSpinBox, QSpinBox,
)
from libs.DataConnector import DataConnector
from model.Trainer import Trainer


# ── Specialty → accent color mapping ─────────────────────────────────────────
_SPECIALTY_COLORS = {
    "strength":      ("#FF6B6B", "#FF8E53"),
    "yoga":          ("#B0EFCD", "#6DD5FA"),
    "cardio":        ("#FBBF24", "#F59E0B"),
    "crossfit":      ("#818CF8", "#A78BFA"),
    "pilates":       ("#F9A8D4", "#EC4899"),
    "bodybuilding":  ("#34D399", "#059669"),
    "conditioning":  ("#60A5FA", "#3B82F6"),
    "flexibility":   ("#B0EFCD", "#6DD5FA"),
}

def _accent_for(specialty: str):
    s = specialty.lower()
    for key, colors in _SPECIALTY_COLORS.items():
        if key in s:
            return colors
    return ("#B0EFCD", "#7DA5FF")


# ── Avatar: renders initials in a gradient circle ─────────────────────────────
class _AvatarLabel(QWidget):
    def __init__(self, name: str, color1: str, color2: str, size=68, parent=None):
        super().__init__(parent)
        self._initials = "".join(w[0].upper() for w in name.split()[:2])
        self._c1, self._c2 = QColor(color1), QColor(color2)
        self._sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QRadialGradient(self._sz / 2, self._sz / 2, self._sz / 2)
        grad.setColorAt(0, self._c1)
        grad.setColorAt(1, self._c2)
        path = QPainterPath()
        path.addEllipse(0, 0, self._sz, self._sz)
        p.fillPath(path, QBrush(grad))
        p.setPen(QPen(QColor("#FFFFFF")))
        p.setFont(QFont("Segoe UI", int(self._sz * 0.28), QFont.Weight.Black))
        p.drawText(QRect(0, 0, self._sz, self._sz), Qt.AlignmentFlag.AlignCenter, self._initials)


# ── Star rating widget — draws filled/half/empty stars ────────────────────────
class _StarRating(QWidget):
    def __init__(self, rating: float, color: str = "#FBBF24", star_size=14, parent=None):
        super().__init__(parent)
        self._rating    = min(max(rating, 0), 5)
        self._color     = QColor(color)
        self._dim_color = QColor("#374151")
        self._sz        = star_size
        total_w = star_size * 5 + 4 * 3 + 50   # 5 stars + gaps + text label
        self.setFixedSize(total_w, star_size + 4)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sz = self._sz
        for i in range(5):
            x = i * (sz + 3)
            y = 2
            fill = self._rating - i   # fraction of this star to fill: >1 full, 0..1 partial, <0 empty
            self._draw_star(p, x, y, sz, fill)

        # text label e.g. "4.9/5"
        p.setPen(QPen(QColor("#D1D5DB")))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(
            QRect(5 * (sz + 3) + 4, 0, 50, sz + 4),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"{self._rating:.1f}/5"
        )

    def _draw_star(self, p: QPainter, x: int, y: int, sz: int, fill: float):
        """Draw one star at (x, y) filled by 'fill' fraction (0‥1+)."""
        pts = self._star_polygon(x + sz / 2, y + sz / 2, sz / 2, sz / 4.5)

        if fill >= 1.0:
            p.setBrush(QBrush(self._color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(pts)
        elif fill <= 0:
            p.setBrush(QBrush(self._dim_color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(pts)
        else:
            # Draw dim background
            p.setBrush(QBrush(self._dim_color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(pts)
            # Clip left portion
            p.save()
            p.setClipRect(QRectF(x, y, sz * fill, sz))
            p.setBrush(QBrush(self._color))
            p.drawPolygon(pts)
            p.restore()

    @staticmethod
    def _star_polygon(cx: float, cy: float, outer: float, inner: float) -> QPolygonF:
        pts = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = outer if i % 2 == 0 else inner
            pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return QPolygonF(pts)


# ── Individual trainer card ───────────────────────────────────────────────────
class _TrainerCard(QFrame):
    CARD_W = 248
    CARD_H = 370

    def __init__(self, trainer: Trainer, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self._trainer   = trainer
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._hovered   = False
        color1, color2  = _accent_for(trainer.specialty)
        self._color1, self._color2 = color1, color2

        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 24, 20, 18)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Avatar ────────────────────────────────────────────────────────────
        avatar = _AvatarLabel(trainer.full_name, color1, color2, size=68)
        lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addSpacing(12)

        # ── Name ──────────────────────────────────────────────────────────────
        name_lbl = QLabel(trainer.full_name)
        name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Black))
        name_lbl.setStyleSheet(f"color: {color1};")
        name_lbl.setWordWrap(True)
        lay.addWidget(name_lbl)
        lay.addSpacing(3)

        # ── Specialty ─────────────────────────────────────────────────────────
        spec_lbl = QLabel(f"🏅  {trainer.specialty}")
        spec_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        spec_lbl.setStyleSheet("color:#94A3B8;")
        spec_lbl.setWordWrap(True)
        lay.addWidget(spec_lbl)
        lay.addSpacing(12)

        # ── Divider ───────────────────────────────────────────────────────────
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("border:none; border-top:1px solid rgba(255,255,255,0.07);")
        lay.addWidget(div)
        lay.addSpacing(10)

        # ── Stats row (experience + trainees) ─────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(0)

        for icon, value, label in [
            ("⚡", f"{trainer.experience_years} yrs", "Experience"),
            ("👥", f"{trainer.total_trainees}+",      "Trainees"),
        ]:
            stat_w = QWidget()
            stat_l = QVBoxLayout(stat_w)
            stat_l.setContentsMargins(0, 0, 0, 0)
            stat_l.setSpacing(1)

            val_lbl = QLabel(f"{icon} {value}")
            val_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Black))
            val_lbl.setStyleSheet(f"color:{color1};")

            key_lbl = QLabel(label)
            key_lbl.setFont(QFont("Segoe UI", 8))
            key_lbl.setStyleSheet("color:#64748B;")

            stat_l.addWidget(val_lbl)
            stat_l.addWidget(key_lbl)
            stats_row.addWidget(stat_w, 1)

        lay.addLayout(stats_row)
        lay.addSpacing(10)

        # ── Star rating ───────────────────────────────────────────────────────
        stars = _StarRating(trainer.rating, color=color1)
        lay.addWidget(stars, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addSpacing(10)

        # ── Divider ───────────────────────────────────────────────────────────
        div2 = QFrame(); div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("border:none; border-top:1px solid rgba(255,255,255,0.07);")
        lay.addWidget(div2)
        lay.addSpacing(8)

        # ── Contact / schedule ────────────────────────────────────────────────
        for icon, text in [
            ("📞", trainer.phone),
            ("🕐", trainer.availability_schedule),
        ]:
            row = QHBoxLayout(); row.setSpacing(8)
            ico = QLabel(icon); ico.setFixedWidth(18); ico.setStyleSheet("font-size:12px;")
            txt = QLabel(text); txt.setFont(QFont("Segoe UI", 9)); txt.setStyleSheet("color:#94A3B8;"); txt.setWordWrap(True)
            row.addWidget(ico); row.addWidget(txt, 1)
            lay.addLayout(row)
            lay.addSpacing(3)

        lay.addStretch()

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        edit_btn = QPushButton("✏  Edit"); edit_btn.setFixedHeight(30)
        edit_btn.setStyleSheet(
            f"QPushButton{{background:rgba(255,255,255,0.07);color:#e2e8f0;border:1px solid rgba(255,255,255,0.12);"
            f"border-radius:8px;font-size:11px;font-weight:600;}}"
            f"QPushButton:hover{{background:{color1};color:#111827;border:none;}}"
        )
        edit_btn.clicked.connect(lambda: self._on_edit(self._trainer))

        del_btn = QPushButton("🗑"); del_btn.setFixedSize(30, 30)
        del_btn.setStyleSheet(
            "QPushButton{background:rgba(248,113,113,0.12);color:#F87171;border:none;border-radius:8px;font-size:13px;}"
            "QPushButton:hover{background:#F87171;color:#fff;}"
        )
        del_btn.clicked.connect(lambda: self._on_delete(self._trainer))

        btn_row.addWidget(edit_btn, 1); btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor("#232E3D") if self._hovered else QColor("#1E2532")
        path = QPainterPath(); path.addRoundedRect(0, 0, self.width(), self.height(), 18, 18)
        p.fillPath(path, QBrush(bg))

        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(self._color1))
        grad.setColorAt(1, QColor(self._color2))
        strip = QPainterPath(); strip.addRoundedRect(0, 0, self.width(), 5, 3, 3)
        p.fillPath(strip, QBrush(grad))

        if self._hovered:
            bc = QColor(self._color1); bc.setAlpha(100)
            p.setPen(QPen(bc, 1.5))
            bp = QPainterPath(); bp.addRoundedRect(0.75, 0.75, self.width()-1.5, self.height()-1.5, 18, 18)
            p.drawPath(bp)

    def enterEvent(self, e): self._hovered = True;  self.update(); super().enterEvent(e)
    def leaveEvent(self, e): self._hovered = False; self.update(); super().leaveEvent(e)


# ── Main Trainers Page ────────────────────────────────────────────────────────
class TrainersPage(QWidget):
    COLS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc   = DataConnector()
        self._data: list[Trainer] = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(14)

        tb = QHBoxLayout()
        self._search = QLineEdit(); self._search.setPlaceholderText("🔍  Search trainers…"); self._search.setMinimumHeight(36)
        self._search.textChanged.connect(self._filter)
        self._count_lbl = QLabel(""); self._count_lbl.setStyleSheet("color:#64748B;font-size:12px;")
        add_btn = QPushButton("＋  Add Trainer"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addWidget(self._search); tb.addWidget(self._count_lbl); tb.addStretch(); tb.addWidget(add_btn)
        lay.addLayout(tb)

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("background:transparent;")

        self._grid_widget = QWidget(); self._grid_widget.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(20)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_widget)
        lay.addWidget(self._scroll)

    def refresh(self):
        self._data = self._dc.get_all_trainers()
        self._render(self._data)

    def _filter(self, text: str):
        t = text.lower()
        self._render([tr for tr in self._data if t in tr.full_name.lower() or t in tr.specialty.lower() or t in tr.phone])

    def _render(self, trainers: list[Trainer]):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not trainers:
            lbl = QLabel("No trainers found."); lbl.setStyleSheet("color:#64748B;font-size:14px;"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(lbl, 0, 0)
        else:
            for i, t in enumerate(trainers):
                self._grid.addWidget(_TrainerCard(t, self._edit_trainer, self._delete_trainer), i // self.COLS, i % self.COLS)
        self._count_lbl.setText(f"{len(trainers)} trainer(s)")

    def _add(self):
        dlg = _TrainerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_trainers(self._data); self.refresh()

    def _edit_trainer(self, trainer: Trainer):
        dlg = _TrainerDialog(self, trainer)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            idx = next((i for i, t in enumerate(self._data) if t.trainer_id == trainer.trainer_id), None)
            if idx is not None:
                self._data[idx] = dlg.result(); self._dc.save_trainers(self._data); self.refresh()

    def _delete_trainer(self, trainer: Trainer):
        if QMessageBox.question(self, "Delete", f"Delete trainer '{trainer.full_name}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data = [t for t in self._data if t.trainer_id != trainer.trainer_id]
            self._dc.save_trainers(self._data); self.refresh()


# ── Add/Edit dialog ───────────────────────────────────────────────────────────
class _TrainerDialog(QDialog):
    def __init__(self, parent=None, t: Trainer = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Trainer" if t else "Add Trainer"); self.setMinimumWidth(380)
        lay = QVBoxLayout(self); form = QFormLayout(); form.setSpacing(10); lay.addLayout(form)

        self.id_in    = QLineEdit();       self.id_in.setMinimumHeight(34)
        self.name_in  = QLineEdit();       self.name_in.setMinimumHeight(34)
        self.phone_in = QLineEdit();       self.phone_in.setMinimumHeight(34)
        self.spec_in  = QLineEdit();       self.spec_in.setMinimumHeight(34)
        self.sched_in = QLineEdit();       self.sched_in.setMinimumHeight(34)
        self.exp_in   = QSpinBox();        self.exp_in.setMinimumHeight(34); self.exp_in.setRange(0, 50); self.exp_in.setSuffix(" years")
        self.trainees_in = QSpinBox();     self.trainees_in.setMinimumHeight(34); self.trainees_in.setRange(0, 9999); self.trainees_in.setSuffix(" trainees")
        self.rating_in = QDoubleSpinBox(); self.rating_in.setMinimumHeight(34); self.rating_in.setRange(0.0, 5.0); self.rating_in.setSingleStep(0.1); self.rating_in.setDecimals(1)

        form.addRow("Trainer ID",     self.id_in)
        form.addRow("Full Name",      self.name_in)
        form.addRow("Phone",          self.phone_in)
        form.addRow("Specialty",      self.spec_in)
        form.addRow("Schedule",       self.sched_in)
        form.addRow("Experience",     self.exp_in)
        form.addRow("Total Trainees", self.trainees_in)
        form.addRow("Rating (0-5)",   self.rating_in)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)

        if t:
            self.id_in.setText(t.trainer_id);    self.name_in.setText(t.full_name)
            self.phone_in.setText(t.phone);       self.spec_in.setText(t.specialty)
            self.sched_in.setText(t.availability_schedule)
            self.exp_in.setValue(t.experience_years)
            self.trainees_in.setValue(t.total_trainees)
            self.rating_in.setValue(t.rating)

    def result(self) -> Trainer:
        return Trainer(
            self.id_in.text().strip(), self.name_in.text().strip(),
            self.phone_in.text().strip(), self.spec_in.text().strip(),
            self.sched_in.text().strip(),
            self.exp_in.value(), self.trainees_in.value(), self.rating_in.value(),
        )
