import os
import pytest
import httpx

AIVIS_MODEL_UUID = os.getenv("AIVIS_MODEL_UUID", "test-model-uuid")
AIVIS_API_KEY = os.getenv("AIVIS_API_KEY")


@pytest.mark.asyncio
async def test_aivis(random_text, wave_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/aivis/tts/synthesize",
        headers={"Authorization": f"Bearer {AIVIS_API_KEY}"},
        json={
            "model_uuid": AIVIS_MODEL_UUID,
            "text": random_text,
            "output_format": "wav",
            "output_sampling_rate": 8000,
            "output_audio_channels": "mono",
            "use_ssml": False,
        }
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    text = audio_transcriber(audio_data, "wav")
    assert "音声合成" in text


@pytest.mark.asyncio
async def test_aivis_with_speed(random_text, wave_checker, audio_transcriber):
    resp = httpx.post(
        "http://127.0.0.1:8000/aivis/tts/synthesize",
        headers={"Authorization": f"Bearer {AIVIS_API_KEY}"},
        json={
            "model_uuid": AIVIS_MODEL_UUID,
            "text": random_text,
            "output_format": "wav",
            "output_sampling_rate": 8000,
            "output_audio_channels": "mono",
            "use_ssml": False,
            "speaking_rate": 1.2,
        }
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    text = audio_transcriber(audio_data, "wav")
    assert "音声合成" in text


@pytest.mark.asyncio
async def test_aivis_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": AIVIS_MODEL_UUID,
        "service_name": "aivis"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    text = audio_transcriber(audio_data, "wav")
    assert "音声合成" in text


@pytest.mark.asyncio
async def test_aivis_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": AIVIS_MODEL_UUID,
        "service_name": "aivis",
        "audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    text = audio_transcriber(audio_data, "wav")
    assert "音声合成" in text


@pytest.mark.asyncio
async def test_aivis_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": AIVIS_MODEL_UUID,
        "service_name": "aivis",
        "audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    is_mp3 = mp3_checker(audio_data)
    assert is_mp3
    text = audio_transcriber(audio_data, "mp3")
    assert "音声合成" in text


@pytest.mark.asyncio
async def test_aivis_unified_with_speed(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": AIVIS_MODEL_UUID,
        "service_name": "aivis",
        "speed": 1.2
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    text = audio_transcriber(audio_data, "wav")
    assert "音声合成" in text
