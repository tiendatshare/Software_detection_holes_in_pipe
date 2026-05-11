# Pipe Defect Inspector

A Windows desktop application for automated pipeline inspection — load an inspection video, run a pre-trained YOLOv8 model to detect defects, review results in a two-panel UI, and export reports as CSV or PDF.

> **Vietnamese version:** [README_VN.md](README_VN.md)

---


## Features

- **Automatic defect detection** — YOLOv8 tracking with ByteTrack (custom buffer to survive camera movement)
- **Post-processing deduplication** — merges repeated detections of the same physical defect
- **Two-panel UI** — video player (left) + defect list (right), click any defect to seek the video
- **Bounding box overlay** — red box drawn on the frame at detected positions
- **Export CSV** — 9-column report (ID, timestamp, frame, confidence, bbox)
- **Export PDF** — summary table + per-defect frame image with bounding box
- **3 languages** — Vietnamese / English / Korean (switch without restart)
- **6 themes** — Steel Blue, Slate & Amber, Carbon & Green × Light / Dark
- **Custom model** — browse to select any `.pt` file from the toolbar
- **Confidence slider** — adjust detection threshold (0.10 – 0.99) live
- **Branding slot** — drop your `logo.png` into `assets/brand/` and restart

---

## Requirements

| | |
|---|---|
| OS | Windows 10 / 11 (64-bit) |
| Python | 3.11 or newer |
| GPU | Optional — CPU inference works, GPU (CUDA) is faster |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/tiendatshare/Software_dectiontion_holes_in_pipe.git
cd Software_dectiontion_holes_in_pipe
```

### 2. Add your model (optional) 

Place your trained YOLOv8 model file at:

```
models/best.pt
```

If you don't have a model yet, see [Training your own model](#training-your-own-model).

### 3. Create a virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the app

Double-click `run.bat` if you don't want to open VS Code, or from the terminal:

```bash
venv\Scripts\python main.py
```

---

## How to Use

1. Click **Open Video** in the toolbar and select an inspection video (`.mp4`, `.avi`, `.mov`, `.mkv`)
2. The app processes the video automatically — a progress bar appears at the bottom
3. Detected defects appear in the **Defect List** on the right as they are found
4. Click any row in the defect list → the video jumps to that timestamp and plays
5. Use **Export CSV** or **Export PDF** to save the full report

---

## Project Structure

```
Software_dectiontion_holes_in_pipe/
├── main.py                      ← entry point
├── run.bat                      ← double-click launcher (Windows)
├── requirements.txt
├── config.json                  ← saved settings (theme, language, model path)
├── models/
│   └── best.pt                  ← your YOLOv8 model (not included in repo)
├── assets/
│   ├── brand/
│   │   ├── HOW_TO_USE.md        ← how to add your logo
│   │   └── logo.png             ← place your logo here (optional)
│   ├── i18n/
│   │   ├── vi.json
│   │   ├── en.json
│   │   └── ko.json
│   └── tracker/
│       └── bytetrack.yaml       ← ByteTrack config (track_buffer=90)
├── src/
│   ├── core/
│   │   ├── models.py            ← DefectRecord, VideoMetadata
│   │   ├── video_loader.py      ← VideoLoader (OpenCV)
│   │   ├── detection_engine.py  ← DetectionEngine (YOLOv8 + ByteTrack)
│   │   ├── detection_store.py   ← DetectionStore (deduplication)
│   │   ├── processing_worker.py ← QThread parallel worker
│   │   └── export_manager.py   ← CSV + PDF export
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── video_player_widget.py
│   │   ├── defect_list_widget.py
│   │   └── toolbar_widget.py
│   └── utils/
│       ├── app_config.py
│       ├── language_manager.py
│       ├── branding_loader.py
│       └── theme_manager.py
|
└──docs/superpowers              ← Doc md of project(if you want recover new project. Use AI to read and create code from this doc)
|
└── tests/
    └── core/                    ← pytest unit tests

```

---

## Custom Logo (Branding)

1. Place your logo image in `assets/brand/`
2. Name it `logo.png`, `logo.jpg`, or `logo.svg`
3. Recommended size: **200×60 px**, transparent background (PNG)
4. Restart the app — the logo appears automatically in the toolbar

See `assets/brand/HOW_TO_USE.md` for more details (Vietnamese / English / Korean).

---

## Configuration

All settings are saved to `config.json` automatically when you change them in the UI:

| Key | Default | Description |
|---|---|---|
| `model_path` | `models/best.pt` | Path to the YOLOv8 `.pt` model |
| `confidence_threshold` | `0.7` | Detection confidence (0.1 – 0.99) |
| `theme` | `slate_amber` | `steel_blue` / `slate_amber` / `carbon_green` |
| `theme_mode` | `light` | `light` / `dark` |
| `language` | `vi` | `vi` / `en` / `ko` |

---

## Training Your Own Model

This app works with any YOLOv8 model trained to detect pipeline defects. To train:

1. Collect and label your pipe inspection images (e.g. with [Label Studio](https://labelstud.io/) or [Roboflow](https://roboflow.com/))
2. Train with [Ultralytics YOLOv8](https://docs.ultralytics.com/):
   ```bash
   yolo train model=yolov8n.pt data=your_dataset.yaml epochs=100
   ```
3. Copy `runs/detect/train/weights/best.pt` → `models/best.pt`

---

## Running Tests

```bash
venv\Scripts\activate
pytest tests/ -v
```

Expected: **9 tests passed**

---

## Tech Stack

| | |
|---|---|
| UI | PyQt6 |
| Detection | Ultralytics YOLOv8 + ByteTrack |
| Video | OpenCV |
| Export | ReportLab (PDF), pandas (CSV), Pillow |
| Language | Python 3.11 |

---

## License

This project is provided as-is for internal use. Contact the repository owner for licensing questions.
