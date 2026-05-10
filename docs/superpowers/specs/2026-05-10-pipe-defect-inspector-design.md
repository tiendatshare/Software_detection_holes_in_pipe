# Pipe Defect Inspector — Design Spec
**Date:** 2026-05-10  
**Status:** Approved

---

## 1. Tổng quan

Phần mềm desktop (Windows) giúp kỹ sư phân tích video từ camera đưa vào đường ống truyền nhiệt, tự động phát hiện lỗi/hư hại bằng model YOLOv8 đã train sẵn, hiển thị kết quả theo timeline và xuất báo cáo.

**Phase hiện tại:** Desktop app (Python + PyQt6)  
**Phase sau:** Web app (xem báo cáo + quản lý dự án theo công trình)

---

## 2. Kiến trúc Module

Mỗi module là một class độc lập với interface rõ ràng (input/output). Thay thế hoặc nâng cấp bất kỳ module nào không ảnh hưởng các module khác.

### Modules

| Module | Input | Output | Ghi chú |
|---|---|---|---|
| `VideoLoader` | đường dẫn file video | iterator frames + metadata (fps, total_frames, duration) | dùng OpenCV |
| `DetectionEngine` | frames (batch), model path, confidence threshold | list detections có track_id, confidence, bbox, frame_index | dùng `model.track(batch)` |
| `DetectionStore` | stream detections từ engine | dict {track_id: DefectRecord} | chỉ lưu frame đầu tiên mỗi track_id; `deduplicate()` gộp lỗi trùng sau processing |
| `ExportManager` | DetectionStore, output path, format | file CSV hoặc PDF | dùng pandas + reportlab |
| `AppConfig` | — | model path mặc định, confidence threshold, theme, language | đọc từ `config.json` |
| `LanguageManager` | language code (vi/en/ko) | dict chuỗi UI | đọc từ `assets/i18n/*.json` |
| `BrandingLoader` | — | logo image hoặc None | đọc từ `assets/brand/` |
| `ThemeManager` | theme name, mode (light/dark) | QSS stylesheet string | 6 themes: 3 palettes × 2 modes |

### DefectRecord (data structure)
```python
@dataclass
class DefectRecord:
    track_id: int
    timestamp_sec: float       # thời điểm xuất hiện lần đầu
    timestamp_hms: str         # "00:01:23"
    frame_number: int
    confidence: float
    bbox: tuple[int,int,int,int]  # x, y, w, h
    frame_image: np.ndarray    # crop frame để dùng cho PDF
```

---

## 3. UI Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                          │
│ [LOGO]  [📂 Mở Video] [Model: best.pt ▾] [Conf: ──●── 0.50]   │
│         [🎨 Theme ▾] [🌐 VI|EN|KO]   [⬇ CSV] [⬇ PDF]         │
├────────────────────────────────────┬─────────────────────────────┤
│                                    │  DANH SÁCH LỖI             │
│         VIDEO PLAYER               │ ┌─────────────────────────┐ │
│         (OpenCV frame render       │ │ #1  00:01:23  conf: 87% │ │
│          qua QLabel/QGraphicsView) │ ├─────────────────────────┤ │
│                                    │ │ #2  00:02:45  conf: 92% │ │
│         bounding box đỏ vẽ lên     │ ├─────────────────────────┤ │
│         frame khi video chạy đến   │ │ #3  00:04:10  conf: 78% │ │
│                                    │ └─────────────────────────┘ │
│  [⏮] [▶/⏸] [⏭]  01:23 / 05:00   │  (click → seek video)      │
│  ══════●═══════════════════════   │                             │
└────────────────────────────────────┴─────────────────────────────┤
│ STATUS: Đang xử lý... [████████████░░░░] 245/365 frames (67%)   │
└──────────────────────────────────────────────────────────────────┘
```

**Tương tác:**
- Click lỗi trong danh sách → video seek đến đúng timestamp, auto-play
- Bounding box vẽ lên frame khi video chạy qua vùng có lỗi
- Màu badge confidence: đỏ ≥ 0.8, vàng 0.5–0.8, xanh < 0.5

---

## 4. Theme System

6 themes = 3 palettes × 2 modes (Light / Dark). Chọn trong toolbar, lưu vào `config.json`.

| Palette | Light | Dark | Accent |
|---|---|---|---|
| Steel Blue | nền `#F5F7FA`, sidebar `#FFFFFF` | nền `#0D1B2A`, sidebar `#1A2B3C` | `#1565C0` / `#4FC3F7` |
| Slate & Amber | nền `#F8FAFC`, sidebar `#F1F5F9` | nền `#1E293B`, sidebar `#0F172A` | `#F59E0B` |
| Carbon & Green | nền `#FAFAFA`, sidebar `#F0F0F0` | nền `#161616`, sidebar `#1E1E1E` | `#00C896` |

Implement bằng QSS stylesheet swap — không ảnh hưởng logic.

---

## 5. Branding System

```
assets/
└── brand/
    ├── HOW_TO_USE.md     ← hướng dẫn thay logo
    └── logo.png          ← logo mặc định app
```

`HOW_TO_USE.md` hướng dẫn:
- Đặt file ảnh vào folder `assets/brand/`
- Đặt tên file: `logo.png`, `logo.jpg`, hoặc `logo.svg`
- Kích thước khuyến nghị: 200×60px, nền trong suốt (PNG)
- Khởi động lại app → logo tự cập nhật trên toolbar

`BrandingLoader` kiểm tra folder khi khởi động, load nếu có, hiển thị tên app mặc định nếu không có. Không cần sửa code.

---

## 6. Detection Engine & Tracking

### Luồng xử lý (Parallel)

```
QThread: ProcessingWorker
│
├── Producer Thread
│   └── VideoLoader.read_frames() → frame by frame → Frame Queue
│
└── Consumer Thread
    └── DetectionEngine.track_frame() → DetectionStore.add()
        └── emit signal progress → UI cập nhật progress bar

Sau khi xong → DetectionStore.deduplicate() → refresh DefectListWidget
```

**Nguyên tắc tracking:**
- Dùng `model.track(persist=True, tracker=bytetrack.yaml)` — YOLOv8 + ByteTrack gán `track_id` nhất quán
- `persist=True` giữ tracking state giữa các frame
- `DetectionStore` chỉ lưu lần xuất hiện **đầu tiên** của mỗi `track_id`
- Tracking chạy tuần tự theo thứ tự frame để đảm bảo ID nhất quán
- Parallel là I/O (đọc frame) song song với Inference (xử lý frame trước)

**ByteTrack config (`assets/tracker/bytetrack.yaml`):**

Camera đường ống di chuyển liên tục — cùng 1 lỗi vật lý có thể xuất hiện trên nhiều frame rồi tạm mất rồi xuất hiện lại khi tracker mất dấu. Config mặc định `track_buffer=30` (1 giây ở 30fps) quá ngắn, dẫn đến mỗi lần reacquire là một `track_id` mới → đếm trùng. Giải pháp:

```yaml
tracker_type: bytetrack
track_high_thresh: 0.25   # ngưỡng detection để bắt đầu track
track_low_thresh: 0.1     # ngưỡng thấp để recover track đang mất
new_track_thresh: 0.25    # ngưỡng tạo track mới
track_buffer: 90          # 90 frame ≈ ~3 giây ở 30fps (mặc định 30)
match_thresh: 0.8         # ngưỡng IoU để match track
fuse_score: True          # bắt buộc có trong ultralytics ByteTrack
```

**Deduplication (post-processing):**

ByteTrack tăng buffer giúp giữ track_id, nhưng khi camera di chuyển qua lại hoặc rung nhiều, vẫn có thể assign track_id mới cho cùng 1 lỗi vật lý. Sau khi processing xong, `DetectionStore.deduplicate()` được gọi để gộp các record có:
- `|timestamp_A - timestamp_B| < time_window_sec` (mặc định 5 giây), **VÀ**
- `IoU(bbox_A, bbox_B) >= iou_threshold` (mặc định 0.1 — bounding box chồng lên nhau)

Record xuất hiện sau (frame_number cao hơn) bị xóa. Defect list được refresh sau dedup.

**Model config:**
- Path mặc định: `models/best.pt` (bundle sẵn trong app)
- Người dùng có thể browse chọn file `.pt` khác từ toolbar
- Confidence threshold: mặc định 0.50, có thể chỉnh qua slider (0.1 – 0.99)
- Tất cả detections vượt ngưỡng đều được liệt kê

---

## 7. Export

### CSV
```
defect_id,timestamp_sec,timestamp_hms,frame_number,confidence,x,y,width,height
1,83.4,00:01:23,2502,0.87,120,340,45,38
2,165.2,00:02:45,4956,0.92,230,180,62,51
```

### PDF (reportlab)
- **Trang 1:** Header (logo, tên file video, ngày phân tích, tổng số lỗi phát hiện)
- **Trang 2+:** Mỗi lỗi 1 block — ảnh frame crop có bounding box đỏ + thông tin (ID, timestamp, confidence, frame number)

---

## 8. Đa ngôn ngữ

3 ngôn ngữ: Tiếng Việt (`vi`), English (`en`), 한국어 (`ko`)

```
assets/
└── i18n/
    ├── vi.json
    ├── en.json
    └── ko.json
```

`LanguageManager` load file JSON theo lựa chọn, cung cấp method `t("key")` trả về chuỗi UI. Chuyển ngôn ngữ không cần restart app.

---

## 9. Cấu trúc thư mục dự án

```
pipe-defect-inspector/
├── main.py
├── requirements.txt
├── config.json                  ← theme, language, model path, confidence
├── models/
│   └── best.pt                  ← model mặc định
├── assets/
│   ├── brand/
│   │   ├── HOW_TO_USE.md
│   │   └── logo.png
│   ├── i18n/
│   │   ├── vi.json
│   │   ├── en.json
│   │   └── ko.json
│   └── tracker/
│       └── bytetrack.yaml       ← custom ByteTrack config (track_buffer=90)
├── src/
│   ├── core/
│   │   ├── video_loader.py      ← VideoLoader
│   │   ├── detection_engine.py  ← DetectionEngine
│   │   ├── detection_store.py   ← DetectionStore, DefectRecord
│   │   └── export_manager.py    ← ExportManager
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── video_player_widget.py
│   │   ├── defect_list_widget.py
│   │   └── toolbar_widget.py
│   └── utils/
│       ├── app_config.py        ← AppConfig
│       ├── language_manager.py  ← LanguageManager
│       ├── branding_loader.py   ← BrandingLoader
│       └── theme_manager.py     ← ThemeManager
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-10-pipe-defect-inspector-design.md
```

---

## 10. Tech Stack & Requirements

```
Python >= 3.11
PyQt6 >= 6.6
opencv-python >= 4.9
ultralytics >= 8.0        ← YOLOv8
reportlab >= 4.0          ← PDF export
pandas >= 2.0             ← CSV export
numpy >= 1.26
```

---

## 11. Phase sau (Web)

Thiết kế module hóa cho phép thêm web layer sau mà không sửa core:
- `core/` modules tái sử dụng nguyên vẹn
- Thêm `FastAPI` wrapper lên trên `DetectionEngine` và `ExportManager`
- Web features: xem báo cáo online, quản lý dự án theo công trình, so sánh các lần kiểm tra
