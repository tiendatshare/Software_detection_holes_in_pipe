from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QProgressBar, QStatusBar, QFileDialog, QMessageBox)
from src.ui.video_player_widget import VideoPlayerWidget
from src.ui.defect_list_widget import DefectListWidget
from src.ui.toolbar_widget import ToolbarWidget
from src.core.detection_engine import DetectionEngine
from src.core.detection_store import DetectionStore
from src.core.processing_worker import ProcessingWorker
from src.core.export_manager import ExportManager
from src.core.models import DefectRecord
from src.utils import language_manager as lm
from src.utils import theme_manager
import src.utils.app_config as app_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._store = DetectionStore(fps=30.0)
        self._engine = None
        self._video_path = None
        self._confidence = app_config.get("confidence_threshold")
        self._model_path = app_config.get("model_path")
        self._build_ui()
        self._apply_theme()
        self._load_engine()

    def _build_ui(self):
        self.setWindowTitle(lm.t("app_title"))
        self.setMinimumSize(1280, 720)

        self.toolbar = ToolbarWidget(self)
        self.addToolBar(self.toolbar)
        self.toolbar.open_video_requested.connect(self._on_open_video)
        self.toolbar.model_changed.connect(self._on_model_changed)
        self.toolbar.confidence_changed.connect(self._on_confidence_changed)
        self.toolbar.language_changed.connect(self._on_language_changed)
        self.toolbar.theme_changed.connect(self._on_theme_changed)
        self.toolbar.export_csv_requested.connect(self._on_export_csv)
        self.toolbar.export_pdf_requested.connect(self._on_export_pdf)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 4)

        content_layout = QHBoxLayout()
        self.player = VideoPlayerWidget()
        self.player.set_store(self._store)
        content_layout.addWidget(self.player, stretch=3)

        self.defect_list = DefectListWidget()
        self.defect_list.defect_selected.connect(self.player.seek_to)
        self.defect_list.setMinimumWidth(280)
        self.defect_list.setMaximumWidth(380)
        content_layout.addWidget(self.defect_list, stretch=1)

        main_layout.addLayout(content_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        main_layout.addWidget(self.progress_bar)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(lm.t("status_ready"))

    def _load_engine(self):
        try:
            self._engine = DetectionEngine(self._model_path)
        except FileNotFoundError as e:
            QMessageBox.warning(self, "Model Error", str(e))

    def _apply_theme(self):
        self.setStyleSheet(theme_manager.get_stylesheet(
            app_config.get("theme"), app_config.get("theme_mode")
        ))

    def _on_open_video(self, path: str):
        self._video_path = path
        self.player.load_video(path)
        self.defect_list.clear()
        self._start_processing()

    def _start_processing(self):
        if not self._engine or not self._video_path:
            return
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()

        from src.core.video_loader import VideoLoader
        meta = VideoLoader(self._video_path).get_metadata()
        self._store = DetectionStore(fps=meta.fps)
        self.player.set_store(self._store)

        self._worker = ProcessingWorker(
            self._video_path, self._engine, self._store, self._confidence
        )
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.defect_found.connect(self._on_defect_found)
        self._worker.finished.connect(self._on_processing_done)
        self._worker.error_occurred.connect(self._on_error)

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(lm.t("status_processing"))
        self._worker.start()

    def _on_progress(self, processed: int, total: int):
        if total > 0:
            self.progress_bar.setValue(int(processed / total * 100))

    def _on_defect_found(self, record: DefectRecord):
        self.defect_list.add_record(record)

    def _on_processing_done(self):
        self.progress_bar.setVisible(False)
        count = len(self._store.get_all())
        self.status_bar.showMessage(lm.t("status_complete", count=count))

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", msg)

    def _on_model_changed(self, path: str):
        self._model_path = path
        self._load_engine()

    def _on_confidence_changed(self, value: float):
        self._confidence = value

    def _on_language_changed(self, _code: str):
        self.setWindowTitle(lm.t("app_title"))
        self.toolbar.retranslate_ui()
        self.defect_list.retranslate_ui()
        self.status_bar.showMessage(lm.t("status_ready"))

    def _on_theme_changed(self, theme: str, mode: str):
        self.setStyleSheet(theme_manager.get_stylesheet(theme, mode))

    def _on_export_csv(self):
        if not self._store.get_all():
            QMessageBox.information(self, "", lm.t("no_defects"))
            return
        path, _ = QFileDialog.getSaveFileName(self, lm.t("file_dialog_csv"), "", "CSV Files (*.csv)")
        if path:
            ExportManager.export_csv(self._store, path)

    def _on_export_pdf(self):
        if not self._store.get_all():
            QMessageBox.information(self, "", lm.t("no_defects"))
            return
        path, _ = QFileDialog.getSaveFileName(self, lm.t("file_dialog_pdf"), "", "PDF Files (*.pdf)")
        if path:
            from pathlib import Path
            from src.utils.branding_loader import get_logo_path
            logo = get_logo_path()
            video_name = Path(self._video_path).name if self._video_path else ""
            ExportManager.export_pdf(self._store, path, logo_path=logo, video_filename=video_name)
