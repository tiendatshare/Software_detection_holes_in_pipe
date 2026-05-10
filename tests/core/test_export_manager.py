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
