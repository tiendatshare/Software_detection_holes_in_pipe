from pathlib import Path
from PyQt6.QtGui import QPixmap

_BRAND_DIR = Path("assets/brand")
_SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".svg")

def get_logo_path() -> str | None:
    for ext in _SUPPORTED_EXT:
        path = _BRAND_DIR / f"logo{ext}"
        if path.exists():
            return str(path)
    return None

def load_logo() -> QPixmap | None:
    path = get_logo_path()
    if path:
        pix = QPixmap(path)
        if not pix.isNull():
            return pix.scaledToHeight(40)
    return None
