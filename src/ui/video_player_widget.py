import cv2
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPolygon
from src.core.detection_store import DetectionStore
from src.utils.icon_loader import load_icon


class EmptyStateWidget(QWidget):
    open_video_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(load_icon("video", "#888888", 56).pixmap(56, 56))
        layout.addWidget(icon_lbl)

        self.text_lbl = QLabel("Mở video để bắt đầu phân tích")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_lbl.setStyleSheet("color: #888888; font-size: 14px;")
        layout.addWidget(self.text_lbl)

        self.btn = QPushButton("  Chọn Video")
        self.btn.setIcon(load_icon("folder-open", "#FFFFFF", 16))
        self.btn.setIconSize(QSize(16, 16))
        self.btn.setFixedWidth(140)
        self.btn.clicked.connect(self.open_video_clicked)
        layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignCenter)


class DefectSeekBar(QWidget):
    value_changed = pyqtSignal(int)  # 0-1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._markers: list[tuple[float, str]] = []  # (ratio 0-1, label)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setValue(self, value: int) -> None:
        self._value = max(0, min(1000, value))
        self.update()

    def value(self) -> int:
        return self._value

    def set_markers(self, markers: list[tuple[float, str]]) -> None:
        self._markers = markers
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = 4
        bar_y = h - bar_h - 6

        # Background bar
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#D0D7E3"))
        painter.drawRoundedRect(0, bar_y, w, bar_h, 2, 2)

        # Progress fill
        prog_w = int(self._value / 1000 * w)
        painter.setBrush(QColor("#1565C0"))
        painter.drawRoundedRect(0, bar_y, prog_w, bar_h, 2, 2)

        # Defect markers (triangles + labels)
        for ratio, label in self._markers:
            x = int(ratio * w)
            tri = QPolygon([
                QPoint(x,     bar_y - 2),
                QPoint(x - 5, bar_y - 11),
                QPoint(x + 5, bar_y - 11),
            ])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#E53935"))
            painter.drawPolygon(tri)
            painter.setPen(QColor("#E53935"))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.drawText(x - 12, bar_y - 25, 24, 14,
                             Qt.AlignmentFlag.AlignHCenter, label)

        # Current position dot
        pos_x = int(self._value / 1000 * w)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1565C0"))
        painter.drawEllipse(pos_x - 5, bar_y - 1, 10, bar_h + 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._seek(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._seek(event.position().x())

    def _seek(self, x: float):
        self._value = max(0, min(1000, int(x / max(self.width(), 1) * 1000)))
        self.value_changed.emit(self._value)
        self.update()


class VideoPlayerWidget(QWidget):
    position_changed = pyqtSignal(float)
    open_video_requested = pyqtSignal()

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
        self._markers: list[tuple[float, str]] = []
        self._build_ui()
        self._empty_state.open_video_clicked.connect(self.open_video_requested)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()

        self._empty_state = EmptyStateWidget()
        self._stack.addWidget(self._empty_state)   # page 0

        self.video_label = QLabel()
        self.video_label.setObjectName("video_label")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 360)
        self._stack.addWidget(self.video_label)    # page 1

        layout.addWidget(self._stack, stretch=1)

        controls = QHBoxLayout()
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.clicked.connect(self.toggle_play)

        self.seek_bar = DefectSeekBar()
        self.seek_bar.value_changed.connect(self._on_seek_bar_moved)

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
        self.clear_markers()
        self._show_current_frame()
        self._stack.setCurrentIndex(1)

    def set_store(self, store) -> None:
        self._store = store

    def add_defect_marker(self, timestamp_sec: float, defect_id: int) -> None:
        if self._total_frames <= 0:
            return
        ratio = min((timestamp_sec * self._fps) / self._total_frames, 1.0)
        self._markers.append((ratio, f"#{defect_id}"))
        self.seek_bar.set_markers(self._markers)

    def clear_markers(self) -> None:
        self._markers = []
        self.seek_bar.set_markers([])

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
