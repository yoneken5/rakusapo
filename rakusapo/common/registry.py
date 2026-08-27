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


def _guide(module: ModuleType) -> str:
    return getattr(module, "GUIDE", "入力例はありません。")


PARSERS = {
    "損保更改": ParserDefinition("損保更改", sonpo_renewal, _guide(sonpo_renewal)),
    "損保新規": ParserDefinition("損保新規", sonpo_new, _guide(sonpo_new)),
    "生保新規": ParserDefinition("生保新規", seiho_new, _guide(seiho_new)),
    "生保アフター": ParserDefinition("生保アフター", seiho_after, _guide(seiho_after)),
    "苦情対応": ParserDefinition("苦情対応", complaint, _guide(complaint)),
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
