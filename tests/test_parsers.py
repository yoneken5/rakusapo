import pytest

from rakusapo.common.registry import REPORT_TYPES, get_parser, parse_report


def test_all_five_templates_are_registered():
    assert REPORT_TYPES == ["損保更改", "損保新規", "生保新規", "生保アフター", "苦情対応"]
    assert all(parse_report("テスト入力", kind) for kind in REPORT_TYPES)


def test_sonpo_renewal_number_assignment_and_fixed_text():
    result = parse_report(
        "1.自動車、9月30日、対面\n2.変化なし\n3.実施済\n4.該当なし\n5.年齢条件を変更",
        "損保更改",
    )
    assert "・対象種目：（ 自動車 ）" in result
    assert "・満期日 ：9月30日" in result
    assert "・（〇）変化なし" in result
    assert "三井住友海上火災保険株式会社（継続）" in result
    assert "・年齢条件を変更" in result


def test_sonpo_new_multiple_selection_and_optional_four():
    text = "1.自動車、対面、配偶者\n2.保険料を抑えたい、補償を手厚くしたい\n3.GK クルマの保険\n5.引受確認"
    result = parse_report(text, "損保新規")
    assert "・（〇）保険料を抑えたい" in result
    assert "・（〇）補償内容を手厚くしたい" in result
    assert "・高齢者対応：（ 非該当 ）" in result
    assert "取扱保険会社一覧の提示・説明 ：（ 実施済 ）" in result
    validation = get_parser("損保新規").validate(text)
    assert validation.missing == ()


def test_seiho_new_number_assignment_and_multiple_products():
    text = (
        "1.デモ花子、昭和55年、妻と子供一人、会社員、他社医療保険加入、ヒアリング\n"
        "2.自宅、配偶者\n3.教育資金を準備したい\n"
        "4.あいおい生命、オリックス生命、医療保険\n"
        "5.保険料を慎重に検討したい\n6.9/10 クロージング、見積書、クレジットカード"
    )
    result = parse_report(text, "生保新規")
    assert "・顧客氏名：デモ花子" in result
    assert "[〇] あいおい生命" in result
    assert "[〇] オリックス生命" in result
    assert "[〇] 医療保険" in result
    assert "・次回アポイント：9/10 クロージング" in result
    assert get_parser("生保新規").validate(text).missing == ()


@pytest.mark.parametrize(
    ("kind", "text", "missing", "duplicates"),
    [
        ("損保更改", "1.自動車\n2.変化なし\n2.変化あり\n4.該当なし", (3,), (2,)),
        ("損保新規", "1.自動車\n3.商品\n5.注意", (2,), ()),
        ("生保新規", "1.氏名\n2.自宅\n3.希望\n4.商品\n5.反応", (6,), ()),
    ],
)
def test_missing_and_duplicate_number_warnings(kind, text, missing, duplicates):
    validation = get_parser(kind).validate(text)
    assert validation.missing == missing
    assert validation.duplicates == duplicates
    assert validation.has_warnings


def test_free_text_templates_do_not_require_numbers():
    assert not get_parser("生保アフター").validate("契約内容を説明した").has_warnings
    assert not get_parser("苦情対応").validate("苦情を受け付けた").has_warnings


def test_duplicate_number_uses_last_value_for_backward_compatibility():
    result = parse_report(
        "1.火災、対面、なし\n2.保険料\n2.補償を手厚く\n3.商品\n5.注意",
        "損保新規",
    )
    assert "・（ ）保険料を抑えたい" in result
    assert "・（〇）補償内容を手厚くしたい" in result
