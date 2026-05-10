# Phần Mềm Kiểm Tra Lỗi Đường Ống

Ứng dụng desktop Windows để kiểm tra đường ống tự động — tải video kiểm tra, chạy model YOLOv8 để phát hiện lỗi/hư hại, xem kết quả trên giao diện 2 bảng, và xuất báo cáo CSV hoặc PDF.

> **English version:** [README.md](README.md)

---

## Tính Năng

- **Phát hiện lỗi tự động** — YOLOv8 tracking với ByteTrack (buffer tăng để chịu được camera di chuyển)
- **Gộp lỗi trùng tự động** — loại bỏ các lần phát hiện lại cùng một lỗi vật lý
- **Giao diện 2 bảng** — video player (trái) + danh sách lỗi (phải), click vào lỗi để nhảy đến đúng thời điểm
- **Vẽ bounding box** — hộp đỏ hiển thị trên frame tại vị trí lỗi khi video chạy đến
- **Xuất CSV** — báo cáo 9 cột (ID, thời gian, frame, độ chính xác, tọa độ bbox)
- **Xuất PDF** — bảng tổng hợp + ảnh frame từng lỗi kèm bounding box
- **3 ngôn ngữ** — Tiếng Việt / English / 한국어 (chuyển không cần restart)
- **6 giao diện** — Steel Blue, Slate & Amber, Carbon & Green × Sáng / Tối
- **Chọn model** — browse chọn file `.pt` bất kỳ từ toolbar
- **Thanh trượt confidence** — chỉnh ngưỡng phát hiện (0.10 – 0.99) trực tiếp
- **Chèn logo** — đặt `logo.png` vào `assets/brand/` và restart là xong

---

## Yêu Cầu Hệ Thống

| | |
|---|---|
| Hệ điều hành | Windows 10 / 11 (64-bit) |
| Python | 3.11 trở lên |
| GPU | Không bắt buộc — CPU chạy được, GPU (CUDA) nhanh hơn |

---

## Cài Đặt Nhanh

### 1. Clone repository

```bash
git clone https://github.com/tiendatshare/Software_dectiontion_holes_in_pipe.git
cd Software_dectiontion_holes_in_pipe
```

### 2. Thêm model YOLOv8

Đặt file model đã train vào:

```
models/best.pt
```

Nếu chưa có model, xem phần [Tự train model](#tự-train-model) bên dưới.

### 3. Tạo môi trường ảo và cài thư viện

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Lần đầu cài có thể mất 2–5 phút do tải ultralytics và các thư viện đi kèm.

### 4. Chạy ứng dụng

Double-click `run.bat`, hoặc từ terminal:

```bash
venv\Scripts\python main.py
```

---

## Cách Sử Dụng

1. Click **Mở Video** trên toolbar, chọn file video kiểm tra (`.mp4`, `.avi`, `.mov`, `.mkv`)
2. App tự động xử lý video — thanh tiến trình xuất hiện ở cuối màn hình
3. Lỗi phát hiện được xuất hiện dần trong **Danh Sách Lỗi** bên phải
4. Click vào bất kỳ hàng nào trong danh sách → video nhảy đến đúng timestamp và tự phát
5. Click **Xuất CSV** hoặc **Xuất PDF** để lưu báo cáo

---

## Cấu Trúc Thư Mục

```
Software_dectiontion_holes_in_pipe/
├── main.py                      ← điểm khởi chạy
├── run.bat                      ← double-click để chạy (Windows)
├── requirements.txt
├── config.json                  ← cài đặt đã lưu (theme, ngôn ngữ, model)
├── models/
│   └── best.pt                  ← model YOLOv8 của bạn (không có trong repo)
├── assets/
│   ├── brand/
│   │   ├── HOW_TO_USE.md        ← hướng dẫn thay logo
│   │   └── logo.png             ← đặt logo của bạn tại đây (tùy chọn)
│   ├── i18n/
│   │   ├── vi.json
│   │   ├── en.json
│   │   └── ko.json
│   └── tracker/
│       └── bytetrack.yaml       ← cấu hình ByteTrack (track_buffer=90)
├── src/
│   ├── core/                    ← logic xử lý (độc lập với UI)
│   └── ui/                     ← các widget PyQt6
└── tests/
    └── core/                    ← unit test với pytest
```

---

## Chèn Logo Doanh Nghiệp

1. Đặt file ảnh logo vào thư mục `assets/brand/`
2. Đặt tên file: `logo.png`, `logo.jpg`, hoặc `logo.svg`
3. Kích thước khuyến nghị: **200×60 px**, nền trong suốt (PNG)
4. Restart app → logo tự động hiển thị trên toolbar bên trái

Xem chi tiết trong `assets/brand/HOW_TO_USE.md`.

---

## Cài Đặt (config.json)

Tất cả cài đặt được tự động lưu vào `config.json` khi bạn thay đổi trên UI:

| Khóa | Mặc định | Mô tả |
|---|---|---|
| `model_path` | `models/best.pt` | Đường dẫn đến file model `.pt` |
| `confidence_threshold` | `0.5` | Ngưỡng phát hiện (0.1 – 0.99) |
| `theme` | `slate_amber` | `steel_blue` / `slate_amber` / `carbon_green` |
| `theme_mode` | `light` | `light` / `dark` |
| `language` | `vi` | `vi` / `en` / `ko` |

---

## Tự Train Model

App hoạt động với bất kỳ model YOLOv8 nào được train để phát hiện lỗi đường ống. Để tự train:

1. Thu thập và gán nhãn ảnh đường ống (dùng [Label Studio](https://labelstud.io/) hoặc [Roboflow](https://roboflow.com/))
2. Train với [Ultralytics YOLOv8](https://docs.ultralytics.com/):
   ```bash
   yolo train model=yolov8n.pt data=your_dataset.yaml epochs=100
   ```
3. Copy `runs/detect/train/weights/best.pt` → `models/best.pt`

---

## Chạy Unit Test

```bash
venv\Scripts\activate
pytest tests/ -v
```

Kết quả mong đợi: **9 tests passed**

---

## Tech Stack

| | |
|---|---|
| Giao diện | PyQt6 |
| Phát hiện lỗi | Ultralytics YOLOv8 + ByteTrack |
| Xử lý video | OpenCV |
| Xuất báo cáo | ReportLab (PDF), pandas (CSV), Pillow |
| Ngôn ngữ | Python 3.11 |

---

## Liên Hệ

Mọi câu hỏi hoặc đóng góp vui lòng liên hệ qua GitHub: [@tiendatshare](https://github.com/tiendatshare)
