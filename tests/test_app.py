from pathlib import Path

from streamlit.testing.v1 import AppTest


def open_app():
    app = Path(__file__).resolve().parents[1] / "rakusapo_app.py"
    at = AppTest.from_file(str(app), default_timeout=20).run()
    return at


def test_streamlit_app_smoke():
    at = open_app()
    assert not at.exception
    assert len(at.radio) == 1
    assert at.radio[0].options == ["損保更改", "損保新規", "生保新規", "生保アフター", "苦情対応"]


def test_transcript_normalization_button_updates_widget_state():
    at = open_app()
    at.text_area[0].set_value("じゅうせつを実施")
    next(button for button in at.button if button.label == "表記ゆれ補正・番号整形").click()
    at.run()
    assert not at.exception
    assert at.text_area[0].value == "重要事項説明を実施"


def test_transcript_normalization_formats_numbered_sections():
    at = open_app()
    at.text_area[0].set_value("1.自動車、9月30日、対面\n2.変化なし")
    next(button for button in at.button if button.label == "表記ゆれ補正・番号整形").click()
    at.run()
    assert not at.exception
    assert "1." in at.text_area[0].value
    assert "・自動車" in at.text_area[0].value
    assert "2." in at.text_area[0].value
    assert "・変化なし" in at.text_area[0].value
    assert "【" not in at.text_area[0].value


def test_generate_report_button_does_not_raise():
    at = open_app()
    at.text_area[0].set_value("1.自動車、9月30日、対面\n2.変化なし\n3.実施済\n4.該当なし")
    next(button for button in at.button if button.label == "日報テンプレートを生成").click()
    at.run()
    assert not at.exception
    assert at.text_area[1].value
    assert "損保更改" in at.text_area[1].value or "対象種目" in at.text_area[1].value


def test_demo_button_fills_and_generates():
    at = open_app()
    next(button for button in at.button if button.label == "発表用デモを入力して生成").click()
    at.run()
    assert "自動車" in at.session_state.raw_speech
    assert "対象種目" in at.session_state.editable_output
    assert "山田" not in at.session_state.editable_output
