"""生保アフターテンプレート。"""

from .helpers import extract_name

REQUIRED_NUMBERS: set[int] = set()
OPTIONAL_NUMBERS = {1, 2, 3, 4, 5}


def parse(text: str) -> str:
    return f"""生保アフター
【1.基本情報】
・お客様名：{extract_name(text)}

【2.ご契約状況・ご相談内容】
・{text}

【3.対応・説明内容】
・【要入力】

【4.次回対応】
・【要入力】

【5.特記事項・備忘録】
・
"""
