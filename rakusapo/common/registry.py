"""テンプレート登録。UIはこのモジュールだけを参照する。"""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType

from rakusapo.parsers import complaint, seiho_after, seiho_new, sonpo_new, sonpo_renewal
from .numbering import NumberingValidation, validate_numbering


@dataclass(frozen=True)
class ParserDefinition:
    label: str
    module: ModuleType
    guide: str

    def parse(self, text: str) -> str:
        return self.module.parse(text)

    def validate(self, text: str) -> NumberingValidation:
        return validate_numbering(
            text,
            required=set(self.module.REQUIRED_NUMBERS),
            optional=set(self.module.OPTIONAL_NUMBERS),
        )


PARSERS = {
    "損保更改": ParserDefinition("損保更改", sonpo_renewal, "1.自動車、9月30日、対面\n2.変化なし\n3.実施済\n4.該当なし\n5.22歳が運転するため本人配偶者限定を削除"),
    "損保新規": ParserDefinition("損保新規", sonpo_new, "1.自動車、対面、配偶者\n2.保険料を抑えたい、補償を手厚くしたい\n3.GK クルマの保険\n4.該当なし\n5.引受条件を確認する"),
    "生保新規": ParserDefinition("生保新規", seiho_new, "1.山田太郎、昭和55年、妻と子供一人、会社員、他社医療保険加入、ヒアリング\n2.自宅、配偶者\n3.教育資金を準備したい\n4.あいおい生命、オリックス生命、医療保険\n5.保険料を慎重に検討したい\n6.9/10 クロージング、見積書、クレジットカード\n7.数字での比較が有効"),
    "生保アフター": ParserDefinition("生保アフター", seiho_after, "対応内容をそのまま話す、または入力してください。"),
    "苦情対応": ParserDefinition("苦情対応", complaint, "受付内容、発生状況、対応内容、次回対応を入力してください。"),
}
REPORT_TYPES = list(PARSERS)


def get_parser(report_type: str) -> ParserDefinition:
    try:
        return PARSERS[report_type]
    except KeyError as exc:
        raise ValueError(f"未対応の日報種類です: {report_type}") from exc


def parse_report(text: str, report_type: str) -> str:
    if not text.strip():
        return "音声またはテキストを入力してください。"
    return get_parser(report_type).parse(text)
