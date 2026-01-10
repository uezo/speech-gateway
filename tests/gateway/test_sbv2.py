import os
import pytest
import httpx


@pytest.mark.asyncio
async def test_sbv2(random_text, wave_checker, audio_transcriber):
    query_params = {
        "text": random_text,
        "model_id": "0",
        "speaker_id": "0"
    }
    resp = httpx.get("http://127.0.0.1:8000/sbv2/voice", params=query_params)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_sbv2_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": "0-0",
        "service_name": "sbv2"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_sbv2_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": "0-0",
        "service_name": "sbv2",
        "audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_sbv2_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": "0-0",
        "service_name": "sbv2",
        "audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")
