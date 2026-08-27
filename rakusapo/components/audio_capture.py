"""iPhone / Safari 向けの音声取り込みコンポーネント。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).resolve().parent / "ios_audio"

_audio_capture = components.declare_component(
    "rakusapo_audio_capture",
    path=str(_COMPONENT_DIR),
)


def audio_capture(key: str | None = None) -> dict[str, Any] | None:
    """録音または音声ファイル選択の結果を返す。"""
    return _audio_capture(key=key, default=None)
