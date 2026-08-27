"""録音音声を日本語テキストへ変換する。"""

from __future__ import annotations

from typing import BinaryIO

import speech_recognition as sr


def transcribe_japanese(audio_file: BinaryIO) -> str:
    """WAV などの音声ファイルを日本語テキストに変換する。"""
    audio_file.seek(0)
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        recorded = recognizer.record(source)
    text = recognizer.recognize_google(recorded, language="ja-JP")
    return text.strip()
