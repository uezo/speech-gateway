import os
import pytest
import httpx

SPEAKER = "alloy"


@pytest.mark.asyncio
async def test_openai_speech(random_text, mp3_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/openai/audio/speech",
        json={
            "model": "tts-1",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
        }
    )
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_openai_speech_wav(random_text, wave_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/openai/audio/speech",
        json={
            "model": "tts-1",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
            "response_format": "wav"
        }
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_openai_speech_mp3(random_text, mp3_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/openai/audio/speech",
        json={
            "model": "tts-1",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
            "response_format": "mp3"
        }
    )
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_openai_speech_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": SPEAKER,
        "service_name": "openai"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_openai_speech_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": SPEAKER,
        "service_name": "openai",
        "audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_openai_speech_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": SPEAKER,
        "service_name": "openai",
        "audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")
