"""番号付き入力の抽出と検証。"""

from __future__ import annotations

import re
from dataclasses import dataclass


MARKER = re.compile(r"(?<!\d)([1-7])(?:\u756a|\u3070\u3093)?(?:[.\uff0e\u3001:\uff1a]\s*|\s+|(?=[^\d\s]))")


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
            result.append("\u4e0d\u8db3\u3057\u3066\u3044\u308b\u756a\u53f7: " + ", ".join(map(str, self.missing)))
        if self.duplicates:
            result.append("\u91cd\u8907\u3057\u3066\u3044\u308b\u756a\u53f7: " + ", ".join(map(str, self.duplicates)))
        if self.unexpected:
            result.append("\u5bfe\u8c61\u5916\u306e\u756a\u53f7: " + ", ".join(map(str, self.unexpected)))
        return result


def numbered_entries(source: str) -> list[tuple[int, str]]:
    source = re.sub(r"(?m)^(\s*[1-7])(?=[^\d.\uff0e\u3001:\uff1a\s])", r"\1.", source)
    matches = list(MARKER.finditer(source))
    return [
        (
            int(match.group(1)),
            source[
                match.end() : matches[index + 1].start()
                if index + 1 < len(matches)
                else len(source)
            ].strip(" \u3001\u3002\n\u3011\uff3b\uff3d[]\u30fb"),
        )
        for index, match in enumerate(matches)
    ]


def extract_numbered_sections(source: str) -> dict[int, str]:
    """従来どおり、重複番号は後に入力された値を採用する。"""
    return dict(numbered_entries(source))


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
