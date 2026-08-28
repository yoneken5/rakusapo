"""用語辞書をアプリと同じフォルダへ保存する。公開デモではセッションだけに覚える。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[2]


def is_streamlit_cloud() -> bool:
    return Path("/mount/src").exists() or os.getenv("RAKUSAPO_TERMS_IN_SESSION") == "1"


def _session_key(filename: str) -> str:
    return f"rakusapo_json_{filename}"


def _session_store() -> Any | None:
    if not is_streamlit_cloud():
        return None
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return None
    if get_script_run_ctx() is None:
        return None
    return st.session_state


def data_path(filename: str) -> Path:
    return APP_DIR / filename


def load_json(filename: str, default: Any) -> Any:
    store = _session_store()
    if store is not None:
        return store.get(_session_key(filename), default)
    path = data_path(filename)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def atomic_write_json(filename: str, data: Any) -> None:
    store = _session_store()
    if store is not None:
        store[_session_key(filename)] = data
        return
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
