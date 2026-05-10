import queue
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.video_loader import VideoLoader
from src.core.detection_engine import DetectionEngine
from src.core.detection_store import DetectionStore

class ProcessingWorker(QThread):
    progress_updated = pyqtSignal(int, int)   # processed_frames, total_frames
    defect_found = pyqtSignal(object)          # DefectRecord
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, video_path: str, engine: DetectionEngine, store: DetectionStore, confidence: float = 0.5):
        super().__init__()
        self.video_path = video_path
        self.engine = engine
        self.store = store
        self._confidence = confidence
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        try:
            loader = VideoLoader(self.video_path)
            meta = loader.get_metadata()
            total = meta.total_frames

            self.engine.reset_tracker()
            self.store.clear()

            frame_queue: queue.Queue = queue.Queue(maxsize=32)

            def producer():
                for frame_index, frame in loader.read_frames(batch_size=1):
                    if self._stop_flag:
                        break
                    frame_queue.put((frame_index, frame))
                frame_queue.put(None)

            producer_thread = threading.Thread(target=producer, daemon=True)
            producer_thread.start()

            processed = 0
            while True:
                item = frame_queue.get()
                if item is None or self._stop_flag:
                    break
                frame_index, frame = item
                detections = self.engine.track_frame(frame, frame_index, self._confidence)
                for det in detections:
                    is_new = self.store.add(det, frame.copy())
                    if is_new:
                        record = self.store.get_latest()
                        if record:
                            self.defect_found.emit(record)
                processed += 1
                self.progress_updated.emit(processed, total)

            producer_thread.join()
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
