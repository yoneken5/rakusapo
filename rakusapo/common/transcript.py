"""音声文字起こしテキストの整形。"""

from __future__ import annotations

import re

from .numbering import MARKER, numbered_entries


def _bullet_items(content: str) -> list[str]:
    cleaned = content.strip()
    if not cleaned:
        return []
    parts = re.split(r"[\n\u3001,]+", cleaned)
    items = []
    for part in parts:
        item = part.strip(" \u30fb\u3002\uff0e.\u3000")
        if item:
            items.append(item)
    return items or [cleaned]


def format_numbered_transcript(source: str) -> str:
    """番号ごとに段落を分け、内容を箇条書きにする。"""
    source = source.strip()
    if not source:
        return ""
    entries = numbered_entries(source)
    if not entries:
        bullets = _bullet_items(source)
        if len(bullets) <= 1:
            return source
        return "\n".join(f"\u30fb{item}" for item in bullets)

    normalized = re.sub(r"(?m)^(\s*[1-7])(?=[^\d.\uff0e\u3001:\uff1a\s])", r"\1.", source)
    first = MARKER.search(normalized)
    preamble = source[: first.start()].strip() if first else ""
    blocks: list[str] = []
    if preamble:
        blocks.append(preamble)
    for number, content in entries:
        lines = [f"\u3010{number}\u3011"]
        lines.extend(f"\u30fb{item}" for item in _bullet_items(content))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
