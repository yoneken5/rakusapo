import json

from rakusapo.common import storage, terms, transcript
from rakusapo.common.demo import DEMO_INPUTS
from rakusapo.common.registry import REPORT_TYPES, get_parser


def test_file_storage_is_used_outside_cloud(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path)
    monkeypatch.delenv("RAKUSAPO_TERMS_IN_SESSION", raising=False)
    assert storage.is_streamlit_cloud() is False
    storage.atomic_write_json("rakusapo_terms.json", {"じゅうせつ": {"replacement": "重要事項説明", "uses": 0}})
    assert (tmp_path / "rakusapo_terms.json").exists()


def test_term_import_saves_locally(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path)
    count = terms.import_terms_json('{"じゅうせつ":{"replacement":"重要事項説明","uses":2}}')
    assert count == 1
    assert terms.load_custom_terms()["じゅうせつ"]["replacement"] == "重要事項説明"
    assert json.loads((tmp_path / "rakusapo_terms.json").read_text(encoding="utf-8"))
    assert not list(tmp_path.glob("*.tmp"))


def test_term_update_and_delete(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path)
    terms.add_term("じゅうせつ", "重要事項説明")
    terms.update_term("じゅうせつ", "重要事項の説明", new_source="じゅうせつめい")
    data = terms.load_custom_terms()
    assert "じゅうせつ" not in data
    assert data["じゅうせつめい"]["replacement"] == "重要事項の説明"
    terms.delete_term("じゅうせつめい")
    assert terms.load_custom_terms() == {}


def test_format_numbered_transcript_makes_bullets():
    text = "1.自動車、9月30日、対面\n2.変化なし"
    formatted = transcript.format_numbered_transcript(text)
    assert formatted == "1.\n・自動車\n・9月30日\n・対面\n2.\n・変化なし"


def test_formatted_transcript_still_parses():
    formatted = transcript.format_numbered_transcript(
        "1.自動車、9月30日、対面\n2.変化なし\n3.実施済\n4.該当なし\n5.年齢条件を変更"
    )
    result = get_parser("損保更改").parse(formatted)
    assert "・対象種目：（ 自動車 ）" in result
    assert "・満期日 ：9月30日" in result
    assert "・年齢条件を変更" in result


def test_guides_show_section_titles():
    guide = get_parser("損保更改").guide
    assert "【1.基本情報】" in guide
    assert "対象種目" in guide
    assert "満期日" in guide
    assert "面談手法" in guide
    assert transcript.format_numbered_transcript("1.a") == "1.\n・a"
    assert "【" not in transcript.format_numbered_transcript("1.a、b\n2.c")


def test_format_strips_legacy_brackets():
    formatted = transcript.format_numbered_transcript("【1】\n・自動車\n\n【2】\n・変化なし")
    assert "【" not in formatted
    assert formatted == "1.\n・自動車\n2.\n・変化なし"


def test_demo_inputs_cover_all_templates_without_real_names():
    assert set(DEMO_INPUTS) == set(REPORT_TYPES)
    for kind, text in DEMO_INPUTS.items():
        result = get_parser(kind).parse(text)
        assert result.strip()
        assert "山田" not in text
        assert "山田" not in result
