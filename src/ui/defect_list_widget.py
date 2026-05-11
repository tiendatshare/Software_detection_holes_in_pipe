from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from src.core.models import DefectRecord
from src.utils.language_manager import t


class DefectCard(QFrame):
    clicked = pyqtSignal(float)  # timestamp_sec

    def __init__(self, record: DefectRecord, parent=None):
        super().__init__(parent)
        self._timestamp = record.timestamp_sec
        conf = record.confidence

        if conf >= 0.8:
            self.setObjectName("DefectCardHigh")
            badge_bg, badge_fg = "#FFCDD2", "#B71C1C"
        elif conf >= 0.5:
            self.setObjectName("DefectCardMid")
            badge_bg, badge_fg = "#FFF9C4", "#7B5E00"
        else:
            self.setObjectName("DefectCardLow")
            badge_bg, badge_fg = "#C8E6C9", "#1B5E20"

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        id_label = QLabel(f"#{record.defect_id}")
        id_label.setStyleSheet("font-weight: 700; font-size: 13px; min-width: 30px;")

        time_label = QLabel(record.timestamp_hms)
        time_label.setStyleSheet(
            "font-family: 'Courier New', monospace; font-size: 12px; color: #64748B;"
        )

        badge = QLabel(f"{conf * 100:.0f}%")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(44)
        badge.setStyleSheet(
            f"background:{badge_bg}; color:{badge_fg}; border-radius:10px;"
            f"padding: 2px 6px; font-weight:600; font-size:11px;"
        )

        layout.addWidget(id_label)
        layout.addWidget(time_label)
        layout.addStretch()
        layout.addWidget(badge)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._timestamp)
        super().mousePressEvent(event)


class DefectListWidget(QWidget):
    defect_selected = pyqtSignal(float)  # timestamp_sec

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list[DefectRecord] = []
        self._cards: list[DefectCard] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(self.title_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 4, 0)
        self.cards_layout.setSpacing(4)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_widget)
        layout.addWidget(self.scroll)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.title_label.setText(t("defect_list_title"))

    def add_record(self, record: DefectRecord) -> None:
        self._records.append(record)
        card = DefectCard(record)
        card.clicked.connect(self.defect_selected)
        self._cards.append(card)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def clear(self) -> None:
        self._records.clear()
        for card in self._cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
