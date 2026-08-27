"""損保新規テンプレート。"""

from __future__ import annotations

import re

from rakusapo.common.numbering import extract_numbered_sections
from .helpers import select

REQUIRED_NUMBERS = {1, 2, 3, 5}
OPTIONAL_NUMBERS = {4}

GUIDE = """【1.基本情報】
・対象種目
・面談手法
・同席者
例）1.自動車、対面、配偶者

【2.当初の意向把握】（複数可）
・保険料を抑えたい / 補償を手厚くしたい など
例）2.保険料を抑えたい、補償を手厚くしたい

【3.比較推奨・提案】
・商品名
例）3.GK クルマの保険

【4.特定顧客への配慮】（任意）
・高齢者対応など（未入力なら非該当）
例）4.該当なし

【5.特記事項・引受上の注意点】
例）5.引受条件を確認する"""


def parse(text: str) -> str:
    numbered = extract_numbered_sections(text)
    fallback = "" if numbered else text
    one, two, three = (numbered.get(i, fallback) for i in range(1, 4))
    four, five = numbered.get(4, ""), numbered.get(5, "")
    genre = select(one, [("自動車", "自動車"), ("火災", "火災"), ("傷害", "傷害"),
                         ("新種", "新種"), ("その他", "その他")])
    method = select(one, [("対面", "対面"), ("web", "WEB"), ("オンライン", "WEB"), ("電話", "電話")])
    attendee = select(one, [("配偶者", "配偶者"), ("奥様", "配偶者"), ("ご主人", "配偶者"),
                            ("子供", "子"), ("お子", "子"), ("同席なし", "なし"),
                            ("なし", "なし"), ("その他", "その他")])
    def mark(words): return "〇" if any(word in two for word in words) else " "
    budget = mark(["保険料", "予算", "安く", "抑え"])
    coverage = mark(["手厚", "車両保険", "水災", "補償内容"])
    review = mark(["見直", "比較", "他社"])
    specified = mark(["指定", "特定の保険会社", "特定の商品"])
    other = mark(["その他"])
    reason_match = re.search(r"理由[：:\s]*([^、。\n]+)", two)
    other_match = re.search(r"その他[：:\s]*([^、。\n]+)", two)
    reason = reason_match.group(1).strip() if reason_match else ""
    other_need = other_match.group(1).strip() if other_match else ""
    product = re.sub(r"^(?:商品名|提案商品)[：:\s]*", "", three).strip() or "【要入力】"
    if not four or any(k in four for k in ["該当なし", "非該当"]):
        elderly = disability = "非該当"
    else:
        elderly = select(four, [("親族", "親族同席"), ("複数回", "複数回面談"),
                                ("管理者", "管理者事前相談")], "非該当")
        disability = "合理的配慮を実施" if any(k in four for k in ["障がい", "合理的配慮"]) else "非該当"
    return f"""損保新規
【1.基本情報】
・対象種目：（ {genre} ）
・面談手法：（ {method} ）
・同席者 ：（ {attendee} ）

【法定要件の基本対応】
・権限明示（所属保険会社の明示等）：当代理店が、損害保険においては三井住友海上火災保険株式会社のみを取り扱う募集代理店である旨（および代理権の有無などの権限明示）をお客様に説明した（ 実施済 ）
・取扱保険会社一覧の提示・説明 ：（ 実施済 ）

【2. 当初の意向把握（複数選択可）】
・（{budget}）保険料を抑えたい・予算内におさめたい
・（{coverage}）補償内容を手厚くしたい（例：車両保険付帯、水災付帯など）
・（{review}）現在加入中の内容を見直したい・他社と比較したい
・（{specified}）特定の保険会社・商品への指定あり（理由：{reason}）
・（{other}）その他具体的な要望：（ {other_need} ）

【3. 比較推奨・提案のプロセス】
・提案商品：（ 三井住友海上 ／ 商品名：{product} ）
▼ 当該商品を推奨した理由
・（〇）当代理店の損害保険推奨販売方針（損害保険は三井住友海上火災保険株式会社の1社のみを取り扱うという経営方針）に基づくため

▼ 比較説明の実施有無
・（〇）単一商品の提案のみ（理由：当代理店の損保取扱保険会社が三井住友海上の1社のみであり、他社比較が非該当であるため）

【重要事項説明と最終合致確認】
・重要事項説明書（契約概要・注意喚起情報）の交付・説明：（ 実施済 ）
・意向と提案内容の最終合致確認：三井住友海上の提案内容が、お客様の当初の意向と完全に合致していることを対話の中で確認し、ご納得のうえ合意をいただいた。

【4. 特定顧客への配慮】
・高齢者対応：（ {elderly} ）
・障がい等への配慮：（ {disability} ）

【5.特記事項・引受上の注意点など】
・{five}
"""
