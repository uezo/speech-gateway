import os
import pytest
import httpx

VOICE_ACTOR_ID = "dba2fa0e-f750-43ad-b9f6-d5aeaea7dc16"


@pytest.mark.asyncio
async def test_nijivoice(random_text, mp3_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0"
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_nijivoice_wav(random_text, wave_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0",
            "format": "wav"
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_nijivoice_mp3(random_text, mp3_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0",
            "format": "mp3"
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_nijivoice_wav_mp3(random_text, mp3_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0",
            "format": "wav"         # <- wav
        },
        params={
            "x_audio_format": "mp3"     # <- mp3
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_nijivoice_mp3_wav(random_text, wave_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0",
            "format": "mp3"         # <- mp3
        },
        params = {
            "x_audio_format": "wav"     # <- wav
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_nijivoice_x_wav(random_text, wave_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0"
        },
        params = {
            "x_audio_format": "wav"     # <- wav
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_nijivoice_x_mp3(random_text, mp3_checker, audio_transcriber):
    resp_json = httpx.post(
        f"http://127.0.0.1:8000/nijivoice/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={
            "script": random_text,
            "speed": "1.0"
        },
        params = {
            "x_audio_format": "mp3"     # <- mp3
        }
    ).json()

    resp = httpx.get(resp_json["generatedVoice"]["audioFileUrl"])
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


@pytest.mark.asyncio
async def test_nijivoice_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": VOICE_ACTOR_ID,
        "service_name": "nijivoice"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_nijivoice_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": VOICE_ACTOR_ID,
        "service_name": "nijivoice"
    }
    query_params = {
        "x_audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", params=query_params, json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_nijivoice_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": VOICE_ACTOR_ID,
        "service_name": "nijivoice"
    }
    query_params = {
        "x_audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", params=query_params, json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")
