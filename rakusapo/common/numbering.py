"""番号付き入力の抽出と検証。"""

from __future__ import annotations

import re
from dataclasses import dataclass


MARKER = re.compile(r"(?<!\d)([1-7])(?:番|ばん)?(?:[.．、:：]\s*|\s+|(?=[^\d\s]))")


@dataclass(frozen=True)
class NumberingValidation:
    missing: tuple[int, ...]
    duplicates: tuple[int, ...]
    unexpected: tuple[int, ...]

    @property
    def has_warnings(self) -> bool:
        return bool(self.missing or self.duplicates or self.unexpected)

    def messages(self) -> list[str]:
        result = []
        if self.missing:
            result.append("不足している番号: " + ", ".join(map(str, self.missing)))
        if self.duplicates:
            result.append("重複している番号: " + ", ".join(map(str, self.duplicates)))
        if self.unexpected:
            result.append("対象外の番号: " + ", ".join(map(str, self.unexpected)))
        return result


def numbered_entries(source: str) -> list[tuple[int, str]]:
    source = re.sub(r"(?m)^(\s*[1-7])(?=[^\d.．、:：\s])", r"\1.", source)
    matches = list(MARKER.finditer(source))
    return [
        (
            int(match.group(1)),
            source[
                match.end() : matches[index + 1].start()
                if index + 1 < len(matches)
                else len(source)
            ].strip(" 、。\n】［］[]・"),
        )
        for index, match in enumerate(matches)
    ]


def extract_numbered_sections(source: str) -> dict[int, str]:
    """従来どおり、重複番号は後に入力された値を採用する。"""
    return dict(numbered_entries(source))


def _bullet_items(content: str) -> list[str]:
    cleaned = content.strip()
    if not cleaned:
        return []
    parts = re.split(r"[\n、,]+", cleaned)
    items = []
    for part in parts:
        item = part.strip(" ・。．.　")
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
        return "\n".join(f"・{item}" for item in bullets)

    first = MARKER.search(re.sub(r"(?m)^(\s*[1-7])(?=[^\d.．、:：\s])", r"\1.", source))
    preamble = source[: first.start()].strip() if first else ""
    blocks: list[str] = []
    if preamble:
        blocks.append(preamble)
    for number, content in entries:
        lines = [f"【{number}】"]
        lines.extend(f"・{item}" for item in _bullet_items(content))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def validate_numbering(
    source: str,
    *,
    required: set[int],
    optional: set[int] | None = None,
) -> NumberingValidation:
    optional = optional or set()
    entries = numbered_entries(source)
    numbers = [number for number, _ in entries]
    # 番号入力をしていない自由記述テンプレートには警告しない。
    if not numbers:
        return NumberingValidation((), (), ())
    accepted = required | optional
    missing = tuple(sorted(required - set(numbers)))
    duplicates = tuple(sorted({number for number in numbers if numbers.count(number) > 1}))
    unexpected = tuple(sorted(set(numbers) - accepted))
    return NumberingValidation(missing, duplicates, unexpected)
