from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from src.core.models import DefectRecord
from src.utils.language_manager import t

class DefectListWidget(QWidget):
    defect_selected = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(self.title_label)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._on_row_clicked)
        layout.addWidget(self.table)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.title_label.setText(t("defect_list_title"))
        self.table.setHorizontalHeaderLabels([t("defect_id"), t("timestamp_col"), t("confidence_col")])

    def add_record(self, record: DefectRecord) -> None:
        self._records.append(record)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._fill_row(row, record)

    def clear(self) -> None:
        self._records.clear()
        self.table.setRowCount(0)

    def _fill_row(self, row: int, record: DefectRecord) -> None:
        conf = record.confidence
        if conf >= 0.8:
            bg = QColor("#FFCDD2")
        elif conf >= 0.5:
            bg = QColor("#FFF9C4")
        else:
            bg = QColor("#C8E6C9")
        items = [
            QTableWidgetItem(f"#{record.defect_id}"),
            QTableWidgetItem(record.timestamp_hms),
            QTableWidgetItem(f"{conf*100:.0f}%"),
        ]
        for col, item in enumerate(items):
            item.setBackground(bg)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

    def _on_row_clicked(self, row: int, _col: int) -> None:
        if 0 <= row < len(self._records):
            self.defect_selected.emit(self._records[row].timestamp_sec)
