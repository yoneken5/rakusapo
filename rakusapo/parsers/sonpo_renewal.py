"""損保更改テンプレート。"""

from __future__ import annotations

import re

from rakusapo.common.numbering import extract_numbered_sections
from .helpers import select

REQUIRED_NUMBERS = {1, 2, 3, 4}
OPTIONAL_NUMBERS = {5}

GUIDE = """【1.基本情報】
・対象種目
・満期日
・面談手法
例）1.自動車、9月30日、対面

【2.ご意向・状況変化の確認】
・変化なし / 変化あり
例）2.変化なし

【3.重要事項説明と前年差異説明】
・前年差異説明（実施済 / 該当なし）
例）3.実施済

【4.特定顧客への配慮】
・高齢者対応（該当なし / 親族同席 など）
例）4.該当なし

【5.特記事項・備忘録】（任意）
例）5.22歳が運転するため本人配偶者限定を削除"""


def parse(text: str) -> str:
    numbered = extract_numbered_sections(text)
    fallback = "" if numbered else text
    one, two, three, four = (numbered.get(i, fallback) for i in range(1, 5))
    five = numbered.get(5, "")
    genre = select(one, [("自動車", "自動車"), ("火災", "火災"), ("傷害", "傷害"),
                         ("賠責", "賠責"), ("その他", "その他")])
    date_match = re.search(r"(\d{1,2}月\d{1,2}日)", one)
    date = date_match.group(1) if date_match else "【要入力】"
    method = select(one, [("対面", "対面"), ("web", "WEB"), ("オンライン", "WEB"),
                          ("電話", "電話"), ("郵送", "郵送・SMS等"), ("sms", "郵送・SMS等")])
    if "変化あり" in two:
        changes = "・（　）変化なし（前年と同等の条件を希望）\n・（〇）変化あり・条件変更希望"
    elif "変化なし" in two:
        changes = "・（〇）変化なし（前年と同等の条件を希望）\n・（　）変化あり・条件変更希望"
    else:
        changes = "・（　）変化なし（前年と同等の条件を希望）\n・（　）変化あり・条件変更希望"
    difference = ("該当なし" if "該当なし" in three else
                  "実施済" if any(k in three for k in ["実施済", "前年差異", "変更点", "商品改定", "差異説明"])
                  else "【要入力】")
    if any(k in four for k in ["該当なし", "非該当"]):
        elderly = "非該当"
    else:
        elderly = select(four, [("親族", "親族同席"), ("複数回", "複数回面談"),
                                ("電話フォロー", "郵送・WEB手続き時の電話フォロー")])
    return f"""損保更改
【1.基本情報】
・対象種目：（ {genre} ）
・満期日 ：{date}
・面談手法：（ {method} ）

【2. ご意向・状況変化の確認】
{changes}
 └（ 運転者の年齢・範囲変更 / 使用目的変更 / 車両入替 / 補償内容の見直し / その他： ）

【 比較推奨・提案内容】
・提案先：三井住友海上火災保険株式会社（継続）
▼ 推奨・最終決定の理由
・（〇）お客様より、現在加入中の保険会社（三井住友海上）での継続希望があったため

【3. 重要事項説明と前年差異説明】
・前年からの変更点（保険料の増減、商品改定、特約の統廃合など）の説明：（ {difference} ）
・重要事項説明書等の交付・説明：（ 実施済 ）
・意向と提案内容の最終合致確認：（ 合致している ）

【4. 特定顧客への配慮】
・高齢者対応：（ {elderly} ）

【5.特記事項・備忘録】
・{five}
"""
