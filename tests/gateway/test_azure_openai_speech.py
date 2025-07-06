import os
import pytest
import httpx

SPEAKER = "alloy"


@pytest.mark.asyncio
async def test_openai_speech(random_text, mp3_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
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
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
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
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
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
async def test_openai_speech_wav_mp3(random_text, mp3_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
            "response_format": "wav"    # <- wav
        },
        params={
            "x_audio_format": "mp3"     # <- mp3
        }
    )
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_openai_speech_mp3_wav(random_text, wave_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
            "response_format": "mp3"    # <- mp3
        },
        params={
            "x_audio_format": "wav"     # <- wav
        }
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_openai_speech_x_wav(random_text, wave_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
        },
        params={
            "x_audio_format": "wav"     # <- wav
        }
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_openai_speech_x_mp3(random_text, mp3_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/azure_openai/audio/speech",
        json={
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            "input": random_text,
            "speed": 1.0,
        },
        params={
            "x_audio_format": "mp3"     # <- mp3
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
        "service_name": "azure_openai"
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
        "service_name": "azure_openai"
    }
    query_params = {
        "x_audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", params=query_params, json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_openai_speech_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": SPEAKER,
        "service_name": "azure_openai"
    }
    query_params = {
        "x_audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", params=query_params, json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")
