from dataclasses import dataclass

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
