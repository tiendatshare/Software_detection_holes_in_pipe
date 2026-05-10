import json
from pathlib import Path

_SUPPORTED = ("vi", "en", "ko")
_cache: dict = {}
_current: str = "vi"

def set_language(code: str) -> None:
    global _current, _cache
    if code not in _SUPPORTED:
        code = "vi"
    _current = code
    path = Path("assets/i18n") / f"{code}.json"
    with open(path, "r", encoding="utf-8") as f:
        _cache = json.load(f)

def t(key: str, **kwargs) -> str:
    text = _cache.get(key, key)
    return text.format(**kwargs) if kwargs else text

def current() -> str:
    return _current
