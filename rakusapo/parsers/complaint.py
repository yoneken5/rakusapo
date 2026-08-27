"""苦情対応テンプレート。"""

from __future__ import annotations

import re

from .helpers import bullets, extract_name

REQUIRED_NUMBERS: set[int] = set()
OPTIONAL_NUMBERS = {1, 2, 3, 4, 5}

GUIDE = """番号入力は不要です。受付から次回対応までまとめて話してください。

【1】受付基本情報（受付日時・顧客氏名・区分）
【2】発生状況・詳細
【3】対応内容
【4】今後の約束・Next Action
【5】備考・所感"""


def parse(text: str) -> str:
    date_match = re.search(r"(\d{1,2}月\d{1,2}日\d{1,2}時|\d{1,2}月\d{1,2}日)", text)
    date = date_match.group(1) if date_match else "【要入力】"
    category = "苦情・不満" if any(k in text for k in ["苦情", "不満", "お叱り", "クレーム"]) else "【要入力】"
    location_match = re.search(r"(?:場所は|場所[:：]|頃[、,\s]+)([^。]{2,40}?)(?:にて|で発生|で事故|。)", text)
    location = location_match.group(1).strip() if location_match else "【要入力】"
    situation = bullets(text, ["発生", "交差点", "追突", "ケガ", "物損", "千葉"])
    response = bullets(text, ["お見舞い", "お詫び", "相手", "対応", "説明", "手順"])
    promise = bullets(text, ["明日", "折り返し", "進捗", "連絡", "担当"])
    return f"""【1】受付基本情報
・受付日時：{date}
・顧客氏名：{extract_name(text)}
・区分：（〇）{category}

【2】発生状況・詳細
・発生日時・場所：{date} / {location}
・具体的な状況：
{situation}

【3】対応内容
・一次対応内容・お詫び：
{response}

【4】今後の約束・Next Action
・次回の対応予定・宿題：
{promise}

【5】備考・所感
・
"""
