# UI Polish — Pipe Defect Inspector Design Spec
**Date:** 2026-05-11  
**Status:** Approved

---

## 1. Mục tiêu

Nâng cấp giao diện từ "basic PyQt6 widgets" lên phong cách app desktop/web hiện đại. **Không thay đổi logic** — chỉ thay đổi UI layer. Tất cả signals/slots, DetectionEngine, DetectionStore, ExportManager giữ nguyên.

---

## 2. Những thay đổi

### 2.1 Icon System — Feather Icons (SVG)

**Nguồn:** Feather Icons v4.29 — MIT License  
**Bundle:** `assets/icons/*.svg` — chỉ copy các icon cần dùng (không bundle toàn bộ thư viện)

| Icon file | Dùng cho |
|---|---|
| `folder-open.svg` | Mở Video |
| `cpu.svg` | Model selector |
| `sliders.svg` | Confidence |
| `droplet.svg` | Theme |
| `sun.svg` / `moon.svg` | Light / Dark toggle |
| `globe.svg` | Language |
| `download.svg` | Export CSV |
| `file-text.svg` | Export PDF |
| `play.svg` / `pause.svg` | Play / Pause |
| `video.svg` | Empty state video player |
| `check-circle.svg` | Status: complete |
| `loader.svg` | Status: processing |
| `alert-circle.svg` | Status: error |

**Cách load:** `QIcon(QPixmap("assets/icons/name.svg"))`, scale về 18×18px. Để icon đổi màu theo theme, tô lại SVG fill bằng `colorize_icon(path, color)` helper.

```python
# src/utils/icon_loader.py
def load_icon(name: str, color: str = "#FFFFFF") -> QIcon:
    """Load SVG icon và tô màu theo theme."""
```

---

### 2.2 Toolbar — Redesign

**Hiện tại:** 1 hàng, text-only buttons, không nhóm rõ.

**Mới:** Vẫn 1 hàng (QToolBar), icon + text, nhóm bằng separator có visual rõ hơn.

```
[LOGO]  |  [📂 Mở Video]  [🤖 best.pt ▾]  |  [🎯 ──●── 0.50]  |  [🎨 Slate ▾] [☀]  [🌐 VI ▾]  |  →→→→  |  [📊 CSV] [📄 PDF]
```

- Mỗi button: `setIcon()` + `setText()` + `setToolButtonStyle(TextBesideIcon)`
- Separator: `addSeparator()` với QSS width tăng lên cho visible hơn
- Confidence label thêm icon trước text

---

### 2.3 Video Panel — Bo góc + Empty State

**Panel wrapper:** Bọc `VideoPlayerWidget` trong `QFrame` có `border-radius: 8px`, `border: 1px solid {border_color}`.

**Empty state** (khi chưa load video — hiện `video_label` đang đen trống):

```
╭─────────────────────────────────╮
│                                 │
│         🎬  (icon lớn 48px)    │
│                                 │
│    Mở video để bắt đầu phân tích│
│    [📂 Chọn Video]              │
│                                 │
╰─────────────────────────────────╯
```

Implement bằng `QStackedWidget` trong `VideoPlayerWidget`:
- Page 0: `EmptyStateWidget` (icon + text + button)
- Page 1: `video_label` (frame hiển thị)
- Switch sang page 1 khi `load_video()` gọi

Button "Chọn Video" trong empty state emit signal `open_video_clicked` → `MainWindow` bắt và mở dialog.

---

### 2.4 Defect List — Card Style

**Hiện tại:** `QTableWidget` với 3 cột.

**Mới:** `QScrollArea` chứa `QVBoxLayout` các `DefectCard(QFrame)`.

```
╭── DefectCard ────────────────────────╮
│ ▌  #1   00:00:03      ● 87%  HIGH   │
╰──────────────────────────────────────╯
```

**DefectCard layout:**
- Border trái 4px màu theo confidence: đỏ ≥0.8, vàng 0.5-0.8, xanh <0.5
- `#ID` — bold, font lớn hơn
- Timestamp — monospace
- Badge confidence: `QLabel` với `border-radius: 10px`, background màu confidence, text "87% HIGH" / "65% MED" / "42% LOW"
- `setCursor(PointingHandCursor)`, `mousePressEvent` → emit `defect_selected(timestamp_sec)`

**Interface giữ nguyên với MainWindow:**
- `add_record(record)` → tạo `DefectCard` và append
- `clear()` → xóa tất cả card
- `retranslate_ui()` → cập nhật title label
- Signal `defect_selected(float)` giữ nguyên

---

### 2.5 Status Bar — Icon + Text

Thay `status_bar.showMessage(text)` bằng custom widget trong status bar:

```python
# Trong MainWindow._update_status(icon_name, text):
self._status_icon.setPixmap(load_icon(icon_name, color).pixmap(16, 16))
self._status_label.setText(text)
```

| Trạng thái | Icon | Màu |
|---|---|---|
| Sẵn sàng | `check-circle` | xanh lá |
| Đang xử lý | `loader` | accent color |
| Hoàn tất | `check-circle` | xanh lá |
| Lỗi | `alert-circle` | đỏ |

---

### 2.6 Theme-aware Icons

Icon màu trắng trên toolbar (nền tối/accent). Icon màu text trên nền sáng.

`icon_loader.py` nhận `color` parameter — MainWindow truyền màu phù hợp khi gọi theme change.

Khi theme đổi: `ToolbarWidget.retranslate_ui()` đã có — mở rộng thành `refresh_icons(accent_color, text_color)`.

---

## 3. Files thay đổi

| File | Thay đổi |
|---|---|
| `src/utils/icon_loader.py` | **Tạo mới** — load + colorize SVG icon |
| `src/ui/toolbar_widget.py` | Thêm icon vào tất cả buttons |
| `src/ui/video_player_widget.py` | Thêm EmptyStateWidget (QStackedWidget) |
| `src/ui/defect_list_widget.py` | Thay QTableWidget bằng DefectCard + QScrollArea |
| `src/ui/main_window.py` | Cập nhật status bar, wire empty state button |
| `assets/icons/*.svg` | **Tạo mới** — 13 SVG files từ Feather Icons |
| `src/utils/theme_manager.py` | Thêm QSS cho DefectCard, EmptyState, panel frame |

---

## 4. Không thay đổi

- Tất cả `src/core/` — logic hoàn toàn không đụng
- `src/utils/app_config.py`, `language_manager.py`, `branding_loader.py`
- Signals/slots interface giữa MainWindow ↔ widgets
- `DefectRecord`, `DetectionStore`, `ProcessingWorker`
- Unit tests — vẫn pass 9/9

---

## 5. Cấu trúc assets/icons/

```
assets/icons/
├── folder-open.svg
├── cpu.svg
├── sliders.svg
├── droplet.svg
├── sun.svg
├── moon.svg
├── globe.svg
├── download.svg
├── file-text.svg
├── play.svg
├── pause.svg
├── video.svg
├── check-circle.svg
├── loader.svg
└── alert-circle.svg
```

Feather Icons SVG format: viewBox="0 0 24 24", stroke-based (không phải fill). Colorize bằng cách thay `stroke` attribute.
