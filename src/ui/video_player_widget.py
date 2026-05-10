import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from src.core.detection_store import DetectionStore

class VideoPlayerWidget(QWidget):
    position_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._fps = 30.0
        self._total_frames = 0
        self._current_frame = 0
        self._is_playing = False
        self._store = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video_label = QLabel()
        self.video_label.setObjectName("video_label")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 360)
        layout.addWidget(self.video_label, stretch=1)
        controls = QHBoxLayout()
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.clicked.connect(self.toggle_play)
        self.seek_bar = QSlider(Qt.Orientation.Horizontal)
        self.seek_bar.setRange(0, 1000)
        self.seek_bar.sliderMoved.connect(self._on_seek_bar_moved)
        self.time_label = QLabel("00:00:00 / 00:00:00")
        controls.addWidget(self.btn_play)
        controls.addWidget(self.seek_bar)
        controls.addWidget(self.time_label)
        layout.addLayout(controls)

    def load_video(self, path: str) -> None:
        if self._cap:
            self._cap.release()
        self._cap = cv2.VideoCapture(path)
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._timer.setInterval(int(1000 / self._fps))
        self._current_frame = 0
        self._show_current_frame()

    def set_store(self, store) -> None:
        self._store = store

    def seek_to(self, timestamp_sec: float) -> None:
        if not self._cap:
            return
        frame_num = int(timestamp_sec * self._fps)
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        self._current_frame = frame_num
        self._show_current_frame()
        if not self._is_playing:
            self.toggle_play()

    def toggle_play(self) -> None:
        if not self._cap:
            return
        self._is_playing = not self._is_playing
        self.btn_play.setText("⏸" if self._is_playing else "▶")
        if self._is_playing:
            self._timer.start()
        else:
            self._timer.stop()

    def _next_frame(self) -> None:
        if not self._cap:
            return
        ret, frame = self._cap.read()
        if not ret:
            self._timer.stop()
            self._is_playing = False
            self.btn_play.setText("▶")
            return
        self._display_frame(frame, self._current_frame)
        self._current_frame += 1
        self._update_controls()

    def _show_current_frame(self) -> None:
        if not self._cap:
            return
        pos = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        ret, frame = self._cap.read()
        if ret:
            self._display_frame(frame, pos)
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, pos)

    def _display_frame(self, frame: np.ndarray, frame_index: int) -> None:
        if self._store:
            bboxes = self._store.get_bbox_at_frame(frame_index)
            if bboxes:
                for (x, y, w, h), conf in bboxes:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, f"{conf*100:.0f}%", (x, max(y-6, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qi = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qi).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(pix)
        self.position_changed.emit(self._current_frame / self._fps)

    def _update_controls(self) -> None:
        if self._total_frames > 0:
            self.seek_bar.setValue(int(self._current_frame / self._total_frames * 1000))
        cur = self._fmt_time(self._current_frame / self._fps)
        tot = self._fmt_time(self._total_frames / self._fps)
        self.time_label.setText(f"{cur} / {tot}")

    def _on_seek_bar_moved(self, value: int) -> None:
        if not self._cap:
            return
        target = int(value / 1000 * self._total_frames)
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        self._current_frame = target
        self._show_current_frame()

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        s = int(seconds)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

    def closeEvent(self, event):
        if self._cap:
            self._cap.release()
        super().closeEvent(event)
