"""日報らくらくサポートくん - Streamlit UI。"""

from __future__ import annotations

import json

import speech_recognition as sr
import streamlit as st
from st_copy import copy_button

from rakusapo.common.demo import DEMO_INPUTS
from rakusapo.common.registry import REPORT_TYPES, get_parser, parse_report
from rakusapo.common.storage import is_streamlit_cloud
from rakusapo.common.transcript import format_numbered_transcript
from rakusapo.common.stt import transcribe_component_payload, transcribe_japanese
from rakusapo.common.terms import (
    add_term,
    apply_learned_terms,
    delete_term,
    export_terms_json,
    import_terms_json,
    load_custom_terms,
    update_term,
)
from rakusapo.components.audio_capture import audio_capture

st.set_page_config(
    page_title="日報らくらくサポートくん (らくサポ)",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    .stApp {background:radial-gradient(circle at 10% 0%,rgba(219,234,254,.75),transparent 32rem),#F5F7FB}
    .block-container {max-width:1500px;padding-top:1.4rem;padding-bottom:3rem}
    .hero-shell {background:linear-gradient(120deg,#163B72,#2463A8);border-radius:18px;
      padding:24px 30px 22px;margin-bottom:20px;box-shadow:0 14px 34px rgba(22,59,114,.18)}
    .eyebrow {color:#BFDBFE;font-size:.95rem;font-weight:700;letter-spacing:.1em;margin-bottom:7px}
    .main-title {font-size:2rem;font-weight:800;color:white;line-height:1.25;margin-bottom:5px}
    .sub-title {font-size:.98rem;color:#DBEAFE;margin:0}
    textarea {border-radius:10px!important;border-color:#CBD5E1!important;background:#FBFDFF!important}
    .stButton>button,.stDownloadButton>button {border-radius:9px;font-weight:650}
    div[data-testid="stExpander"] {border-color:#E2E8F0;border-radius:10px;background:rgba(255,255,255,.7)}
    .warning-badge {background:#FEE2E2;color:#991B1B;padding:7px 13px;border-radius:999px;
      font-size:.9rem;font-weight:bold;display:inline-block;margin-bottom:10px}
    .success-badge {background:#D1FAE5;color:#065F46;padding:7px 13px;border-radius:999px;
      font-size:.9rem;font-weight:bold;display:inline-block;margin-bottom:10px}
    @media(max-width:700px){.hero-shell{padding:20px;border-radius:14px}.main-title{font-size:1.55rem}}
    </style>
    <div class="hero-shell">
      <div class="eyebrow">あおぞら保険サービス ／ AIドリブンスクール卒業制作</div>
      <div class="main-title">日報らくらくサポートくん</div>
      <div class="sub-title">話した内容を整理して、確認・コピーまでをひとつの画面で。日報本文は保存しません。</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "raw_speech" not in st.session_state:
    st.session_state.raw_speech = ""
if "selected_temp" not in st.session_state:
    st.session_state.selected_temp = REPORT_TYPES[0]
if "editable_output" not in st.session_state:
    st.session_state.editable_output = ""
if "last_audio_digest" not in st.session_state:
    st.session_state.last_audio_digest = ""
if "number_warnings" not in st.session_state:
    st.session_state.number_warnings = []
if "capture_version" not in st.session_state:
    st.session_state.capture_version = 0
if "generate_warning" not in st.session_state:
    st.session_state.generate_warning = False
if st.session_state.selected_temp not in REPORT_TYPES:
    st.session_state.selected_temp = REPORT_TYPES[0]


def clear_report() -> None:
    st.session_state.raw_speech = ""
    st.session_state.editable_output = ""
    st.session_state.number_warnings = []
    st.session_state.last_audio_digest = ""
    st.session_state.capture_version += 1


def append_transcript(spoken: str) -> None:
    corrected = apply_learned_terms(spoken, count_usage=True)
    formatted = format_numbered_transcript(corrected)
    separator = "\n\n" if st.session_state.raw_speech.strip() else ""
    combined = (st.session_state.raw_speech + separator + formatted).strip()
    st.session_state.raw_speech = format_numbered_transcript(combined)


def handle_transcription(spoken: str, digest: str) -> None:
    st.session_state.last_audio_digest = digest
    if spoken:
        append_transcript(spoken)
        st.session_state.capture_version += 1
        st.rerun()


def transcribe_safely(runner) -> str:
    try:
        return runner()
    except sr.UnknownValueError:
        st.warning("音声を認識できませんでした。もう一度録音するか、下に直接入力してください。")
    except sr.RequestError:
        st.error("文字変換サービスに接続できませんでした。少し待って再試行するか、下に直接入力してください。")
    except Exception as exc:  # noqa: BLE001 - 端末差のある音声エラーを画面へ出す
        st.error(f"音声の変換に失敗しました: {exc}")
    return ""


def normalize_transcript() -> None:
    corrected = apply_learned_terms(
        st.session_state.raw_speech,
        count_usage=True,
    )
    st.session_state.raw_speech = format_numbered_transcript(corrected)


def generate_report() -> None:
    text = st.session_state.get("raw_speech", "")
    if not str(text).strip():
        st.session_state.generate_warning = True
        st.session_state.number_warnings = []
        st.session_state.editable_output = ""
        return
    st.session_state.generate_warning = False
    corrected = format_numbered_transcript(
        apply_learned_terms(str(text), count_usage=True)
    )
    st.session_state.raw_speech = corrected
    validation = get_parser(st.session_state.selected_temp).validate(corrected)
    st.session_state.number_warnings = validation.messages()
    st.session_state.editable_output = parse_report(
        corrected,
        st.session_state.selected_temp,
    )


def load_demo() -> None:
    kind = st.session_state.selected_temp
    st.session_state.raw_speech = DEMO_INPUTS[kind]
    generate_report()


left, right = st.columns([1.1, 1.0])
with left:
    st.subheader("1. 日報の種類を選ぶ")
    selected = st.radio(
        "作成する日報テンプレート：",
        REPORT_TYPES,
        horizontal=True,
        index=REPORT_TYPES.index(st.session_state.selected_temp),
    )
    st.session_state.selected_temp = selected
    st.button(
        "発表用デモを入力して生成",
        use_container_width=True,
        on_click=load_demo,
    )
    st.caption("審査・発表用の架空データです。実在の顧客情報は含みません。")
    with st.expander("番号入力の例", expanded=False):
        st.markdown(
            "テンプレートのどの項目を話すかの目安です。\n\n"
            + get_parser(selected).guide.replace("\n", "  \n")
        )

    st.subheader("2. 話す、または入力する")
    st.caption(
        "iPhone は下の青い「録音を開始」を使ってください。"
        "許可を求められたら「許可」を選びます。日報本文は保存しません。"
    )
    captured = audio_capture(key=f"ios_capture_{st.session_state.capture_version}")
    if isinstance(captured, dict) and captured.get("data"):
        digest = str(hash(captured.get("data")))
        if digest != st.session_state.last_audio_digest:
            with st.spinner("音声を文字に変換しています…"):
                spoken = transcribe_safely(lambda: transcribe_component_payload(captured))
            handle_transcription(spoken, digest)

    with st.expander("パソコン用マイク（または別の録音方法）"):
        audio = st.audio_input(
            "マイクで録音",
            sample_rate=None,
            key=f"voice_input_{st.session_state.capture_version}",
            help="録音開始→話して→停止。",
        )
        if audio is not None:
            digest = str(hash(audio.getvalue()))
            if digest != st.session_state.last_audio_digest:
                with st.spinner("音声を文字に変換しています…"):
                    spoken = transcribe_safely(lambda: transcribe_japanese(audio))
                handle_transcription(spoken, digest)
        uploaded = st.file_uploader(
            "音声ファイルをアップロード",
            type=["wav", "mp3", "m4a", "aac", "caf", "ogg", "webm", "mp4"],
            key=f"audio_upload_{st.session_state.capture_version}",
        )
        if uploaded is not None:
            digest = str(hash(uploaded.getvalue()))
            if digest != st.session_state.last_audio_digest:
                with st.spinner("音声を文字に変換しています…"):
                    spoken = transcribe_safely(lambda: transcribe_japanese(uploaded))
                handle_transcription(spoken, digest)

    st.text_area(
        "音声文字起こしテキスト",
        key="raw_speech",
        height=220,
        placeholder="録音するか、ここに直接入力してください。",
    )
    action, clear = st.columns([2, 1])
    action.button(
        "表記ゆれ補正・番号整形",
        on_click=normalize_transcript,
        use_container_width=True,
    )
    clear.button("クリア", on_click=clear_report, use_container_width=True)
    st.button(
        "日報テンプレートを生成",
        type="primary",
        use_container_width=True,
        on_click=generate_report,
    )
    if st.session_state.get("generate_warning"):
        st.warning("音声またはテキストを入力してください。")
        st.session_state.generate_warning = False

with right:
    st.subheader("3. 内容を確認してコピーする")
    st.caption("生成後も直接修正できます。コピーして日報へ貼り付けてください。")
    for warning in st.session_state.number_warnings:
        st.warning(f"{warning}（生成は完了しています。内容を確認してください）")
    if st.session_state.editable_output:
        missing = st.session_state.editable_output.count("【要入力")
        badge = (
            f'<div class="warning-badge">要確認項目が {missing} 件あります</div>'
            if missing
            else '<div class="success-badge">必須項目が入力されています。内容を最終確認してください</div>'
        )
        st.markdown(badge, unsafe_allow_html=True)
        st.text_area("生成された日報テキスト", height=430, key="editable_output")
        copied = copy_button(
            st.session_state.editable_output,
            icon="st",
            tooltip="クリップボードへコピー",
            copied_label="コピーしました",
            key="copy_report",
        )
        if copied is False:
            st.warning("コピーできない場合は、テキスト欄から選択してコピーしてください。")
        st.download_button(
            "テキストファイルとして保存",
            st.session_state.editable_output,
            "らくサポ日報.txt",
            "text/plain",
            use_container_width=True,
        )
    else:
        st.info("左側で入力後、「日報テンプレートを生成」を押してください。")

st.divider()
with st.expander("よく使う用語"):
    if is_streamlit_cloud():
        st.caption("この画面を開いているあいだだけ覚えます。共有しません。顧客名は登録しないでください。")
    else:
        st.caption("このパソコンにだけ覚えます。顧客名は登録しないでください。追加・編集・削除ができます。")
    with st.form("term_form", clear_on_submit=True):
        first, second = st.columns(2)
        heard = first.text_input("認識される表記", placeholder="例：じゅうせつ")
        correct = second.text_input("正しい表記", placeholder="例：重要事項説明")
        add = st.form_submit_button("この用語を覚える", use_container_width=True)
    if add:
        if not heard.strip() or not correct.strip() or heard.strip() == correct.strip():
            st.error("異なる2つの表記を入力してください。")
        else:
            add_term(heard.strip(), correct.strip())
            st.success("用語を覚えました。")
    uploaded = st.file_uploader("用語ファイルを読み込む", type=["json"])
    if uploaded and st.button("読み込む"):
        try:
            count = import_terms_json(uploaded.getvalue())
            st.success(f"{count} 件を読み込みました。")
        except (ValueError, json.JSONDecodeError, UnicodeError) as exc:
            st.error(f"読み込めません: {exc}")
    st.download_button(
        "用語ファイルを保存",
        export_terms_json(),
        "rakusapo_terms.json",
        "application/json",
    )
    custom_terms = load_custom_terms()
    if not custom_terms:
        st.caption("まだ追加した用語はありません。")
    else:
        st.markdown("#### 登録済み用語の編集・削除")
        for index, (source, data) in enumerate(
            sorted(
                custom_terms.items(),
                key=lambda item: item[1].get("uses", 0) if isinstance(item[1], dict) else 0,
                reverse=True,
            )
        ):
            replacement = data.get("replacement", "") if isinstance(data, dict) else str(data)
            uses = data.get("uses", 0) if isinstance(data, dict) else 0
            row = st.columns([2.2, 2.2, 1, 1])
            new_source = row[0].text_input(
                "認識される表記",
                value=source,
                key=f"term_source_{index}",
                label_visibility="collapsed",
            )
            new_replacement = row[1].text_input(
                "正しい表記",
                value=replacement,
                key=f"term_replacement_{index}",
                label_visibility="collapsed",
            )
            if row[2].button("更新", key=f"term_update_{index}", use_container_width=True):
                try:
                    update_term(source, new_replacement, new_source=new_source)
                    st.success(f"「{source}」を更新しました。")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if row[3].button("削除", key=f"term_delete_{index}", use_container_width=True):
                delete_term(source)
                st.success(f"「{source}」を削除しました。")
                st.rerun()
            st.caption(f"「{source}」→「{replacement}」（変換 {uses} 回）")

st.caption(
    "AIドリブンスクール 卒業制作 ｜ "
    "[ソースコード](https://github.com/yoneken5/rakusapo) ｜ "
    "日報本文は保存しません。公開デモでは個人情報を入力しないでください。"
)
