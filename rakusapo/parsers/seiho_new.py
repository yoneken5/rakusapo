"""生保新規テンプレート。"""

from __future__ import annotations

import re

from rakusapo.common.numbering import extract_numbered_sections

REQUIRED_NUMBERS = {1, 2, 3, 4, 5, 6}
OPTIONAL_NUMBERS = {7}
INSURERS = ["あいおい生命", "ジブラルタ生命", "オリックス生命", "メットライフ生命",
            "アフラック生命", "日本生命", "プライマリー生命"]
PRODUCTS = ["医療保険", "収入保障保険", "がん保険", "介護保険", "終身保険",
            "ドル建て終身", "養老保険", "定期保険"]

GUIDE = """【1】顧客の基本情報
・顧客氏名
・生年月日
・家族構成
・職業／勤務先
・現在の契約状況
・営業フェーズ
例）1.山田太郎、昭和55年、妻と子供一人、会社員、他社医療保険加入、ヒアリング

【2】対応の概要
・面談場所
・同席者
例）2.自宅、配偶者

【3】面談・対応の詳細
・ヒアリング内容・ニーズ
例）3.教育資金を準備したい

【4】提案内容
・保険会社（複数可）
・商品（複数可）
例）4.あいおい生命、オリックス生命、医療保険

【5】お客様の反応・懸念点
例）5.保険料を慎重に検討したい

【6】次回アクションと宿題
・次回アポイント
・こちらの準備物
・お客様の準備物
例）6.9/10 クロージング、見積書、クレジットカード

【7】所感・備考（任意）
例）7.数字での比較が有効"""


def _tokens(section: str) -> list[str]:
    return [token.strip() for token in re.split(r"[、,\n]", section) if token.strip()]


def _labeled(section: str, labels: list[str]) -> str:
    match = re.search(
        rf"(?:{'|'.join(map(re.escape, labels))})(?:は|が|[:：])?\s*([^、。\n]+)",
        section,
    )
    return match.group(1).strip() if match else ""


def parse(text: str) -> str:
    numbered = extract_numbered_sections(text)
    fallback = "" if numbered else text
    sections = {i: numbered.get(i, fallback if i <= 6 else "") for i in range(1, 8)}
    one, one_tokens = sections[1], _tokens(sections[1])
    name = _labeled(one, ["顧客氏名", "氏名", "名前"])
    if not name and one_tokens:
        candidate = re.sub(r"(?:さん|様)$", "", one_tokens[0]).strip()
        if re.fullmatch(r"[A-Zァ-ヶ一-龠々]{2,10}", candidate):
            name = candidate
    name = name or "【要入力】"
    birthday_match = re.search(
        r"(\d{4}年(?:\d{1,2}月\d{1,2}日)?|(?:昭和|平成|令和)\d{1,2}年(?:\d{1,2}月\d{1,2}日)?)",
        one,
    )
    birthday = birthday_match.group(0) if birthday_match else "【要入力】"
    family = _labeled(one, ["家族構成", "ご家族"]) or next(
        (token for token in one_tokens if any(k in token for k in ["家族", "妻", "夫", "子", "独身"])),
        "【要入力】",
    )
    job = _labeled(one, ["職業", "勤務先"]) or next(
        (token for token in one_tokens if any(k in token for k in ["会社員", "公務員", "自営業", "パート", "主婦", "勤務"])),
        "【要入力】",
    )
    contract_match = re.search(r"((?:現在|他社)[^。\n]{0,40}(?:加入|未加入|契約)[^。\n]*)", one)
    contract = contract_match.group(1).strip() if contract_match else "【要入力】"
    phase = lambda words: "[〇]" if any(word in one for word in words) else "[　]"
    two_tokens = _tokens(sections[2])
    location = _labeled(sections[2], ["面談場所", "場所"]) or (two_tokens[0] if two_tokens else "【要入力】")
    attendee = _labeled(sections[2], ["同席者"]) or (two_tokens[1] if len(two_tokens) > 1 else "【要入力】")
    insurers = "\n".join(f"[{'〇' if value in sections[4] else '　'}] {value}" for value in INSURERS)
    products = "\n".join(f"[{'〇' if value in sections[4] else '　'}] {value}" for value in PRODUCTS)
    six_tokens = _tokens(sections[6])
    appointment = _labeled(sections[6], ["次回アポイント"]) or (six_tokens[0] if six_tokens else "【要入力】")
    ours = _labeled(sections[6], ["こちらの準備物", "こちらの宿題", "私の宿題"]) or (
        six_tokens[1] if len(six_tokens) > 1 else "【要入力】")
    theirs = _labeled(sections[6], ["お客様の準備物", "お客様の宿題"]) or (
        six_tokens[2] if len(six_tokens) > 2 else "【要入力】")
    return f"""【1】顧客の基本情報
・顧客氏名：{name}
・生年月日：{birthday}
・家族構成：{family}
・職業／勤務先：{job}
・現在の契約状況：{contract}
・現在の営業フェーズ：
{phase(["アプローチ", "初回"])} アプローチ（初回接触）
{phase(["ヒアリング", "意向確認"])} ヒアリング（意向確認・情報収集）
{phase(["プレゼン", "プラン提示"])} プレゼンテーション（プラン提示）
{phase(["クロージング", "申込"])} クロージング（申込手続き）

【2】対応の概要
・面談場所：{location}
・同席者：{attendee}

【3】面談・対応の詳細
・ヒアリング内容・お客様のニーズ（意向確認）
・{sections[3] or "【要入力】"}

【4】提案内容
・生命保険会社
{insurers}

・商品
{products}

【5】お客様の反応・懸念点（反論・ネック）
・{sections[5] or "【要入力】"}

【6】次回アクションと宿題
・次回アポイント：{appointment}
・こちらの準備物（宿題）：{ours}
・お客様の準備物（宿題）：{theirs}

【7】所感・備考
・{sections[7]}
"""
