import os
import pytest
import httpx

SPEAKER = 46


@pytest.mark.asyncio
async def test_voicevox(random_text, wave_checker, audio_transcriber):
    audio_query = httpx.post(
        "http://127.0.0.1:8000/voicevox/audio_query",
        params={"speaker": SPEAKER, "text": random_text}
    ).json()

    query_params = {
        "speaker": SPEAKER
    }
    resp = httpx.post(
        "http://127.0.0.1:8000/voicevox/synthesis",
        params=query_params,
        json=audio_query
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_voicevox_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": str(SPEAKER),
        "service_name": "voicevox"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_voicevox_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": str(SPEAKER),
        "service_name": "voicevox",
        "audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_voicevox_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": str(SPEAKER),
        "service_name": "voicevox",
        "audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")
