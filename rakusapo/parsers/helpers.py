"""パーサー共通の小さな抽出処理。"""

from __future__ import annotations

import re


def select(text: str, choices: list[tuple[str, str]], default: str = "【要入力】") -> str:
    lowered = text.lower()
    return next((value for keyword, value in choices if keyword.lower() in lowered), default)


def extract_name(text: str) -> str:
    match = re.search(
        r"([A-Zァ-ヶ一-龠々]{2,10})さん|顧客は([A-Zァ-ヶ一-龠々]{2,10})|"
        r"契約者は([A-Zァ-ヶ一-龠々]{2,10})", text
    )
    return (next(value for value in match.groups() if value) + " 様") if match else "【要入力】"


def bullets(text: str, keywords: list[str]) -> str:
    values = []
    for phrase in re.split(r"[、。！？」\n]", text):
        phrase = phrase.strip()
        if len(phrase) > 3 and any(keyword in phrase for keyword in keywords):
            values.append("・" + phrase)
    return "\n".join(values[:3]) if values else "・【要入力】"
