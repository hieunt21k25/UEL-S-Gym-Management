"""ui/pages/members_page.py — CRUD for Members via DataConnector."""
from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit, QPushButton, QLabel, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox)
from libs.DataConnector import DataConnector
from model.Member import Member


class MembersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dc = DataConnector()
        self._data: list[Member] = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        # Toolbar
        tb = QHBoxLayout()
        self.search_in = QLineEdit(); self.search_in.setPlaceholderText("🔍  Search name, phone, email…"); self.search_in.setMinimumHeight(36)
        self.search_in.textChanged.connect(self._filter)
        self.status_cb = QComboBox(); self.status_cb.setMinimumHeight(36); self.status_cb.addItems(["All", "active", "inactive"])
        self.status_cb.currentTextChanged.connect(self._filter)
        add_btn = QPushButton("＋  Add Member"); add_btn.setObjectName("primaryBtn"); add_btn.setMinimumHeight(36); add_btn.clicked.connect(self._add)
        tb.addWidget(self.search_in); tb.addWidget(self.status_cb); tb.addStretch(); tb.addWidget(add_btn)
        lay.addLayout(tb)
        # Table
        self.table = QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID","Full Name","Phone","Email","DOB","Gender","Join Date","Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        # Bottom
        bot = QHBoxLayout(); self.lbl = QLabel("")
        edit_btn  = QPushButton("✏  Edit");         edit_btn.setObjectName("secondaryBtn"); edit_btn.setMinimumHeight(34);  edit_btn.clicked.connect(self._edit)
        face_btn  = QPushButton("📷  Register Face"); face_btn.setObjectName("secondaryBtn"); face_btn.setMinimumHeight(34); face_btn.clicked.connect(self._register_face)
        del_btn   = QPushButton("🗑  Delete");        del_btn.setObjectName("dangerBtn");    del_btn.setMinimumHeight(34);  del_btn.clicked.connect(self._delete)
        bot.addWidget(self.lbl); bot.addStretch(); bot.addWidget(edit_btn); bot.addWidget(face_btn); bot.addWidget(del_btn)
        lay.addLayout(bot)

    def refresh(self):
        self._data = self._dc.get_all_members(); self._populate(self._data)

    def _populate(self, data):
        self.table.setRowCount(0)
        for m in data:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate([m.member_id, m.full_name, m.phone, m.email, m.dob, m.gender, m.join_date, m.status]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.lbl.setText(f"{len(data)} member(s)")

    def _filter(self):
        s = self.search_in.text().strip(); st = self.status_cb.currentText()
        filtered = self._dc.get_all_members(status=None if st == "All" else st, search=s or None)
        self._populate(filtered)

    def _sel(self):
        return self.table.currentRow() if self.table.selectedItems() else None

    def _add(self):
        dlg = _MemberDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data.append(dlg.result()); self._dc.save_members(self._data); self.refresh()

    def _edit(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a member."); return
        dlg = _MemberDialog(self, self._data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._data[idx] = dlg.result(); self._dc.save_members(self._data); self.refresh()

    def _delete(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a member."); return
        if QMessageBox.question(self, "Delete", f"Delete '{self._data[idx].full_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._data.pop(idx); self._dc.save_members(self._data); self.refresh()

    def _register_face(self):
        idx = self._sel()
        if idx is None: QMessageBox.information(self, "Select", "Please select a member first."); return
        m = self._data[idx]
        from ui.dialogs.face_register_dialog import FaceRegisterDialog
        dlg = FaceRegisterDialog(m.member_id, m.full_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            from libs.FaceRecognizer import FaceRecognizer
            count = FaceRecognizer().sample_count(m.member_id)
            QMessageBox.information(self, "Face Registered",
                f"Face data saved for {m.full_name}.\n{count} sample(s) stored.\nYou can now use Face Check-in.")


class _MemberDialog(QDialog):
    def __init__(self, parent=None, m: Member = None):
        super().__init__(parent); self.setWindowTitle("Edit Member" if m else "Add Member"); self.setMinimumWidth(400)
        lay = QVBoxLayout(self); form = QFormLayout(); lay.addLayout(form)
        self.id_in   = QLineEdit(); self.id_in.setMinimumHeight(34)
        self.name_in = QLineEdit(); self.name_in.setMinimumHeight(34)
        self.phone_in= QLineEdit(); self.phone_in.setMinimumHeight(34)
        self.email_in= QLineEdit(); self.email_in.setMinimumHeight(34)
        self.dob_in  = QLineEdit(); self.dob_in.setPlaceholderText("YYYY-MM-DD"); self.dob_in.setMinimumHeight(34)
        self.gender_cb = QComboBox(); self.gender_cb.addItems(["Male","Female","Other"]); self.gender_cb.setMinimumHeight(34)
        self.join_in = QLineEdit(); self.join_in.setPlaceholderText("YYYY-MM-DD"); self.join_in.setMinimumHeight(34)
        self.status_cb = QComboBox(); self.status_cb.addItems(["active","inactive"]); self.status_cb.setMinimumHeight(34)
        form.addRow("Member ID", self.id_in); form.addRow("Full Name", self.name_in)
        form.addRow("Phone",     self.phone_in); form.addRow("Email",  self.email_in)
        form.addRow("DOB",       self.dob_in);  form.addRow("Gender",  self.gender_cb)
        form.addRow("Join Date", self.join_in); form.addRow("Status",  self.status_cb)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
        if m:
            self.id_in.setText(m.member_id); self.name_in.setText(m.full_name)
            self.phone_in.setText(m.phone); self.email_in.setText(m.email)
            self.dob_in.setText(m.dob); self.gender_cb.setCurrentText(m.gender)
            self.join_in.setText(m.join_date); self.status_cb.setCurrentText(m.status)

    def result(self) -> Member:
        return Member(self.id_in.text().strip(), self.name_in.text().strip(),
                      self.phone_in.text().strip(), self.email_in.text().strip(),
                      self.dob_in.text().strip(), self.gender_cb.currentText(),
                      self.join_in.text().strip(), self.status_cb.currentText())
