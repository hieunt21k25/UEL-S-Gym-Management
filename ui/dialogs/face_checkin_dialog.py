"""
ui/dialogs/face_checkin_dialog.py
──────────────────────────────────
Webcam dialog for face-based check-in.
- Camera capture runs in a QThread (avoids PyCharm debugger deadlocks)
- LBPH recognition on each frame
- Auto-check-in after HOLD_FRAMES consecutive matches (~1.5 s)
"""
from __future__ import annotations

import cv2
import numpy as np

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QDialog, QVBoxLayout,
                              QLabel, QPushButton, QMessageBox)

from libs.FaceRecognizer import FaceRecognizer
from libs.DataConnector  import DataConnector

HOLD_FRAMES = 38   # ~1.5 s at 25 fps


class _CameraWorker(QThread):
    """Capture + recognise in a background thread; emit signals to the UI thread."""
    frame_ready  = pyqtSignal(np.ndarray, object, float)   # display_frame, member_id|None, confidence
    error        = pyqtSignal(str)

    def __init__(self, recognizer: FaceRecognizer) -> None:
        super().__init__()
        self._recognizer = recognizer
        self._running    = True

    def stop(self) -> None:
        self._running = False
        self.wait(3000)

    def run(self) -> None:
        import sys
        # CAP_DSHOW is stable on Windows in QThread; fall back for other OS
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        cap = cv2.VideoCapture(0, backend)
        if not cap.isOpened():
            self.error.emit("Could not open camera (index 0).")
            return
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    continue
                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self._recognizer.detect_faces(gray)
                disp  = frame.copy()
                matched_id: str | None = None
                best_conf = 999.0

                for (x, y, w, h) in faces:
                    roi       = gray[y:y+h, x:x+w]
                    mid, conf = self._recognizer.predict(roi)
                    if mid:
                        matched_id = mid
                        best_conf  = conf
                        color = (52, 211, 153)   # green
                        cv2.rectangle(disp, (x, y), (x+w, y+h), color, 3)
                        cv2.putText(disp, f"{mid}  ({conf:.0f})",
                                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.65, color, 2, cv2.LINE_AA)
                    else:
                        cv2.rectangle(disp, (x, y), (x+w, y+h), (100, 100, 200), 2)

                self.frame_ready.emit(disp, matched_id, best_conf)
                self.msleep(40)   # ~25 fps
        finally:
            cap.release()


class FaceCheckinDialog(QDialog):
    """Show webcam feed; auto-check-in when a recognised face holds for ~1.5 s."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Face Check-in")
        self.setMinimumSize(580, 520)
        self.setModal(True)

        self._recognizer   = FaceRecognizer()
        self._dc           = DataConnector()
        self._worker: _CameraWorker | None = None
        self._hold_member: str | None      = None
        self._hold_count   = 0
        self._done         = False

        self._member_cache = {m.member_id: m.full_name for m in self._dc.get_all_members()}

        self._trained = self._recognizer.train()

        lay = QVBoxLayout(self); lay.setSpacing(12)

        # ── No face data ──────────────────────────────────────────────────────
        if not self._trained:
            warn = QLabel(
                "⚠️  No face data found.\n\n"
                "Go to Members → select a member → Register Face\n"
                "to enrol faces before using face check-in.",
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            warn.setStyleSheet("font-size:13px; color:#94a3b8;")
            lay.addWidget(warn)
            ok = QPushButton("OK"); ok.setObjectName("primaryBtn")
            ok.setMinimumHeight(40); ok.clicked.connect(self.accept)
            lay.addWidget(ok)
            return

        # ── Camera view ───────────────────────────────────────────────────────
        self._cam_lbl = QLabel("Starting camera…")
        self._cam_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cam_lbl.setMinimumHeight(380)
        self._cam_lbl.setStyleSheet("background:#0b0f14; border-radius:12px;")
        lay.addWidget(self._cam_lbl)

        self._status = QLabel("Looking for a registered face…")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("font-size:14px; font-weight:600; color:#e2e8f0;")
        lay.addWidget(self._status)

        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(36)
        cancel_btn.clicked.connect(self.reject)
        lay.addWidget(cancel_btn)

        # ── Start worker ──────────────────────────────────────────────────────
        self._worker = _CameraWorker(self._recognizer)
        self._worker.frame_ready.connect(self._on_frame)
        self._worker.error.connect(lambda e: self._status.setText(f"❌ {e}"))
        self._worker.start()

    # ── Slots (always called in UI thread via queued connection) ──────────────

    def _on_frame(self, disp: np.ndarray,
                  matched_id: object, conf: float) -> None:
        if self._done:
            return
        self._show_frame(disp)

        mid: str | None = matched_id   # type: ignore[assignment]

        if mid:
            name = self._member_cache.get(mid, mid)
            if mid == self._hold_member:
                self._hold_count += 1
            else:
                self._hold_member = mid; self._hold_count = 1
            pct = min(100, int(self._hold_count / HOLD_FRAMES * 100))
            self._status.setText(f"✅  Recognised: {name}  —  {pct}%")
            if self._hold_count >= HOLD_FRAMES:
                self._do_checkin(mid)
        else:
            self._hold_member = None; self._hold_count = 0
            self._status.setText("Looking for a registered face…")

    def _do_checkin(self, member_id: str) -> None:
        self._done = True
        self._cleanup()
        ok, msg = self._dc.checkin_member(member_id)
        name = self._member_cache.get(member_id, member_id)
        if ok:
            QMessageBox.information(self, "Check-in Successful",
                f"👋  Welcome, {name}!\n\n{msg}")
        else:
            QMessageBox.warning(self, "Check-in Failed", f"{name}: {msg}")
        self.accept()

    def _show_frame(self, frame: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data.tobytes(), w, h, ch * w, QImage.Format.Format_RGB888)
        self._cam_lbl.setPixmap(
            QPixmap.fromImage(img).scaled(
                self._cam_lbl.width(), self._cam_lbl.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def closeEvent(self, event):  self._cleanup(); super().closeEvent(event)
    def reject(self):             self._cleanup(); super().reject()
