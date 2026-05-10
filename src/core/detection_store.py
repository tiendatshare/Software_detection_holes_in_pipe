from src.core.models import DefectRecord
from src.core.detection_engine import RawDetection

class DetectionStore:
    def __init__(self, fps: float):
        self._fps = fps
        self._records: dict[int, DefectRecord] = {}
        self._frame_bboxes: dict[int, list[tuple]] = {}

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

    def get_all(self) -> list:
        return sorted(self._records.values(), key=lambda r: r.frame_number)

    def get_latest(self) -> object:
        if not self._records:
            return None
        return max(self._records.values(), key=lambda r: r.frame_number)

    def get_bbox_at_frame(self, frame_index: int) -> list | None:
        return self._frame_bboxes.get(frame_index)

    def clear(self) -> None:
        self._records.clear()
        self._frame_bboxes.clear()
