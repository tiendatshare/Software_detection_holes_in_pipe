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
    assert result[0] == ((10, 20, 30, 40), 0.9)
