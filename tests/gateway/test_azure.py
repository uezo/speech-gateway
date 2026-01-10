import pytest
import httpx


@pytest.mark.asyncio
async def test_azure(random_text, wave_checker, audio_transcriber):
    ssml_text = f"<speak version='1.0' xml:lang='ja-JP'><voice xml:lang='ja-JP' name='zh-CN-XiaoyuMultilingualNeural'>{random_text}</voice></speak>"
    resp = httpx.post(
        url="http://127.0.0.1:8000/azure/cognitiveservices/v1",
        headers={
            "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
            "Content-Type": "application/ssml+xml"
        },
        data=ssml_text.encode("utf-8")
    )
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_azure_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": "zh-CN-XiaoyuMultilingualNeural",
        "service_name": "azure"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_azure_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": "zh-CN-XiaoyuMultilingualNeural",
        "service_name": "azure",
        "audio_format": "wav"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_azure_unified_mp3(random_text, mp3_checker, audio_transcriber):
    req = {
        "text": random_text,
        "speaker": "zh-CN-XiaoyuMultilingualNeural",
        "service_name": "azure",
        "audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")
