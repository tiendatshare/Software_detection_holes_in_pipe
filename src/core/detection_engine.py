from ultralytics import YOLO
from pathlib import Path
from dataclasses import dataclass
import numpy as np

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

    def track_frame(self, frame: np.ndarray, frame_index: int, confidence: float = 0.5) -> list:
        results = self._model.track(
            frame,
            persist=True,
            conf=confidence,
            verbose=False,
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
