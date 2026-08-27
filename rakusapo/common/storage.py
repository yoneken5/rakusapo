"""用語辞書をアプリと同じフォルダへ保存する。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[2]


def data_path(filename: str) -> Path:
    return APP_DIR / filename


def load_json(filename: str, default: Any) -> Any:
    path = data_path(filename)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def atomic_write_json(filename: str, data: Any) -> None:
    path = data_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def update_json(filename: str, default: Any, update) -> Any:
    current = load_json(filename, default)
    result = update(current)
    atomic_write_json(filename, result)
    return result
