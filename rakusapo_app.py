"""日報らくらくサポートくん - Streamlit UI。"""

from __future__ import annotations

import json

import speech_recognition as sr
import streamlit as st
from st_copy import copy_button

from rakusapo.common.registry import REPORT_TYPES, get_parser, parse_report
from rakusapo.common.stt import transcribe_japanese
from rakusapo.common.terms import (
    add_term,
    apply_learned_terms,
    export_terms_json,
    import_terms_json,
    load_custom_terms,
)

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
      <div class="eyebrow">あおぞら保険サービス</div>
      <div class="main-title">日報らくらくサポートくん</div>
      <div class="sub-title">話した内容を整理して、確認・コピーまでをひとつの画面で。</div>
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
if "audio_input_version" not in st.session_state:
    st.session_state.audio_input_version = 0
if st.session_state.selected_temp not in REPORT_TYPES:
    st.session_state.selected_temp = REPORT_TYPES[0]


def clear_report() -> None:
    st.session_state.raw_speech = ""
    st.session_state.editable_output = ""
    st.session_state.number_warnings = []
    st.session_state.last_audio_digest = ""
    st.session_state.audio_input_version += 1


def normalize_transcript() -> None:
    st.session_state.raw_speech = apply_learned_terms(
        st.session_state.raw_speech,
        count_usage=True,
    )


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
    with st.expander("番号入力の例"):
        st.code(get_parser(selected).guide, language=None, wrap_lines=True)

    st.subheader("2. 話す、または入力する")
    st.caption(
        "マイクボタンで録音→停止すると文字になります。"
        "iPhone でも使えます。日報本文は保存しません。"
    )
    audio = st.audio_input(
        "マイクで録音",
        sample_rate=16000,
        key=f"voice_input_{st.session_state.audio_input_version}",
        help="録音開始→話して→停止。しばらくすると下の入力欄へ文字が入ります。",
    )
    if audio is not None:
        digest = str(hash(audio.getvalue()))
        if digest != st.session_state.last_audio_digest:
            with st.spinner("音声を文字に変換しています…"):
                try:
                    spoken = transcribe_japanese(audio)
                except sr.UnknownValueError:
                    st.warning("音声を認識できませんでした。もう一度録音するか、下に直接入力してください。")
                    spoken = ""
                except sr.RequestError:
                    st.error("文字変換サービスに接続できませんでした。少し待って再試行するか、下に直接入力してください。")
                    spoken = ""
                except Exception as exc:  # noqa: BLE001 - 端末差のある音声エラーを画面へ出す
                    st.error(f"音声の変換に失敗しました: {exc}")
                    spoken = ""
            st.session_state.last_audio_digest = digest
            if spoken:
                corrected = apply_learned_terms(spoken, count_usage=True)
                separator = "\n" if st.session_state.raw_speech.strip() else ""
                st.session_state.raw_speech += separator + corrected
                st.session_state.audio_input_version += 1
                st.rerun()

    st.text_area(
        "音声文字起こしテキスト",
        key="raw_speech",
        height=220,
        placeholder="録音するか、ここに直接入力してください。",
    )
    action, clear = st.columns([2, 1])
    action.button(
        "表記ゆれを補正",
        on_click=normalize_transcript,
        use_container_width=True,
    )
    clear.button("クリア", on_click=clear_report, use_container_width=True)
    generate = st.button("日報テンプレートを生成", type="primary", use_container_width=True)

if generate:
    if not st.session_state.raw_speech.strip():
        st.warning("音声またはテキストを入力してください。")
    else:
        corrected = apply_learned_terms(st.session_state.raw_speech, count_usage=True)
        validation = get_parser(st.session_state.selected_temp).validate(corrected)
        st.session_state.number_warnings = validation.messages()
        st.session_state.editable_output = parse_report(
            corrected,
            st.session_state.selected_temp,
        )

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
    st.caption("このパソコンにだけ覚えます。顧客名は登録しないでください。")
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
    for source, data in sorted(
        load_custom_terms().items(),
        key=lambda item: item[1].get("uses", 0) if isinstance(item[1], dict) else 0,
        reverse=True,
    ):
        st.caption(
            f"{source} → {data.get('replacement', '')}"
            f"（変換 {data.get('uses', 0)} 回）"
        )
