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

    def deduplicate(self, time_window_sec: float = 5.0, iou_threshold: float = 0.1) -> int:
        """Merge records that are close in time AND spatially overlapping.
        Returns number of duplicates removed."""
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
