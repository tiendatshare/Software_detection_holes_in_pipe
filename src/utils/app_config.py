import json
from pathlib import Path

_CONFIG_PATH = Path("config.json")
_DEFAULTS = {
    "model_path": "models/best.pt",
    "confidence_threshold": 0.5,
    "theme": "slate_amber",
    "theme_mode": "light",
    "language": "vi",
}

def load() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**_DEFAULTS, **data}
    return dict(_DEFAULTS)

def save(config: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get(key: str):
    return load().get(key, _DEFAULTS.get(key))

def set(key: str, value) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)
