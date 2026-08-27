"""用語辞書の補正と入出力。この端末にだけ保存し、顧客名は登録しない。"""

from __future__ import annotations

import json
import re
from typing import Any

from .storage import atomic_write_json, load_json, update_json

TERMS_FILE = "rakusapo_terms.json"
DEFAULT_TERMS = {
    "みついすみとも": "三井住友", "みつい": "三井", "すみとも": "住友",
    "じどうしゃほけん": "自動車保険", "かさいほけん": "火災保険",
    "しょうがいほけん": "傷害保険", "いこうかくにん": "意向確認",
    "いこうはあく": "意向把握", "じゅうせつ": "重要事項説明",
    "ちゅういかんきじょうほう": "注意喚起情報", "ひかくすいしょう": "比較推奨",
    "こうれいしゃたいおう": "高齢者対応", "そんぽ": "損保", "せいほ": "生保",
    "まんきこうかい": "満期更改", "ほけんりょう": "保険料",
    "ほしょうないよう": "補償内容", "めんせききんがく": "免責金額",
    "とくやく": "特約", "へんがくほけん": "変額保険",
    "がくしほけん": "学資保険", "くろーじんぐ": "クロージング",
}


def load_custom_terms() -> dict[str, dict[str, Any]]:
    data = load_json(TERMS_FILE, {})
    return data if isinstance(data, dict) else {}


def save_custom_terms(terms: dict[str, Any]) -> None:
    atomic_write_json(TERMS_FILE, terms)


def add_term(source: str, replacement: str) -> None:
    def merge(current):
        current = current if isinstance(current, dict) else {}
        old = current.get(source, {})
        current[source] = {"replacement": replacement, "uses": old.get("uses", 0)}
        return current
    update_json(TERMS_FILE, {}, merge)


def apply_learned_terms(text: str, *, count_usage: bool = False) -> str:
    custom = load_custom_terms()
    replacements = {
        **{source: {"replacement": target, "uses": 0} for source, target in DEFAULT_TERMS.items()},
        **custom,
    }
    corrected, counts = text, {}
    for source, data in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        target = data.get("replacement", "") if isinstance(data, dict) else str(data)
        corrected, count = re.subn(re.escape(source), target, corrected, flags=re.IGNORECASE)
        if count and source in custom:
            counts[source] = count
    if count_usage and counts:
        def increment(current):
            current = current if isinstance(current, dict) else {}
            for source, count in counts.items():
                if source in current and isinstance(current[source], dict):
                    current[source]["uses"] = current[source].get("uses", 0) + count
            return current
        update_json(TERMS_FILE, {}, increment)
    return corrected


def export_terms_json() -> str:
    return json.dumps(load_custom_terms(), ensure_ascii=False, indent=2)


def import_terms_json(payload: bytes | str) -> int:
    text = payload.decode("utf-8-sig") if isinstance(payload, bytes) else payload
    incoming = json.loads(text)
    if not isinstance(incoming, dict):
        raise ValueError("辞書JSONはオブジェクト形式である必要があります。")
    normalized = {}
    for source, value in incoming.items():
        if not isinstance(source, str) or not source.strip():
            raise ValueError("変換元は空でない文字列にしてください。")
        if isinstance(value, str):
            normalized[source] = {"replacement": value, "uses": 0}
        elif isinstance(value, dict) and isinstance(value.get("replacement"), str):
            normalized[source] = {
                "replacement": value["replacement"],
                "uses": max(0, int(value.get("uses", 0))),
            }
        else:
            raise ValueError(f"用語「{source}」の形式が不正です。")
    def merge(current):
        current = current if isinstance(current, dict) else {}
        current.update(normalized)
        return current
    update_json(TERMS_FILE, {}, merge)
    return len(normalized)
