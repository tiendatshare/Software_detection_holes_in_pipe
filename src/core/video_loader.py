import cv2
from pathlib import Path
from src.core.models import VideoMetadata

class VideoLoader:
    def __init__(self, video_path: str):
        self.path = str(video_path)
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.path}")
        self._meta = VideoMetadata(
            fps=cap.get(cv2.CAP_PROP_FPS) or 30.0,
            total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            duration_sec=cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30.0),
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        cap.release()

    def get_metadata(self) -> VideoMetadata:
        return self._meta

    def read_frames(self, batch_size: int = 1):
        """Yields (frame_index, frame_ndarray) when batch_size=1, or list of (frame_index, frame) when batch_size>1."""
        cap = cv2.VideoCapture(self.path)
        idx = 0
        batch = []
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if batch_size == 1:
                    yield idx, frame
                else:
                    batch.append((idx, frame))
                    if len(batch) == batch_size:
                        yield batch
                        batch = []
                idx += 1
            if batch:
                yield batch
        finally:
            cap.release()
