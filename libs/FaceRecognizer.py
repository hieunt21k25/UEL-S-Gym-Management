"""
libs/FaceRecognizer.py
───────────────────────
Simple face recognition using OpenCV LBPH.
  - detect faces with Haar cascade
  - store N sample images per member under  dataset/faces/<member_id>/
  - train LBPH model from all stored samples
  - predict: returns (member_id, confidence) where confidence < 70 = good match
"""
from __future__ import annotations
from pathlib import Path

import cv2
import numpy as np

FACES_DIR = Path(__file__).resolve().parent.parent / "dataset" / "faces"
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"     # type: ignore
CONFIDENCE_THRESHOLD = 70   # LBPH: lower = better match; below this = recognised


class FaceRecognizer:
    def __init__(self) -> None:
        FACES_DIR.mkdir(parents=True, exist_ok=True)
        self._recognizer  = cv2.face.LBPHFaceRecognizer_create()    # type: ignore
        self._cascade     = cv2.CascadeClassifier(CASCADE_PATH)
        self._label_map: dict[int, str] = {}   # numeric label → member_id
        self._trained     = False

    # ── Training ──────────────────────────────────────────────────────────────

    def train(self) -> bool:
        """Re-train from ALL stored face images. Returns True if at ≥1 member."""
        faces:  list[np.ndarray] = []
        labels: list[int]        = []
        self._label_map          = {}
        label_idx                = 0

        for member_dir in sorted(FACES_DIR.iterdir()):
            if not member_dir.is_dir():
                continue
            imgs = sorted(member_dir.glob("*.jpg"))
            if not imgs:
                continue
            self._label_map[label_idx] = member_dir.name
            for p in imgs:
                gray = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
                if gray is None:
                    continue
                roi = cv2.resize(gray, (100, 100))
                faces.append(roi)
                labels.append(label_idx)
            label_idx += 1

        if not faces:
            return False
        self._recognizer.train(faces, np.array(labels))
        self._trained = True
        return True

    # ── Detection helper ──────────────────────────────────────────────────────

    def detect_faces(self, gray_frame: np.ndarray):
        """Returns list of (x, y, w, h) bounding boxes."""
        return self._cascade.detectMultiScale(
            gray_frame, scaleFactor=1.2, minNeighbors=5,
            minSize=(80, 80), flags=cv2.CASCADE_SCALE_IMAGE
        )

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict(self, face_roi_gray: np.ndarray) -> tuple[str | None, float]:
        """Returns (member_id, confidence) or (None, 999) if no match / untrained."""
        if not self._trained:
            return None, 999.0
        roi = cv2.resize(face_roi_gray, (100, 100))
        try:
            label, conf = self._recognizer.predict(roi)
            if conf < CONFIDENCE_THRESHOLD:
                return self._label_map.get(label), conf
        except Exception:
            pass
        return None, 999.0

    # ── Sample saving ─────────────────────────────────────────────────────────

    def save_sample(self, member_id: str, face_gray: np.ndarray) -> str:
        """Save one face ROI as a JPEG sample. Returns path."""
        d = FACES_DIR / member_id
        d.mkdir(parents=True, exist_ok=True)
        idx  = len(list(d.glob("*.jpg")))
        path = d / f"{idx:03d}.jpg"
        roi  = cv2.resize(face_gray, (100, 100))
        cv2.imwrite(str(path), roi)
        return str(path)

    def sample_count(self, member_id: str) -> int:
        d = FACES_DIR / member_id
        return len(list(d.glob("*.jpg"))) if d.exists() else 0

    def has_face_data(self, member_id: str) -> bool:
        return self.sample_count(member_id) > 0
