"""ui/pages/packages_page.py — Card-based package gallery (pure PyQt6)."""
from __future__ import annotations
import math

from PyQt6.QtCore import Qt, QRect, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QBrush, QPen,
    QLinearGradient, QRadialGradient, QPolygonF,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QFrame, QGridLayout, QComboBox,
)
from libs.DataConnector import DataConnector
from model.Package import Package


# ── Tier color palette by price ───────────────────────────────────────────────
def _tier_colors(price: float):
    """Return (color1, color2, tier_label) based on price."""
    if price < 400_000:
        return "#60A5FA", "#3B82F6", "BASIC"
    elif price < 1_000_000:
        return "#B0EFCD", "#34D399", "PLUS"
    elif price < 2_000_000:
        return "#818CF8", "#A78BFA", "PRO"
    else:
        return "#FBBF24", "#F59E0B", "PREMIUM"


# ── Package icon by keyword ───────────────────────────────────────────────────
def _package_icon(name: str) -> str:
    n = name.lower()
    if "annual" in n or "year" in n or "premium" in n: return "👑"
    if "quarter" in n or "3" in n:                      return "💎"
    if "plus" in n or "pro" in n:                       return "⭐"
    if "basic" in n or "starter" in n:                  return "🏃"
    return "📦"


# ── Individual package card ───────────────────────────────────────────────────
class _PackageCard(QFrame):
    CARD_W = 248
    CARD_H = 340

    def __init__(self, package: Package, on_edit, on_delete, is_staff=False, parent=None):
        super().__init__(parent)
        self._pkg       = package
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._hovered   = False

        try:
            price = float(package.price)
        except (ValueError, TypeError):
            price = 0.0

        color1, color2, tier = _tier_colors(price)
        self._color1, self._color2 = color1, color2

        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 18)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Top row: icon + tier badge ────────────────────────────────────────
        top_row = QHBoxLayout(); top_row.setSpacing(0)

        icon_lbl = QLabel(_package_icon(package.name))
        icon_lbl.setFont(QFont("Segoe UI", 28))
        icon_lbl.setFixedSize(50, 50)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(icon_lbl)
        top_row.addStretch()

        tier_badge = QLabel(f" {tier} ")
        tier_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Black))
        tier_badge.setStyleSheet(
            f"color:#111827; background:{color1}; border-radius:6px;"
            f"padding:3px 8px;"
        )
        tier_badge.setFixedHeight(22)
        top_row.addWidget(tier_badge, alignment=Qt.AlignmentFlag.AlignTop)
        lay.addLayout(top_row)
        lay.addSpacing(12)

        # ── Package Name ──────────────────────────────────────────────────────
        name_lbl = QLabel(package.name)
        name_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Black))
        name_lbl.setStyleSheet(f"color:{color1};")
        name_lbl.setWordWrap(True)
        lay.addWidget(name_lbl)
        lay.addSpacing(4)

        # ── Description ───────────────────────────────────────────────────────
        desc_lbl = QLabel(package.description)
        desc_lbl.setFont(QFont("Segoe UI", 9))
        desc_lbl.setStyleSheet("color:#64748B;")
        desc_lbl.setWordWrap(True)
        desc_lbl.setMaximumHeight(44)
        lay.addWidget(desc_lbl)
        lay.addSpacing(16)

        # ── Divider ───────────────────────────────────────────────────────────
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("border:none; border-top:1px solid rgba(255,255,255,0.07);")
        lay.addWidget(div)
        lay.addSpacing(14)

        # ── Price (big) ───────────────────────────────────────────────────────
        try:
            price_text = f"{float(package.price):,.0f}"
        except Exception:
            price_text = str(package.price)

        price_row = QHBoxLayout(); price_row.setSpacing(4)
        price_lbl = QLabel(price_text)
        price_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Black))
        price_lbl.setStyleSheet(f"color:#F8FAFC;")
        cur_lbl = QLabel("VND")
        cur_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        cur_lbl.setStyleSheet("color:#64748B;")
        cur_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        price_row.addWidget(price_lbl)
        price_row.addWidget(cur_lbl)
        price_row.addStretch()
        lay.addLayout(price_row)
        lay.addSpacing(10)

        # ── Duration pill ─────────────────────────────────────────────────────
        dur_pill = QLabel(f"🗓  {package.duration_value} {package.duration_unit}")
        dur_pill.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        dur_pill.setStyleSheet(
            f"color:{color1}; background:rgba(255,255,255,0.05);"
            f"border-radius:8px; padding:4px 12px;"
        )
        dur_pill.setFixedHeight(30)
        lay.addWidget(dur_pill, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addSpacing(8)

        # ── Package ID label ──────────────────────────────────────────────────
        id_lbl = QLabel(f"🆔  {package.package_id}")
        id_lbl.setFont(QFont("Segoe UI", 8))
        id_lbl.setStyleSheet("color:#475569;")
        lay.addWidget(id_lbl)

        lay.addStretch()

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)

        if not is_staff:
            edit_btn = QPushButton("✏  Edit"); edit_btn.setFixedHeight(30)
            edit_btn.setStyleSheet(
                f"QPushButton{{background:rgba(255,255,255,0.07);color:#e2e8f0;"
                f"border:1px solid rgba(255,255,255,0.12);border-radius:8px;"
                f"font-size:11px;font-weight:600;}}"
                f"QPushButton:hover{{background:{color1};color:#111827;border:none;}}"
            )
            edit_btn.clicked.connect(lambda: self._on_edit(self._pkg))

            del_btn = QPushButton("🗑"); del_btn.setFixedSize(30, 30)
            del_btn.setStyleSheet(
                "QPushButton{background:rgba(248,113,113,0.12);color:#F87171;"
                "border:none;border-radius:8px;font-size:13px;}"
                "QPushButton:hover{background:#F87171;color:#fff;}"
            )
            del_btn.clicked.connect(lambda: self._on_delete(self._pkg))
            btn_row.addWidget(edit_btn, 1); btn_row.addWidget(del_btn)
        else:
            view_lbl = QLabel("👁  View Only")
            view_lbl.setStyleSheet("color:#475569; font-size:10px;")
            btn_row.addWidget(view_lbl)

        lay.addLayout(btn_row)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor("#232E3D") if self._hovered else QColor("#1E2532")
        path = QPainterPath(); path.addRoundedRect(0, 0, self.width(), self.height(), 18, 18)
        p.fillPath(path, QBrush(bg))

        # Top accent strip
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(self._color1))
        grad.setColorAt(1, QColor(self._color2))
        strip = QPainterPath(); strip.addRoundedRect(0, 0, self.width(), 5, 3, 3)
        p.fillPath(strip, QBrush(grad))

        # Subtle glow border on hover
        if self._hovered:
            bc = QColor(self._color1); bc.setAlpha(110)
            p.setPen(QPen(bc, 1.5))
            bp = QPainterPath(); bp.addRoundedRect(0.75, 0.75, self.width()-1.5, self.height()-1.5, 18, 18)
            p.drawPath(bp)

    def enterEvent(self, e): self._hovered = True;  self.update(); super().enterEvent(e)
    def leaveEvent(self, e): self._hovered = False; self.update(); super().leaveEvent(e)


# ── Main PackagesPage ─────────────────────────────────────────────────────────
class PackagesPage(QWidget):
    COLS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc   = DataConnector()
        self._data: list[Package] = []
        self.user  = None          # set by MainWindowEx for role checks
        self._build()

    def _is_staff(self) -> bool:
        return self.user is not None and str(getattr(self.user, "role", "")).lower() == "staff"

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(14)

        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search packages…")
        self._search.setMinimumHeight(36)
        self._search.textChanged.connect(self._filter)
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color:#64748B; font-size:12px;")
        self._add_btn = QPushButton("＋  Add Package")
        self._add_btn.setObjectName("primaryBtn")
        self._add_btn.setMinimumHeight(36)
        self._add_btn.clicked.connect(self._add)
        tb.addWidget(self._search)
        tb.addWidget(self._count_lbl)
        tb.addStretch()
        tb.addWidget(self._add_btn)
        lay.addLayout(tb)

        # ── Scroll area ───────────────────────────────────────────────────────
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
        self._data = self._dc.get_all_packages()
        # Hide add button for staff
        self._add_btn.setVisible(not self._is_staff())
        self._render(self._data)

    def _filter(self, text: str):
        t = text.lower()
        self._render([p for p in self._data
                      if t in p.name.lower() or t in p.description.lower() or t in p.package_id.lower()])

    def _render(self, packages: list[Package]):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not packages:
            lbl = QLabel("No packages found.")
            lbl.setStyleSheet("color:#64748B; font-size:14px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(lbl, 0, 0)
        else:
            for i, pkg in enumerate(packages):
                card = _PackageCard(pkg, self._edit_pkg, self._delete_pkg, is_staff=self._is_staff())
                self._grid.addWidget(card, i // self.COLS, i % self.COLS)

        self._count_lbl.setText(f"{len(packages)} package(s)")

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def _add(self):
        if self._is_staff():
            QMessageBox.warning(self, "Access Denied", "Staff cannot add packages.")
            return
        dlg = _PackageDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result())
            self._dc.save_packages(self._data)
            self.refresh()

    def _edit_pkg(self, pkg: Package):
        if self._is_staff():
            QMessageBox.warning(self, "Access Denied", "Staff cannot edit packages.")
            return
        dlg = _PackageDialog(self, pkg)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            idx = next((i for i, p in enumerate(self._data) if p.package_id == pkg.package_id), None)
            if idx is not None:
                self._data[idx] = dlg.result()
                self._dc.save_packages(self._data)
                self.refresh()

    def _delete_pkg(self, pkg: Package):
        if self._is_staff():
            QMessageBox.warning(self, "Access Denied", "Staff cannot delete packages.")
            return
        if QMessageBox.question(self, "Delete", f"Delete package '{pkg.name}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data = [p for p in self._data if p.package_id != pkg.package_id]
            self._dc.save_packages(self._data)
            self.refresh()


# ── Add/Edit dialog ───────────────────────────────────────────────────────────
class _PackageDialog(QDialog):
    def __init__(self, parent=None, p: Package = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Package" if p else "Add Package")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self); form = QFormLayout(); form.setSpacing(10); lay.addLayout(form)

        self.id_in    = QLineEdit();   self.id_in.setMinimumHeight(34)
        self.name_in  = QLineEdit();   self.name_in.setMinimumHeight(34)
        self.unit_cb  = QComboBox();   self.unit_cb.addItems(["months", "days"]); self.unit_cb.setMinimumHeight(34)
        self.dur_in   = QLineEdit();   self.dur_in.setMinimumHeight(34)
        self.price_in = QLineEdit();   self.price_in.setMinimumHeight(34)
        self.desc_in  = QLineEdit();   self.desc_in.setMinimumHeight(34)

        form.addRow("Package ID",     self.id_in)
        form.addRow("Name",           self.name_in)
        form.addRow("Duration Unit",  self.unit_cb)
        form.addRow("Duration Value", self.dur_in)
        form.addRow("Price (VND)",    self.price_in)
        form.addRow("Description",    self.desc_in)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)

        if p:
            self.id_in.setText(p.package_id);      self.name_in.setText(p.name)
            self.unit_cb.setCurrentText(p.duration_unit)
            self.dur_in.setText(str(p.duration_value))
            self.price_in.setText(str(p.price));   self.desc_in.setText(p.description)

    def result(self) -> Package:
        return Package(
            self.id_in.text().strip(), self.name_in.text().strip(),
            self.unit_cb.currentText(), self.dur_in.text().strip(),
            self.price_in.text().strip(), self.desc_in.text().strip(),
        )
