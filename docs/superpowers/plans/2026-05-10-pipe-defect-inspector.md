# Pipe Defect Inspector — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop app that loads pipeline inspection videos, runs YOLOv8 defect tracking, displays results in a 2-panel UI (video player left + defect list right), and exports CSV and PDF reports.

**Architecture:** Python + PyQt6 app with independent core modules (VideoLoader, DetectionEngine, DetectionStore, ExportManager) and UI widgets (VideoPlayerWidget, DefectListWidget, ToolbarWidget) wired through Qt signals/slots. Parallel processing uses QThread + threading.Thread producer/consumer via queue.Queue. Each module has a clear input/output interface — replace any module without touching others.

**Tech Stack:** Python 3.11, PyQt6 6.6+, OpenCV 4.9+, Ultralytics 8.0+, ReportLab 4.0+, pandas 2.0+, pytest 7.0+

---

## File Map

```
pipe-defect-inspector/
├── main.py
├── requirements.txt
├── config.json
├── models/best.pt                    ← already exists
├── assets/
│   ├── brand/HOW_TO_USE.md           ← already exists
│   ├── i18n/
│   │   ├── vi.json
│   │   ├── en.json
│   │   └── ko.json
│   └── tracker/
│       └── bytetrack.yaml            ← custom ByteTrack config
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py                 ← DefectRecord, VideoMetadata dataclasses
│   │   ├── video_loader.py           ← VideoLoader
│   │   ├── detection_engine.py       ← DetectionEngine (wraps YOLOv8)
│   │   ├── detection_store.py        ← DetectionStore
│   │   ├── processing_worker.py      ← QThread parallel worker
│   │   └── export_manager.py         ← CSV + PDF export
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── video_player_widget.py
│   │   ├── defect_list_widget.py
│   │   └── toolbar_widget.py
│   └── utils/
│       ├── __init__.py
│       ├── app_config.py
│       ├── language_manager.py
│       ├── branding_loader.py
│       └── theme_manager.py
└── tests/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── test_models.py
    │   ├── test_detection_store.py
    │   └── test_export_manager.py
    └── videos/                       ← already exists (3 test videos)
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `config.json`
- Create: `src/__init__.py`, `src/core/__init__.py`, `src/ui/__init__.py`, `src/utils/__init__.py`
- Create: `tests/__init__.py`, `tests/core/__init__.py`

- [ ] **Step 1: Create virtual environment and install dependencies**

```bash
cd "A:\Work_of_brother\Software_detection_hole_intructions"
python -m venv venv
venv\Scripts\activate
```

- [ ] **Step 2: Create `requirements.txt`**

```
PyQt6>=6.6.0
opencv-python>=4.9.0
ultralytics>=8.0.0
reportlab>=4.0.0
pandas>=2.0.0
numpy>=1.26.0
pytest>=7.0.0
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error. ultralytics will download ~50MB.

- [ ] **Step 4: Create `config.json`**

```json
{
  "model_path": "models/best.pt",
  "confidence_threshold": 0.5,
  "theme": "slate_amber",
  "theme_mode": "light",
  "language": "vi"
}
```

- [ ] **Step 5: Create all `__init__.py` files**

```bash
echo. > src\__init__.py
echo. > src\core\__init__.py
echo. > src\ui\__init__.py
echo. > src\utils\__init__.py
echo. > tests\__init__.py
echo. > tests\core\__init__.py
```

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt config.json src/ tests/
git commit -m "feat: project setup — requirements, config, package structure"
```

---

## Task 2: Core Data Models

**Files:**
- Create: `src/core/models.py`
- Create: `tests/core/test_models.py`

- [ ] **Step 1: Write failing test**

`tests/core/test_models.py`:
```python
from src.core.models import DefectRecord, VideoMetadata

def test_defect_record_creation():
    r = DefectRecord(
        track_id=1,
        timestamp_sec=83.4,
        frame_number=2502,
        confidence=0.87,
        bbox=(120, 340, 45, 38),
        frame_image=None,
    )
    assert r.timestamp_hms == "00:01:23"
    assert r.defect_id == 1

def test_video_metadata():
    m = VideoMetadata(fps=30.0, total_frames=9000, duration_sec=300.0, width=1920, height=1080)
    assert m.total_frames == 9000
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/core/test_models.py -v
```

Expected: `ImportError: cannot import name 'DefectRecord'`

- [ ] **Step 3: Implement `src/core/models.py`**

```python
from dataclasses import dataclass, field
import numpy as np

@dataclass
class DefectRecord:
    track_id: int
    timestamp_sec: float
    frame_number: int
    confidence: float
    bbox: tuple          # (x, y, w, h)
    frame_image: object  # np.ndarray or None

    @property
    def defect_id(self) -> int:
        return self.track_id

    @property
    def timestamp_hms(self) -> str:
        total = int(self.timestamp_sec)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

@dataclass
class VideoMetadata:
    fps: float
    total_frames: int
    duration_sec: float
    width: int
    height: int
```

- [ ] **Step 4: Run to verify pass**

```bash
pytest tests/core/test_models.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/core/models.py tests/core/test_models.py
git commit -m "feat: DefectRecord and VideoMetadata dataclasses"
```

---

## Task 3: AppConfig

**Files:**
- Create: `src/utils/app_config.py`

- [ ] **Step 1: Implement `src/utils/app_config.py`**

```python
import json
from pathlib import Path

_CONFIG_PATH = Path("config.json")
_DEFAULTS = {
    "model_path": "models/best.pt",
    "confidence_threshold": 0.5,
    "theme": "slate_amber",
    "theme_mode": "light",
    "language": "vi",
}

def load() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**_DEFAULTS, **data}
    return dict(_DEFAULTS)

def save(config: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get(key: str):
    return load().get(key, _DEFAULTS.get(key))

def set(key: str, value) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)
```

- [ ] **Step 2: Quick smoke test in Python REPL**

```bash
python -c "from src.utils.app_config import load, get; print(get('language'))"
```

Expected: `vi`

- [ ] **Step 3: Commit**

```bash
git add src/utils/app_config.py
git commit -m "feat: AppConfig read/write config.json"
```

---

## Task 4: LanguageManager + i18n Files

**Files:**
- Create: `assets/i18n/vi.json`, `assets/i18n/en.json`, `assets/i18n/ko.json`
- Create: `src/utils/language_manager.py`

- [ ] **Step 1: Create `assets/i18n/vi.json`**

```json
{
  "app_title": "Kiểm Tra Đường Ống",
  "open_video": "Mở Video",
  "select_model": "Chọn Model",
  "confidence": "Ngưỡng",
  "export_csv": "Xuất CSV",
  "export_pdf": "Xuất PDF",
  "defect_list_title": "Danh Sách Lỗi",
  "no_defects": "Chưa có lỗi phát hiện",
  "defect_id": "#",
  "timestamp_col": "Thời gian",
  "confidence_col": "Độ chính xác",
  "status_ready": "Sẵn sàng",
  "status_processing": "Đang xử lý...",
  "status_complete": "Hoàn tất — {count} lỗi phát hiện",
  "file_dialog_video": "Chọn file video",
  "file_dialog_model": "Chọn file model (.pt)",
  "file_dialog_csv": "Lưu file CSV",
  "file_dialog_pdf": "Lưu file PDF",
  "error_model_not_found": "Không tìm thấy model: {path}",
  "error_video_not_found": "Không mở được video: {path}",
  "theme_light": "Sáng",
  "theme_dark": "Tối",
  "language_label": "Ngôn ngữ"
}
```

- [ ] **Step 2: Create `assets/i18n/en.json`**

```json
{
  "app_title": "Pipe Defect Inspector",
  "open_video": "Open Video",
  "select_model": "Select Model",
  "confidence": "Confidence",
  "export_csv": "Export CSV",
  "export_pdf": "Export PDF",
  "defect_list_title": "Defect List",
  "no_defects": "No defects detected",
  "defect_id": "#",
  "timestamp_col": "Timestamp",
  "confidence_col": "Confidence",
  "status_ready": "Ready",
  "status_processing": "Processing...",
  "status_complete": "Done — {count} defects found",
  "file_dialog_video": "Select video file",
  "file_dialog_model": "Select model file (.pt)",
  "file_dialog_csv": "Save CSV file",
  "file_dialog_pdf": "Save PDF file",
  "error_model_not_found": "Model not found: {path}",
  "error_video_not_found": "Cannot open video: {path}",
  "theme_light": "Light",
  "theme_dark": "Dark",
  "language_label": "Language"
}
```

- [ ] **Step 3: Create `assets/i18n/ko.json`**

```json
{
  "app_title": "파이프 결함 검사기",
  "open_video": "비디오 열기",
  "select_model": "모델 선택",
  "confidence": "신뢰도",
  "export_csv": "CSV 내보내기",
  "export_pdf": "PDF 내보내기",
  "defect_list_title": "결함 목록",
  "no_defects": "감지된 결함 없음",
  "defect_id": "#",
  "timestamp_col": "타임스탬프",
  "confidence_col": "신뢰도",
  "status_ready": "준비",
  "status_processing": "처리 중...",
  "status_complete": "완료 — {count}개 결함 감지",
  "file_dialog_video": "비디오 파일 선택",
  "file_dialog_model": "모델 파일 선택 (.pt)",
  "file_dialog_csv": "CSV 파일 저장",
  "file_dialog_pdf": "PDF 파일 저장",
  "error_model_not_found": "모델을 찾을 수 없음: {path}",
  "error_video_not_found": "비디오를 열 수 없음: {path}",
  "theme_light": "라이트",
  "theme_dark": "다크",
  "language_label": "언어"
}
```

- [ ] **Step 4: Implement `src/utils/language_manager.py`**

```python
import json
from pathlib import Path

_SUPPORTED = ("vi", "en", "ko")
_cache: dict = {}
_current: str = "vi"

def set_language(code: str) -> None:
    global _current, _cache
    if code not in _SUPPORTED:
        code = "vi"
    _current = code
    path = Path("assets/i18n") / f"{code}.json"
    with open(path, "r", encoding="utf-8") as f:
        _cache = json.load(f)

def t(key: str, **kwargs) -> str:
    text = _cache.get(key, key)
    return text.format(**kwargs) if kwargs else text

def current() -> str:
    return _current
```

- [ ] **Step 5: Smoke test**

```bash
python -c "
from src.utils.language_manager import set_language, t
set_language('vi')
print(t('app_title'))
set_language('en')
print(t('status_complete', count=3))
"
```

Expected:
```
Kiểm Tra Đường Ống
Done — 3 defects found
```

- [ ] **Step 6: Commit**

```bash
git add assets/i18n/ src/utils/language_manager.py
git commit -m "feat: LanguageManager with VI/EN/KO i18n"
```

---

## Task 5: BrandingLoader + ThemeManager

**Files:**
- Create: `src/utils/branding_loader.py`
- Create: `src/utils/theme_manager.py`

- [ ] **Step 1: Implement `src/utils/branding_loader.py`**

```python
from pathlib import Path
from PyQt6.QtGui import QPixmap

_BRAND_DIR = Path("assets/brand")
_SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".svg")

def get_logo_path() -> str | None:
    for ext in _SUPPORTED_EXT:
        path = _BRAND_DIR / f"logo{ext}"
        if path.exists():
            return str(path)
    return None

def load_logo() -> QPixmap | None:
    path = get_logo_path()
    if path:
        pix = QPixmap(path)
        if not pix.isNull():
            return pix.scaledToHeight(40)
    return None
```

- [ ] **Step 2: Implement `src/utils/theme_manager.py`**

```python
_THEMES = {
    "steel_blue": {
        "light": {
            "bg": "#F5F7FA", "sidebar": "#FFFFFF", "accent": "#1565C0",
            "text": "#1A1A2E", "border": "#D0D7E3", "row_hover": "#E3ECF7",
            "conf_high": "#FFEBEE", "conf_mid": "#FFF8E1", "conf_low": "#E8F5E9",
        },
        "dark": {
            "bg": "#0D1B2A", "sidebar": "#1A2B3C", "accent": "#4FC3F7",
            "text": "#E8F4FD", "border": "#2A3F52", "row_hover": "#1E3448",
            "conf_high": "#4A1010", "conf_mid": "#4A3A00", "conf_low": "#0A3A1A",
        },
    },
    "slate_amber": {
        "light": {
            "bg": "#F8FAFC", "sidebar": "#F1F5F9", "accent": "#F59E0B",
            "text": "#0F172A", "border": "#E2E8F0", "row_hover": "#FEF3C7",
            "conf_high": "#FFEBEE", "conf_mid": "#FFF8E1", "conf_low": "#E8F5E9",
        },
        "dark": {
            "bg": "#1E293B", "sidebar": "#0F172A", "accent": "#F59E0B",
            "text": "#F1F5F9", "border": "#334155", "row_hover": "#2D3748",
            "conf_high": "#4A1010", "conf_mid": "#4A3A00", "conf_low": "#0A3A1A",
        },
    },
    "carbon_green": {
        "light": {
            "bg": "#FAFAFA", "sidebar": "#F0F0F0", "accent": "#00C896",
            "text": "#1C1C1C", "border": "#E0E0E0", "row_hover": "#E0FAF3",
            "conf_high": "#FFEBEE", "conf_mid": "#FFF8E1", "conf_low": "#E8F5E9",
        },
        "dark": {
            "bg": "#161616", "sidebar": "#1E1E1E", "accent": "#00C896",
            "text": "#E0E0E0", "border": "#2A2A2A", "row_hover": "#0A2A20",
            "conf_high": "#4A1010", "conf_mid": "#4A3A00", "conf_low": "#0A3A1A",
        },
    },
}

def get_stylesheet(theme: str, mode: str) -> str:
    c = _THEMES.get(theme, _THEMES["slate_amber"]).get(mode, _THEMES["slate_amber"]["light"])
    return f"""
        QMainWindow, QWidget {{
            background-color: {c['bg']};
            color: {c['text']};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }}
        QToolBar {{
            background-color: {c['sidebar']};
            border-bottom: 1px solid {c['border']};
            padding: 4px 8px;
            spacing: 8px;
        }}
        QPushButton {{
            background-color: {c['accent']};
            color: {'#FFFFFF' if mode == 'dark' or theme != 'steel_blue' else '#FFFFFF'};
            border: none;
            border-radius: 4px;
            padding: 6px 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {c['accent']}CC;
        }}
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text']}88;
        }}
        QTableWidget {{
            background-color: {c['sidebar']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            gridline-color: {c['border']};
        }}
        QTableWidget::item:hover {{
            background-color: {c['row_hover']};
        }}
        QTableWidget::item:selected {{
            background-color: {c['accent']}44;
        }}
        QHeaderView::section {{
            background-color: {c['bg']};
            color: {c['text']};
            border: none;
            border-bottom: 2px solid {c['accent']};
            padding: 6px;
            font-weight: 600;
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {c['border']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {c['accent']};
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}
        QComboBox {{
            background-color: {c['sidebar']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {c['text']};
        }}
        QProgressBar {{
            background-color: {c['border']};
            border-radius: 4px;
            height: 6px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 4px;
        }}
        QStatusBar {{
            background-color: {c['sidebar']};
            border-top: 1px solid {c['border']};
            color: {c['text']};
        }}
        QLabel#video_label {{
            background-color: #000000;
            border-radius: 4px;
        }}
    """

def available_themes() -> list[str]:
    return list(_THEMES.keys())
```

- [ ] **Step 3: Smoke test stylesheet generation**

```bash
python -c "
from src.utils.theme_manager import get_stylesheet
css = get_stylesheet('slate_amber', 'dark')
print('OK, length:', len(css))
"
```

Expected: `OK, length: <some number>`

- [ ] **Step 4: Commit**

```bash
git add src/utils/branding_loader.py src/utils/theme_manager.py
git commit -m "feat: ThemeManager (6 themes) and BrandingLoader"
```

---

## Task 6: VideoLoader

**Files:**
- Create: `src/core/video_loader.py`

- [ ] **Step 1: Implement `src/core/video_loader.py`**

```python
import cv2
from pathlib import Path
from src.core.models import VideoMetadata

class VideoLoader:
    def __init__(self, video_path: str):
        self.path = str(video_path)
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.path}")
        self._meta = VideoMetadata(
            fps=cap.get(cv2.CAP_PROP_FPS) or 30.0,
            total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            duration_sec=cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30.0),
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        cap.release()

    def get_metadata(self) -> VideoMetadata:
        return self._meta

    def read_frames(self, batch_size: int = 1):
        """Yields (frame_index, frame_ndarray) or batches of them."""
        cap = cv2.VideoCapture(self.path)
        idx = 0
        batch = []
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if batch_size == 1:
                    yield idx, frame
                else:
                    batch.append((idx, frame))
                    if len(batch) == batch_size:
                        yield batch
                        batch = []
                idx += 1
            if batch:
                yield batch
        finally:
            cap.release()
```

- [ ] **Step 2: Smoke test with a real test video**

```bash
python -c "
from src.core.video_loader import VideoLoader
loader = VideoLoader('tests/videos/video-test-01.mp4')
meta = loader.get_metadata()
print(f'FPS: {meta.fps}, Frames: {meta.total_frames}, Duration: {meta.duration_sec:.1f}s')
"
```

Expected: prints video metadata without error.

- [ ] **Step 3: Commit**

```bash
git add src/core/video_loader.py
git commit -m "feat: VideoLoader reads frames and metadata via OpenCV"
```

---

## Task 7: DetectionEngine

**Files:**
- Create: `assets/tracker/bytetrack.yaml`
- Create: `src/core/detection_engine.py`

**Vấn đề cần giải quyết (Fix A):** Camera di chuyển qua đường ống → cùng 1 lỗi vật lý có thể tạm mất khỏi frame rồi xuất hiện lại. ByteTrack default `track_buffer=30` quá ngắn → reacquire = track_id mới → đếm trùng. Tăng lên 90 frame (~3 giây ở 30fps).

- [ ] **Step 1: Tạo `assets/tracker/bytetrack.yaml`**

```yaml
tracker_type: bytetrack
track_high_thresh: 0.25
track_low_thresh: 0.1
new_track_thresh: 0.25
track_buffer: 90
match_thresh: 0.8
fuse_score: True
```

- [ ] **Step 2: Implement `src/core/detection_engine.py`**

```python
from ultralytics import YOLO
from pathlib import Path
from dataclasses import dataclass
import numpy as np

_TRACKER_CONFIG = str(Path(__file__).parent.parent.parent / "assets" / "tracker" / "bytetrack.yaml")

@dataclass
class RawDetection:
    track_id: int
    frame_index: int
    confidence: float
    bbox: tuple   # (x, y, w, h) in pixels

class DetectionEngine:
    def __init__(self, model_path: str):
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        self._model = YOLO(str(path))
        tracker_path = Path(_TRACKER_CONFIG)
        self._tracker = str(tracker_path) if tracker_path.exists() else "bytetrack"

    def track_frame(self, frame: np.ndarray, frame_index: int, confidence: float = 0.5) -> list[RawDetection]:
        results = self._model.track(
            frame,
            persist=True,
            conf=confidence,
            verbose=False,
            tracker=self._tracker,
        )
        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                if box.id is None:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(RawDetection(
                    track_id=int(box.id.item()),
                    frame_index=frame_index,
                    confidence=float(box.conf.item()),
                    bbox=(int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                ))
        return detections

    def reset_tracker(self) -> None:
        self._model.predictor = None
```

- [ ] **Step 3: Smoke test with real model and video frame**

```bash
python -c "
import cv2
from src.core.detection_engine import DetectionEngine
engine = DetectionEngine('models/best.pt')
cap = cv2.VideoCapture('tests/videos/video-test-01.mp4')
ret, frame = cap.read()
cap.release()
dets = engine.track_frame(frame, 0, confidence=0.5)
print(f'Detections on first frame: {len(dets)}')
for d in dets:
    print(f'  track_id={d.track_id} conf={d.confidence:.2f} bbox={d.bbox}')
"
```

Expected: prints detection results (0 or more) without error.

- [ ] **Step 4: Commit**

```bash
git add assets/tracker/bytetrack.yaml src/core/detection_engine.py
git commit -m "feat: DetectionEngine — ByteTrack custom config (track_buffer=90) to reduce duplicate IDs"
```

---

## Task 8: DetectionStore

**Files:**
- Create: `src/core/detection_store.py`
- Create: `tests/core/test_detection_store.py`

- [ ] **Step 1: Write failing test**

`tests/core/test_detection_store.py`:
```python
import numpy as np
from src.core.detection_store import DetectionStore
from src.core.detection_engine import RawDetection

def _make_det(track_id, frame_index, confidence=0.9):
    return RawDetection(
        track_id=track_id,
        frame_index=frame_index,
        confidence=confidence,
        bbox=(10, 20, 30, 40),
    )

def test_first_occurrence_stored():
    store = DetectionStore(fps=30.0)
    det = _make_det(track_id=1, frame_index=90)
    is_new = store.add(det, frame=None)
    assert is_new is True
    records = store.get_all()
    assert len(records) == 1
    assert records[0].track_id == 1
    assert abs(records[0].timestamp_sec - 3.0) < 0.1

def test_duplicate_track_id_ignored():
    store = DetectionStore(fps=30.0)
    store.add(_make_det(1, 90), frame=None)
    is_new = store.add(_make_det(1, 91), frame=None)
    assert is_new is False
    assert len(store.get_all()) == 1

def test_multiple_tracks():
    store = DetectionStore(fps=30.0)
    store.add(_make_det(1, 30), frame=None)
    store.add(_make_det(2, 60), frame=None)
    store.add(_make_det(1, 31), frame=None)
    records = store.get_all()
    assert len(records) == 2

def test_clear():
    store = DetectionStore(fps=30.0)
    store.add(_make_det(1, 30), frame=None)
    store.clear()
    assert len(store.get_all()) == 0

def test_frame_bbox_lookup():
    store = DetectionStore(fps=30.0)
    det = _make_det(1, 90)
    store.add(det, frame=None)
    result = store.get_bbox_at_frame(90)
    assert result is not None
    assert result[0] == (10, 20, 30, 40)

def test_deduplicate_merges_nearby():
    # track_id 1 @ frame 0 (t=0s), track_id 2 @ frame 60 (t=2s) — same bbox → dup
    store = DetectionStore(fps=30.0)
    store.add(RawDetection(1, 0, 0.9, (10, 20, 30, 40)), frame=None)
    store.add(RawDetection(2, 60, 0.85, (12, 22, 28, 38)), frame=None)  # overlapping bbox
    removed = store.deduplicate(time_window_sec=5.0, iou_threshold=0.1)
    assert removed == 1
    assert len(store.get_all()) == 1

def test_deduplicate_keeps_distant():
    # track_id 1 @ frame 0 (t=0s), track_id 2 @ frame 300 (t=10s) — far in time → kept
    store = DetectionStore(fps=30.0)
    store.add(RawDetection(1, 0, 0.9, (10, 20, 30, 40)), frame=None)
    store.add(RawDetection(2, 300, 0.85, (12, 22, 28, 38)), frame=None)
    removed = store.deduplicate(time_window_sec=5.0, iou_threshold=0.1)
    assert removed == 0
    assert len(store.get_all()) == 2
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/core/test_detection_store.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `src/core/detection_store.py`**

**Vấn đề cần giải quyết (Fix B):** Dù ByteTrack buffer tăng, camera rung mạnh hoặc đi qua lỗi 2 lần vẫn có thể sinh track_id mới cho cùng 1 lỗi vật lý. `deduplicate()` gộp các record xuất hiện gần nhau về thời gian VÀ vị trí.

```python
from src.core.models import DefectRecord
from src.core.detection_engine import RawDetection

class DetectionStore:
    def __init__(self, fps: float):
        self._fps = fps
        self._records: dict[int, DefectRecord] = {}       # track_id -> DefectRecord
        self._frame_bboxes: dict[int, list[tuple]] = {}   # frame_index -> [(bbox, conf), ...]

    def add(self, det: RawDetection, frame: object) -> bool:
        """Returns True if this is a new track_id (first occurrence)."""
        bbox_entry = (det.bbox, det.confidence)
        self._frame_bboxes.setdefault(det.frame_index, []).append(bbox_entry)

        if det.track_id in self._records:
            return False

        self._records[det.track_id] = DefectRecord(
            track_id=det.track_id,
            timestamp_sec=det.frame_index / self._fps,
            frame_number=det.frame_index,
            confidence=det.confidence,
            bbox=det.bbox,
            frame_image=frame,
        )
        return True

    def get_all(self) -> list[DefectRecord]:
        return sorted(self._records.values(), key=lambda r: r.frame_number)

    def get_latest(self) -> DefectRecord | None:
        if not self._records:
            return None
        return max(self._records.values(), key=lambda r: r.frame_number)

    def get_bbox_at_frame(self, frame_index: int) -> list[tuple] | None:
        return self._frame_bboxes.get(frame_index)

    def deduplicate(self, time_window_sec: float = 5.0, iou_threshold: float = 0.1) -> int:
        """Merge records close in time AND spatially overlapping. Returns count removed."""
        records = self.get_all()
        removed = 0
        kept_ids: list[int] = []

        for rec in records:
            is_dup = False
            for kept_id in kept_ids:
                kept = self._records[kept_id]
                if abs(rec.timestamp_sec - kept.timestamp_sec) > time_window_sec:
                    continue
                if _iou(rec.bbox, kept.bbox) >= iou_threshold:
                    is_dup = True
                    break
            if is_dup:
                del self._records[rec.track_id]
                removed += 1
            else:
                kept_ids.append(rec.track_id)

        return removed

    def clear(self) -> None:
        self._records.clear()
        self._frame_bboxes.clear()


def _iou(a: tuple, b: tuple) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(ax, bx)
    iy = max(ay, by)
    ix2 = min(ax + aw, bx + bw)
    iy2 = min(ay + ah, by + bh)
    inter = max(0, ix2 - ix) * max(0, iy2 - iy)
    if inter == 0:
        return 0.0
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0
```

- [ ] **Step 4: Run to verify pass**

```bash
pytest tests/core/test_detection_store.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/core/detection_store.py tests/core/test_detection_store.py
git commit -m "feat: DetectionStore deduplicates by track_id, stores first occurrence"
```

---

## Task 9: ProcessingWorker

**Files:**
- Create: `src/core/processing_worker.py`

- [ ] **Step 1: Implement `src/core/processing_worker.py`**

```python
import queue
import threading
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.video_loader import VideoLoader
from src.core.detection_engine import DetectionEngine
from src.core.detection_store import DetectionStore
from src.core.models import DefectRecord

class ProcessingWorker(QThread):
    progress_updated = pyqtSignal(int, int)   # processed_frames, total_frames
    defect_found = pyqtSignal(object)          # DefectRecord
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, video_path: str, engine: DetectionEngine, store: DetectionStore, confidence: float = 0.5):
        super().__init__()
        self.video_path = video_path
        self.engine = engine
        self.store = store
        self._confidence = confidence
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        try:
            loader = VideoLoader(self.video_path)
            meta = loader.get_metadata()
            total = meta.total_frames

            self.engine.reset_tracker()
            self.store.clear()

            frame_queue: queue.Queue = queue.Queue(maxsize=32)

            def producer():
                for frame_index, frame in loader.read_frames(batch_size=1):
                    if self._stop_flag:
                        break
                    frame_queue.put((frame_index, frame))
                frame_queue.put(None)

            producer_thread = threading.Thread(target=producer, daemon=True)
            producer_thread.start()

            processed = 0
            while True:
                item = frame_queue.get()
                if item is None or self._stop_flag:
                    break
                frame_index, frame = item
                detections = self.engine.track_frame(frame, frame_index, self._confidence)
                for det in detections:
                    is_new = self.store.add(det, frame.copy())
                    if is_new:
                        record = self.store.get_latest()
                        if record:
                            self.defect_found.emit(record)
                processed += 1
                self.progress_updated.emit(processed, total)

            producer_thread.join()
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
```

- [ ] **Step 2: Commit**

```bash
git add src/core/processing_worker.py
git commit -m "feat: ProcessingWorker QThread with producer/consumer parallel pipeline"
```

---

## Task 10: ExportManager — CSV + PDF

**Files:**
- Create: `src/core/export_manager.py`
- Create: `tests/core/test_export_manager.py`

- [ ] **Step 1: Write failing tests**

`tests/core/test_export_manager.py`:
```python
import os
import tempfile
import numpy as np
from src.core.export_manager import ExportManager
from src.core.detection_store import DetectionStore
from src.core.detection_engine import RawDetection

def _make_store():
    store = DetectionStore(fps=30.0)
    store.add(RawDetection(1, 90, 0.87, (10, 20, 30, 40)), frame=np.zeros((100,100,3), dtype=np.uint8))
    store.add(RawDetection(2, 180, 0.65, (50, 60, 25, 35)), frame=np.zeros((100,100,3), dtype=np.uint8))
    return store

def test_export_csv_creates_file():
    store = _make_store()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.csv")
        ExportManager.export_csv(store, path)
        assert os.path.exists(path)
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 3  # header + 2 records
        assert "defect_id" in lines[0]
        assert "00:00:03" in lines[1]

def test_export_pdf_creates_file():
    store = _make_store()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.pdf")
        ExportManager.export_pdf(store, path, logo_path=None, video_filename="test.mp4")
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/core/test_export_manager.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `src/core/export_manager.py`**

```python
import csv
import io
from datetime import date
from pathlib import Path
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from src.core.detection_store import DetectionStore
from src.core.models import DefectRecord

class ExportManager:

    @staticmethod
    def export_csv(store: DetectionStore, output_path: str) -> None:
        records = store.get_all()
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "defect_id", "timestamp_sec", "timestamp_hms",
                "frame_number", "confidence", "x", "y", "width", "height"
            ])
            for r in records:
                x, y, w, h = r.bbox
                writer.writerow([
                    r.defect_id, f"{r.timestamp_sec:.2f}", r.timestamp_hms,
                    r.frame_number, f"{r.confidence:.2f}", x, y, w, h
                ])

    @staticmethod
    def export_pdf(
        store: DetectionStore,
        output_path: str,
        logo_path: str | None = None,
        video_filename: str = "",
    ) -> None:
        records = store.get_all()
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Header
        title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold", spaceAfter=6)
        sub_style = ParagraphStyle("sub", fontSize=10, textColor=colors.grey, spaceAfter=20)
        story.append(Paragraph("Pipe Defect Inspection Report", title_style))
        story.append(Paragraph(
            f"Video: {video_filename} &nbsp;|&nbsp; Date: {date.today()} &nbsp;|&nbsp; Total defects: {len(records)}",
            sub_style
        ))

        if logo_path and Path(logo_path).exists():
            story.insert(0, RLImage(logo_path, width=5*cm, height=1.5*cm))
            story.insert(1, Spacer(1, 0.5*cm))

        # Summary table
        summary_data = [["#", "Timestamp", "Frame", "Confidence", "BBox (x,y,w,h)"]]
        for r in records:
            x, y, w, h = r.bbox
            summary_data.append([
                str(r.defect_id), r.timestamp_hms, str(r.frame_number),
                f"{r.confidence*100:.0f}%", f"({x},{y},{w},{h})"
            ])
        tbl = Table(summary_data, colWidths=[1.5*cm, 3*cm, 2.5*cm, 3*cm, 5*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 1*cm))

        # Per-defect detail blocks
        for r in records:
            story.append(Paragraph(f"Defect #{r.defect_id}", ParagraphStyle(
                "defect_title", fontSize=13, fontName="Helvetica-Bold", spaceAfter=4
            )))
            info_data = [
                ["Timestamp", r.timestamp_hms],
                ["Frame", str(r.frame_number)],
                ["Confidence", f"{r.confidence*100:.0f}%"],
                ["BBox (x,y,w,h)", str(r.bbox)],
            ]
            if r.frame_image is not None:
                try:
                    import cv2
                    frame = r.frame_image.copy()
                    x, y, w, h = r.bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    buf = io.BytesIO()
                    from PIL import Image as PILImage
                    PILImage.fromarray(frame_rgb).save(buf, format="PNG")
                    buf.seek(0)
                    img = RLImage(buf, width=8*cm, height=5*cm)
                    story.append(img)
                except Exception:
                    pass
            info_tbl = Table(info_data, colWidths=[4*cm, 10*cm])
            info_tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(info_tbl)
            story.append(Spacer(1, 0.8*cm))

        doc.build(story)
```

Note: PDF with frame images requires `Pillow`. Add to requirements.txt:
```
Pillow>=10.0.0
```

Install: `pip install Pillow`

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/core/test_export_manager.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/core/export_manager.py tests/core/test_export_manager.py requirements.txt
git commit -m "feat: ExportManager — CSV and PDF with frame images"
```

---

## Task 11: VideoPlayerWidget

**Files:**
- Create: `src/ui/video_player_widget.py`

- [ ] **Step 1: Implement `src/ui/video_player_widget.py`**

```python
import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from src.core.detection_store import DetectionStore

class VideoPlayerWidget(QWidget):
    position_changed = pyqtSignal(float)  # current timestamp in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._fps = 30.0
        self._total_frames = 0
        self._current_frame = 0
        self._is_playing = False
        self._store: DetectionStore | None = None
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

    def set_store(self, store: DetectionStore) -> None:
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
                    cv2.putText(frame, f"{conf*100:.0f}%", (x, y-6),
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
            pos = int(self._current_frame / self._total_frames * 1000)
            self.seek_bar.setValue(pos)
        cur = self._fmt_time(self._current_frame / self._fps)
        tot = self._fmt_time(self._total_frames / self._fps)
        self.time_label.setText(f"{cur} / {tot}")

    def _on_seek_bar_moved(self, value: int) -> None:
        if not self._cap:
            return
        target_frame = int(value / 1000 * self._total_frames)
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self._current_frame = target_frame
        self._show_current_frame()

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        s = int(seconds)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

    def closeEvent(self, event):
        if self._cap:
            self._cap.release()
        super().closeEvent(event)
```

- [ ] **Step 2: Commit**

```bash
git add src/ui/video_player_widget.py
git commit -m "feat: VideoPlayerWidget — OpenCV frame render with bbox overlay"
```

---

## Task 12: DefectListWidget

**Files:**
- Create: `src/ui/defect_list_widget.py`

- [ ] **Step 1: Implement `src/ui/defect_list_widget.py`**

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from src.core.models import DefectRecord
from src.utils.language_manager import t

class DefectListWidget(QWidget):
    defect_selected = pyqtSignal(float)  # timestamp_sec

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list[DefectRecord] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(self.title_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._on_row_clicked)
        layout.addWidget(self.table)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.title_label.setText(t("defect_list_title"))
        self.table.setHorizontalHeaderLabels([
            t("defect_id"), t("timestamp_col"), t("confidence_col")
        ])

    def add_record(self, record: DefectRecord) -> None:
        self._records.append(record)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._fill_row(row, record)

    def clear(self) -> None:
        self._records.clear()
        self.table.setRowCount(0)

    def _fill_row(self, row: int, record: DefectRecord) -> None:
        conf = record.confidence
        if conf >= 0.8:
            bg = QColor("#FFCDD2")
        elif conf >= 0.5:
            bg = QColor("#FFF9C4")
        else:
            bg = QColor("#C8E6C9")

        items = [
            QTableWidgetItem(f"#{record.defect_id}"),
            QTableWidgetItem(record.timestamp_hms),
            QTableWidgetItem(f"{conf*100:.0f}%"),
        ]
        for col, item in enumerate(items):
            item.setBackground(bg)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

    def _on_row_clicked(self, row: int, _col: int) -> None:
        if 0 <= row < len(self._records):
            self.defect_selected.emit(self._records[row].timestamp_sec)
```

- [ ] **Step 2: Commit**

```bash
git add src/ui/defect_list_widget.py
git commit -m "feat: DefectListWidget — color-coded table with click-to-seek"
```

---

## Task 13: ToolbarWidget

**Files:**
- Create: `src/ui/toolbar_widget.py`

- [ ] **Step 1: Implement `src/ui/toolbar_widget.py`**

```python
from pathlib import Path
from PyQt6.QtWidgets import (QToolBar, QLabel, QPushButton, QSlider, QComboBox,
                              QFileDialog, QWidget, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from src.utils.language_manager import t, set_language, current as current_lang
from src.utils.branding_loader import load_logo
from src.utils.theme_manager import available_themes
import src.utils.app_config as app_config

class ToolbarWidget(QToolBar):
    open_video_requested = pyqtSignal(str)         # video path
    model_changed = pyqtSignal(str)                # model path
    confidence_changed = pyqtSignal(float)         # 0.0–1.0
    language_changed = pyqtSignal(str)             # language code
    theme_changed = pyqtSignal(str, str)           # theme name, mode
    export_csv_requested = pyqtSignal()
    export_pdf_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self._current_model = app_config.get("model_path")
        self._build_ui()

    def _build_ui(self):
        # Logo
        logo = load_logo()
        if logo:
            lbl = QLabel()
            lbl.setPixmap(logo)
            self.addWidget(lbl)
            self.addSeparator()

        # Open video
        self.btn_open = QPushButton()
        self.btn_open.clicked.connect(self._on_open_video)
        self.addWidget(self.btn_open)

        self.addSeparator()

        # Model selector
        self.btn_model = QPushButton()
        self.btn_model.setMaximumWidth(180)
        self.btn_model.clicked.connect(self._on_select_model)
        self.addWidget(self.btn_model)
        self._update_model_button_text()

        self.addSeparator()

        # Confidence slider
        self.conf_label = QLabel()
        self.addWidget(self.conf_label)
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(10, 99)
        self.conf_slider.setValue(int(app_config.get("confidence_threshold") * 100))
        self.conf_slider.setFixedWidth(100)
        self.conf_slider.valueChanged.connect(self._on_confidence_changed)
        self.addWidget(self.conf_slider)
        self.conf_value_label = QLabel(f"{self.conf_slider.value()/100:.2f}")
        self.conf_value_label.setFixedWidth(32)
        self.addWidget(self.conf_value_label)

        self.addSeparator()

        # Theme selector
        self.theme_combo = QComboBox()
        theme_labels = {
            "steel_blue": "Steel Blue", "slate_amber": "Slate & Amber", "carbon_green": "Carbon & Green"
        }
        for key in available_themes():
            self.theme_combo.addItem(theme_labels.get(key, key), key)
        saved_theme = app_config.get("theme")
        idx = self.theme_combo.findData(saved_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.addWidget(self.theme_combo)

        # Dark/Light toggle
        self.btn_mode = QPushButton()
        self.btn_mode.setFixedWidth(60)
        self._mode = app_config.get("theme_mode")
        self._update_mode_button()
        self.btn_mode.clicked.connect(self._on_mode_toggle)
        self.addWidget(self.btn_mode)

        self.addSeparator()

        # Language selector
        self.lang_combo = QComboBox()
        for code, label in [("vi", "VI"), ("en", "EN"), ("ko", "KO")]:
            self.lang_combo.addItem(label, code)
        idx = self.lang_combo.findData(current_lang())
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self.addWidget(self.lang_combo)

        self.addSeparator()

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        # Export buttons
        self.btn_csv = QPushButton()
        self.btn_csv.clicked.connect(self.export_csv_requested.emit)
        self.addWidget(self.btn_csv)

        self.btn_pdf = QPushButton()
        self.btn_pdf.clicked.connect(self.export_pdf_requested.emit)
        self.addWidget(self.btn_pdf)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_open.setText(t("open_video"))
        self.btn_model.setToolTip(t("select_model"))
        self.conf_label.setText(t("confidence") + ":")
        self.btn_csv.setText(t("export_csv"))
        self.btn_pdf.setText(t("export_pdf"))

    def _update_model_button_text(self):
        name = Path(self._current_model).name
        self.btn_model.setText(f"Model: {name}")

    def _update_mode_button(self):
        self.btn_mode.setText(t("theme_light") if self._mode == "dark" else t("theme_dark"))

    def _on_open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("file_dialog_video"), "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if path:
            self.open_video_requested.emit(path)

    def _on_select_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("file_dialog_model"), "", "Model Files (*.pt)"
        )
        if path:
            self._current_model = path
            self._update_model_button_text()
            app_config.set("model_path", path)
            self.model_changed.emit(path)

    def _on_confidence_changed(self, value: int):
        conf = value / 100
        self.conf_value_label.setText(f"{conf:.2f}")
        app_config.set("confidence_threshold", conf)
        self.confidence_changed.emit(conf)

    def _on_language_changed(self, _idx: int):
        code = self.lang_combo.currentData()
        set_language(code)
        app_config.set("language", code)
        self.language_changed.emit(code)

    def _on_theme_changed(self, _idx: int):
        theme = self.theme_combo.currentData()
        app_config.set("theme", theme)
        self.theme_changed.emit(theme, self._mode)

    def _on_mode_toggle(self):
        self._mode = "dark" if self._mode == "light" else "light"
        self._update_mode_button()
        app_config.set("theme_mode", self._mode)
        self.theme_changed.emit(self.theme_combo.currentData(), self._mode)
```

- [ ] **Step 2: Commit**

```bash
git add src/ui/toolbar_widget.py
git commit -m "feat: ToolbarWidget — video, model, confidence, theme, language, export"
```

---

## Task 14: MainWindow + main.py

**Files:**
- Create: `src/ui/main_window.py`
- Create: `main.py`

- [ ] **Step 1: Implement `src/ui/main_window.py`**

```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QProgressBar, QStatusBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from src.ui.video_player_widget import VideoPlayerWidget
from src.ui.defect_list_widget import DefectListWidget
from src.ui.toolbar_widget import ToolbarWidget
from src.core.detection_engine import DetectionEngine
from src.core.detection_store import DetectionStore
from src.core.processing_worker import ProcessingWorker
from src.core.export_manager import ExportManager
from src.core.models import DefectRecord
from src.utils import language_manager as lm
from src.utils import theme_manager
import src.utils.app_config as app_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._worker: ProcessingWorker | None = None
        self._store = DetectionStore(fps=30.0)
        self._engine: DetectionEngine | None = None
        self._video_path: str | None = None
        self._confidence = app_config.get("confidence_threshold")
        self._model_path = app_config.get("model_path")
        self._build_ui()
        self._apply_theme()
        self._load_engine()

    def _build_ui(self):
        self.setWindowTitle(lm.t("app_title"))
        self.setMinimumSize(1280, 720)

        # Toolbar
        self.toolbar = ToolbarWidget(self)
        self.addToolBar(self.toolbar)
        self.toolbar.open_video_requested.connect(self._on_open_video)
        self.toolbar.model_changed.connect(self._on_model_changed)
        self.toolbar.confidence_changed.connect(self._on_confidence_changed)
        self.toolbar.language_changed.connect(self._on_language_changed)
        self.toolbar.theme_changed.connect(self._on_theme_changed)
        self.toolbar.export_csv_requested.connect(self._on_export_csv)
        self.toolbar.export_pdf_requested.connect(self._on_export_pdf)

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 4)

        content_layout = QHBoxLayout()
        self.player = VideoPlayerWidget()
        self.player.set_store(self._store)
        content_layout.addWidget(self.player, stretch=3)

        self.defect_list = DefectListWidget()
        self.defect_list.defect_selected.connect(self.player.seek_to)
        self.defect_list.setMinimumWidth(280)
        self.defect_list.setMaximumWidth(380)
        content_layout.addWidget(self.defect_list, stretch=1)

        main_layout.addLayout(content_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(lm.t("status_ready"))

    def _load_engine(self):
        try:
            self._engine = DetectionEngine(self._model_path)
        except FileNotFoundError as e:
            QMessageBox.warning(self, "Model Error", str(e))

    def _apply_theme(self):
        theme = app_config.get("theme")
        mode = app_config.get("theme_mode")
        self.setStyleSheet(theme_manager.get_stylesheet(theme, mode))

    def _on_open_video(self, path: str):
        self._video_path = path
        self.player.load_video(path)
        self.defect_list.clear()
        self._store.clear()
        self._start_processing()

    def _start_processing(self):
        if not self._engine or not self._video_path:
            return
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()

        from src.core.video_loader import VideoLoader
        meta = VideoLoader(self._video_path).get_metadata()
        self._store = DetectionStore(fps=meta.fps)
        self.player.set_store(self._store)

        self._worker = ProcessingWorker(self._video_path, self._engine, self._store, self._confidence)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.defect_found.connect(self._on_defect_found)
        self._worker.finished.connect(self._on_processing_done)
        self._worker.error_occurred.connect(self._on_error)

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(lm.t("status_processing"))
        self._worker.start()

    def _on_progress(self, processed: int, total: int):
        if total > 0:
            self.progress_bar.setValue(int(processed / total * 100))

    def _on_defect_found(self, record: DefectRecord):
        self.defect_list.add_record(record)

    def _on_processing_done(self):
        self.progress_bar.setVisible(False)
        self._store.deduplicate(time_window_sec=5.0, iou_threshold=0.1)
        self.defect_list.clear()
        for record in self._store.get_all():
            self.defect_list.add_record(record)
        count = len(self._store.get_all())
        self.status_bar.showMessage(lm.t("status_complete", count=count))

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", msg)

    def _on_model_changed(self, path: str):
        self._model_path = path
        self._load_engine()

    def _on_confidence_changed(self, value: float):
        self._confidence = value

    def _on_language_changed(self, _code: str):
        self.setWindowTitle(lm.t("app_title"))
        self.toolbar.retranslate_ui()
        self.defect_list.retranslate_ui()
        self.status_bar.showMessage(lm.t("status_ready"))

    def _on_theme_changed(self, theme: str, mode: str):
        self.setStyleSheet(theme_manager.get_stylesheet(theme, mode))

    def _on_export_csv(self):
        if not self._store.get_all():
            QMessageBox.information(self, "", lm.t("no_defects"))
            return
        path, _ = QFileDialog.getSaveFileName(self, lm.t("file_dialog_csv"), "", "CSV Files (*.csv)")
        if path:
            ExportManager.export_csv(self._store, path)

    def _on_export_pdf(self):
        if not self._store.get_all():
            QMessageBox.information(self, "", lm.t("no_defects"))
            return
        path, _ = QFileDialog.getSaveFileName(self, lm.t("file_dialog_pdf"), "", "PDF Files (*.pdf)")
        if path:
            from pathlib import Path
            from src.utils.branding_loader import get_logo_path
            logo = get_logo_path()
            video_name = Path(self._video_path).name if self._video_path else ""
            ExportManager.export_pdf(self._store, path, logo_path=logo, video_filename=video_name)
```

- [ ] **Step 2: Implement `main.py`**

```python
import sys
from PyQt6.QtWidgets import QApplication
from src.utils import language_manager as lm
import src.utils.app_config as app_config

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pipe Defect Inspector")

    lang = app_config.get("language")
    lm.set_language(lang)

    from src.ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the app**

```bash
python main.py
```

Expected: App opens, toolbar visible, no errors in console.

- [ ] **Step 4: Commit**

```bash
git add src/ui/main_window.py main.py
git commit -m "feat: MainWindow wires all widgets — complete app skeleton"
```

---

## Task 15: Integration Test với Video Thực

- [ ] **Step 1: Load video-test-01.mp4**

Mở app: `python main.py`
Click "Mở Video" → chọn `tests/videos/video-test-01.mp4`

Expected:
- Progress bar xuất hiện và tăng dần
- Defect list bên phải bắt đầu populate khi tìm thấy lỗi
- Progress bar ẩn khi xong, status bar hiển thị số lỗi

- [ ] **Step 2: Test click-to-seek**

Click vào một row trong defect list.
Expected: Video bên trái tự động nhảy đến timestamp đó và play.

- [ ] **Step 3: Test bounding box overlay**

Để video chạy qua một frame có lỗi.
Expected: Hộp đỏ vẽ quanh vùng lỗi trên video.

- [ ] **Step 4: Test Export CSV**

Click "Xuất CSV" → chọn đường dẫn lưu.
Expected: File CSV tạo ra, mở bằng Excel kiểm tra có đủ cột.

- [ ] **Step 5: Test Export PDF**

Click "Xuất PDF" → chọn đường dẫn lưu.
Expected: File PDF tạo ra, mở ra thấy summary table + ảnh từng lỗi.

- [ ] **Step 6: Test theme switching**

Chuyển giữa 3 palettes và Light/Dark.
Expected: UI đổi màu ngay không cần restart.

- [ ] **Step 7: Test language switching**

Chuyển VI → EN → KO.
Expected: Tất cả text UI đổi ngôn ngữ.

- [ ] **Step 8: Test logo branding**

Đặt một file ảnh tên `logo.png` vào `assets/brand/`. Restart app.
Expected: Logo hiển thị trên toolbar bên trái.

- [ ] **Step 9: Test với video-test-02 và video-test-03**

Lặp lại Step 1-5 với 2 video còn lại.

- [ ] **Step 10: Final commit**

```bash
git add .
git commit -m "test: integration test complete — all features verified"
```
