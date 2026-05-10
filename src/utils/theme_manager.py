_THEMES = {
    "steel_blue": {
        "light": {
            "bg": "#F5F7FA", "sidebar": "#FFFFFF", "accent": "#1565C0",
            "text": "#1A1A2E", "border": "#D0D7E3", "row_hover": "#E3ECF7",
            "conf_high": "#FFEBEE", "conf_mid": "#FFF8E1", "conf_low": "#E8F5E9",
        },
        "dark": {
            "bg": "#0D1B2A", "sidebar": "#1A2B3C", "accent": "#4FC3F7",
            "text": "#E8F4FD", "border": "#2A3F52", "row_hover": "#1E3448",
            "conf_high": "#4A1010", "conf_mid": "#4A3A00", "conf_low": "#0A3A1A",
        },
    },
    "slate_amber": {
        "light": {
            "bg": "#F8FAFC", "sidebar": "#F1F5F9", "accent": "#F59E0B",
            "text": "#0F172A", "border": "#E2E8F0", "row_hover": "#FEF3C7",
            "conf_high": "#FFEBEE", "conf_mid": "#FFF8E1", "conf_low": "#E8F5E9",
        },
        "dark": {
            "bg": "#1E293B", "sidebar": "#0F172A", "accent": "#F59E0B",
            "text": "#F1F5F9", "border": "#334155", "row_hover": "#2D3748",
            "conf_high": "#4A1010", "conf_mid": "#4A3A00", "conf_low": "#0A3A1A",
        },
    },
    "carbon_green": {
        "light": {
            "bg": "#FAFAFA", "sidebar": "#F0F0F0", "accent": "#00C896",
            "text": "#1C1C1C", "border": "#E0E0E0", "row_hover": "#E0FAF3",
            "conf_high": "#FFEBEE", "conf_mid": "#FFF8E1", "conf_low": "#E8F5E9",
        },
        "dark": {
            "bg": "#161616", "sidebar": "#1E1E1E", "accent": "#00C896",
            "text": "#E0E0E0", "border": "#2A2A2A", "row_hover": "#0A2A20",
            "conf_high": "#4A1010", "conf_mid": "#4A3A00", "conf_low": "#0A3A1A",
        },
    },
}

def get_stylesheet(theme: str, mode: str) -> str:
    c = _THEMES.get(theme, _THEMES["slate_amber"]).get(mode, _THEMES["slate_amber"]["light"])
    return f"""
        QMainWindow, QWidget {{
            background-color: {c['bg']};
            color: {c['text']};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }}
        QToolBar {{
            background-color: {c['sidebar']};
            border-bottom: 1px solid {c['border']};
            padding: 4px 8px;
            spacing: 8px;
        }}
        QPushButton {{
            background-color: {c['accent']};
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            padding: 6px 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {c['accent']}CC;
        }}
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text']}88;
        }}
        QTableWidget {{
            background-color: {c['sidebar']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            gridline-color: {c['border']};
        }}
        QTableWidget::item:hover {{
            background-color: {c['row_hover']};
        }}
        QTableWidget::item:selected {{
            background-color: {c['accent']}44;
        }}
        QHeaderView::section {{
            background-color: {c['bg']};
            color: {c['text']};
            border: none;
            border-bottom: 2px solid {c['accent']};
            padding: 6px;
            font-weight: 600;
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {c['border']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {c['accent']};
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}
        QComboBox {{
            background-color: {c['sidebar']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {c['text']};
        }}
        QProgressBar {{
            background-color: {c['border']};
            border-radius: 4px;
            height: 6px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 4px;
        }}
        QStatusBar {{
            background-color: {c['sidebar']};
            border-top: 1px solid {c['border']};
            color: {c['text']};
        }}
        QLabel#video_label {{
            background-color: #000000;
            border-radius: 4px;
        }}
    """

def available_themes() -> list[str]:
    return list(_THEMES.keys())
