"""
ui/dialogs/face_register_dialog.py
────────────────────────────────────
Captures N face samples from the webcam for a given member.
Camera runs in a QThread — works in both PyCharm and terminal.
"""
from __future__ import annotations

import cv2
import numpy as np

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QProgressBar, QMessageBox)

from libs.FaceRecognizer import FaceRecognizer

N_SAMPLES = 8


class _CamWorker(QThread):
    frame_ready = pyqtSignal(np.ndarray, list)   # display_frame, faces list
    error       = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running    = True
        self._recognizer = FaceRecognizer()

    def stop(self) -> None:
        self._running = False
        self.wait(3000)

    def run(self) -> None:
        import sys
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        cap = cv2.VideoCapture(0, backend)
        if not cap.isOpened():
            self.error.emit("Could not open camera."); return
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    self.msleep(20); continue
                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = list(self._recognizer.detect_faces(gray))
                disp  = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(disp, (x, y), (x+w, y+h), (52, 211, 153), 2)
                self.frame_ready.emit(disp, faces)
                self.msleep(40)
        finally:
            cap.release()


class FaceRegisterDialog(QDialog):
    def __init__(self, member_id: str, member_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Register Face — {member_name} ({member_id})")
        self.setMinimumSize(540, 500)
        self.setModal(True)

        self._member_id  = member_id
        self._recognizer = FaceRecognizer()
        self._worker: _CamWorker | None = None
        self._last_frame: np.ndarray | None = None
        self._last_faces: list             = []
        self._captured   = 0

        lay = QVBoxLayout(self); lay.setSpacing(12)

        self._cam_lbl = QLabel("Starting camera…")
        self._cam_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cam_lbl.setMinimumHeight(360)
        self._cam_lbl.setStyleSheet("background:#0b0f14; border-radius:12px;")
        lay.addWidget(self._cam_lbl)

        self._status = QLabel(f"Samples captured: 0 / {N_SAMPLES}")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._status)

        self._bar = QProgressBar()
        self._bar.setMaximum(N_SAMPLES); self._bar.setValue(0)
        self._bar.setMinimumHeight(10); self._bar.setTextVisible(False)
        lay.addWidget(self._bar)

        btns = QHBoxLayout()
        self._cap_btn  = QPushButton("📸  Capture Sample")
        self._cap_btn.setObjectName("primaryBtn"); self._cap_btn.setMinimumHeight(40)
        self._cap_btn.clicked.connect(self._capture_sample)
        self._done_btn = QPushButton("✅  Done")
        self._done_btn.setObjectName("secondaryBtn"); self._done_btn.setMinimumHeight(40)
        self._done_btn.setEnabled(False); self._done_btn.clicked.connect(self._finish)
        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self._cap_btn); btns.addWidget(self._done_btn); btns.addWidget(cancel_btn)
        lay.addLayout(btns)

        self._worker = _CamWorker()
        self._worker.frame_ready.connect(self._on_frame)
        self._worker.error.connect(lambda e: self._status.setText(f"❌ {e}"))
        self._worker.start()

    def _on_frame(self, disp: np.ndarray, faces: list) -> None:
        self._last_frame = disp
        self._last_faces = faces
        rgb = cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data.tobytes(), w, h, ch * w, QImage.Format.Format_RGB888)
        self._cam_lbl.setPixmap(
            QPixmap.fromImage(img).scaled(
                self._cam_lbl.width(), self._cam_lbl.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _capture_sample(self) -> None:
        if self._last_frame is None or not self._last_faces:
            QMessageBox.warning(self, "No face", "No face detected. Look at the camera."); return
        gray = cv2.cvtColor(self._last_frame, cv2.COLOR_BGR2GRAY)
        x, y, w, h = self._last_faces[0]
        roi = gray[y:y+h, x:x+w]
        self._recognizer.save_sample(self._member_id, roi)
        self._captured += 1
        self._bar.setValue(self._captured)
        self._status.setText(f"Samples captured: {self._captured} / {N_SAMPLES}")
        if self._captured >= N_SAMPLES:
            self._cap_btn.setEnabled(False)
            self._done_btn.setEnabled(True)
            self._status.setText(f"✅ {N_SAMPLES} samples captured! Click Done.")

    def _finish(self) -> None:
        self._cleanup(); self.accept()

    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def closeEvent(self, event): self._cleanup(); super().closeEvent(event)
    def reject(self):            self._cleanup(); super().reject()
