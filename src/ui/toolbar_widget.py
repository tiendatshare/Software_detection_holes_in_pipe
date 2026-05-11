from pathlib import Path
from PyQt6.QtWidgets import (QToolBar, QLabel, QPushButton, QSlider, QComboBox,
                              QFileDialog, QWidget, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from src.utils.language_manager import t, set_language, current as current_lang
from src.utils.branding_loader import load_logo
from src.utils.theme_manager import available_themes
from src.utils.icon_loader import load_icon
import src.utils.app_config as app_config


class ToolbarWidget(QToolBar):
    open_video_requested = pyqtSignal(str)
    model_changed = pyqtSignal(str)
    confidence_changed = pyqtSignal(float)
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str, str)
    export_csv_requested = pyqtSignal()
    export_pdf_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self._current_model = app_config.get("model_path")
        self._mode = app_config.get("theme_mode")
        self._icon_sun = load_icon("sun", "#FFFFFF")
        self._icon_moon = load_icon("moon", "#FFFFFF")
        self._build_ui()

    def _build_ui(self):
        logo = load_logo()
        if logo:
            lbl = QLabel()
            lbl.setPixmap(logo)
            self.addWidget(lbl)
            self.addSeparator()

        self.btn_open = QPushButton()
        self.btn_open.setIcon(load_icon("folder-open", "#FFFFFF"))
        self.btn_open.setIconSize(QSize(16, 16))
        self.btn_open.clicked.connect(self._on_open_video)
        self.addWidget(self.btn_open)
        self.addSeparator()

        self.btn_model = QPushButton()
        self.btn_model.setIcon(load_icon("cpu", "#FFFFFF"))
        self.btn_model.setIconSize(QSize(16, 16))
        self.btn_model.setMaximumWidth(180)
        self.btn_model.clicked.connect(self._on_select_model)
        self.addWidget(self.btn_model)
        self._update_model_button_text()
        self.addSeparator()

        conf_icon = QLabel()
        conf_icon.setPixmap(load_icon("sliders", "#888888", 14).pixmap(14, 14))
        self.addWidget(conf_icon)
        self.conf_label = QLabel()
        self.addWidget(self.conf_label)
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(10, 99)
        self.conf_slider.setValue(int(app_config.get("confidence_threshold") * 100))
        self.conf_slider.setFixedWidth(100)
        self.conf_slider.valueChanged.connect(self._on_confidence_changed)
        self.addWidget(self.conf_slider)
        self.conf_value_label = QLabel(f"{self.conf_slider.value()/100:.2f}")
        self.conf_value_label.setFixedWidth(32)
        self.addWidget(self.conf_value_label)
        self.addSeparator()

        theme_icon = QLabel()
        theme_icon.setPixmap(load_icon("droplet", "#888888", 14).pixmap(14, 14))
        self.addWidget(theme_icon)
        self.theme_combo = QComboBox()
        theme_labels = {"steel_blue": "Steel Blue", "slate_amber": "Slate & Amber", "carbon_green": "Carbon & Green"}
        for key in available_themes():
            self.theme_combo.addItem(theme_labels.get(key, key), key)
        idx = self.theme_combo.findData(app_config.get("theme"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.addWidget(self.theme_combo)

        self.btn_mode = QPushButton()
        self.btn_mode.setFixedWidth(80)
        self.btn_mode.setIconSize(QSize(16, 16))
        self._update_mode_button()
        self.btn_mode.clicked.connect(self._on_mode_toggle)
        self.addWidget(self.btn_mode)
        self.addSeparator()

        globe_lbl = QLabel()
        globe_lbl.setPixmap(load_icon("globe", "#888888", 14).pixmap(14, 14))
        self.addWidget(globe_lbl)
        self.lang_combo = QComboBox()
        for code, label in [("vi", "VI"), ("en", "EN"), ("ko", "KO")]:
            self.lang_combo.addItem(label, code)
        idx = self.lang_combo.findData(current_lang())
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self.addWidget(self.lang_combo)
        self.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self.btn_csv = QPushButton()
        self.btn_csv.setIcon(load_icon("download", "#FFFFFF"))
        self.btn_csv.setIconSize(QSize(16, 16))
        self.btn_csv.clicked.connect(self.export_csv_requested.emit)
        self.addWidget(self.btn_csv)

        self.btn_pdf = QPushButton()
        self.btn_pdf.setIcon(load_icon("file-text", "#FFFFFF"))
        self.btn_pdf.setIconSize(QSize(16, 16))
        self.btn_pdf.clicked.connect(self.export_pdf_requested.emit)
        self.addWidget(self.btn_pdf)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_open.setText(t("open_video"))
        self.btn_model.setToolTip(t("select_model"))
        self.conf_label.setText(t("confidence") + ":")
        self.btn_csv.setText(t("export_csv"))
        self.btn_pdf.setText(t("export_pdf"))
        self._update_mode_button()

    def _update_model_button_text(self):
        self.btn_model.setText(f"Model: {Path(self._current_model).name}")

    def _update_mode_button(self):
        if self._mode == "dark":
            self.btn_mode.setIcon(self._icon_sun)
            self.btn_mode.setText(t("theme_light"))
        else:
            self.btn_mode.setIcon(self._icon_moon)
            self.btn_mode.setText(t("theme_dark"))

    def _on_open_video(self):
        path, _ = QFileDialog.getOpenFileName(self, t("file_dialog_video"), "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if path:
            self.open_video_requested.emit(path)

    def _on_select_model(self):
        path, _ = QFileDialog.getOpenFileName(self, t("file_dialog_model"), "", "Model Files (*.pt)")
        if path:
            self._current_model = path
            self._update_model_button_text()
            app_config.set("model_path", path)
            self.model_changed.emit(path)

    def _on_confidence_changed(self, value: int):
        conf = value / 100
        self.conf_value_label.setText(f"{conf:.2f}")
        app_config.set("confidence_threshold", conf)
        self.confidence_changed.emit(conf)

    def _on_language_changed(self, _idx: int):
        code = self.lang_combo.currentData()
        set_language(code)
        app_config.set("language", code)
        self.language_changed.emit(code)

    def _on_theme_changed(self, _idx: int):
        theme = self.theme_combo.currentData()
        app_config.set("theme", theme)
        self.theme_changed.emit(theme, self._mode)

    def _on_mode_toggle(self):
        self._mode = "dark" if self._mode == "light" else "light"
        self._update_mode_button()
        app_config.set("theme_mode", self._mode)
        self.theme_changed.emit(self.theme_combo.currentData(), self._mode)
