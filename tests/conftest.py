import os
import random
import pytest
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def make_random_text():
    random_key = "{:,}".format(random.randint(100000, 999999))
    return f"これは音声合成のテストです。ランダムキーは、{random_key}です。"


def is_wave(data: bytes) -> bool:
    if len(data) < 12:
        return False
    return data[:4] == b"RIFF" and data[8:12] == b"WAVE"


def is_mp3(data: bytes) -> bool:
    if data[:3] == b"ID3":
        id3_size = 10
        if len(data) >= 10:
            tag_size = (
                (data[6] << 21)
                | (data[7] << 14)
                | (data[8] << 7)
                | data[9]
            )
            id3_size += tag_size
        data = data[id3_size:]

    if len(data) < 2:
        return False
    # MP3 frame sync: 0xFF followed by byte with upper 3 bits set (0xE0 or higher)
    return data[0] == 0xFF and (data[1] & 0xE0) == 0xE0


def transcribe(data: bytes, audio_format: str) -> str:
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    form_data = {"model": "whisper-1"}
    files = {"file": (f"voice.{audio_format}", data, f"audio/{audio_format}")}
    resp = httpx.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers=headers,
        data=form_data,
        files=files
    )
    return resp.json().get("text")


@pytest.fixture
def random_text():
    random_key = "{:,}".format(random.randint(100000, 999999))
    return f"これは音声合成のテストです。ランダムキーは、{random_key}です。"

@pytest.fixture
def wave_checker():
    return is_wave

@pytest.fixture
def mp3_checker():
    return is_mp3

@pytest.fixture
def audio_transcriber():
    return transcribe
