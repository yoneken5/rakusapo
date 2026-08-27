"""録音音声を日本語テキストへ変換する。"""

from __future__ import annotations

import base64
import io
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO

import imageio_ffmpeg
import speech_recognition as sr

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def _suffix_from_name(name: str | None, mime: str | None) -> str:
    if name and "." in name:
        return "." + name.rsplit(".", 1)[-1].lower()
    mime = (mime or "").lower()
    if "webm" in mime:
        return ".webm"
    if "wav" in mime:
        return ".wav"
    if "mpeg" in mime or "mp3" in mime:
        return ".mp3"
    if "mp4" in mime or "m4a" in mime or "aac" in mime:
        return ".m4a"
    return ".m4a"


def _to_wav_bytes(raw: bytes, suffix: str) -> bytes:
    """任意の音声バイト列を WAV へ変換する。"""
    with tempfile.TemporaryDirectory() as tmp:
        source_path = Path(tmp) / f"input{suffix}"
        wav_path = Path(tmp) / "output.wav"
        source_path.write_bytes(raw)
        completed = subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i",
                str(source_path),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(wav_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0 or not wav_path.exists():
            detail = (completed.stderr or completed.stdout or "").strip()
            raise ValueError(f"音声形式を変換できませんでした。{detail[-300:]}")
        return wav_path.read_bytes()


def transcribe_bytes(raw: bytes, *, name: str | None = None, mime: str | None = None) -> str:
    """音声バイト列を日本語テキストに変換する。"""
    if not raw:
        raise ValueError("音声データが空です。")
    suffix = _suffix_from_name(name, mime)
    wav_bytes = raw if suffix == ".wav" else _to_wav_bytes(raw, suffix)
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
        recorded = recognizer.record(source)
    text = recognizer.recognize_google(recorded, language="ja-JP")
    return text.strip()


def transcribe_component_payload(payload: dict) -> str:
    """独自コンポーネントから受け取った payload を文字起こしする。"""
    encoded = payload.get("data")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("音声データがありません。")
    raw = base64.b64decode(encoded)
    return transcribe_bytes(
        raw,
        name=str(payload.get("name") or ""),
        mime=str(payload.get("mime") or ""),
    )


def transcribe_japanese(audio_file: BinaryIO) -> str:
    """アップロード音声を日本語テキストに変換する。"""
    audio_file.seek(0)
    raw = audio_file.read()
    name = getattr(audio_file, "name", "") or "audio.wav"
    mime = getattr(audio_file, "type", "") or ""
    return transcribe_bytes(raw, name=name, mime=mime)
