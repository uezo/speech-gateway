import pytest
import os
import httpx
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway.sbv2 import StyleBertVits2Gateway
from speech_gateway.gateway.openai_speech import OpenAIGateway
from speech_gateway.gateway.unified import UnifiedGateway
from speech_gateway.gateway import UnifiedTTSRequest

VOICEVOX_URL = os.getenv("VOICEVOX_URL")
SBV2_URL = os.getenv("SBV2_URL")
NIJIVOICE_API_KEY = os.getenv("NIJIVOICE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@pytest.mark.asyncio
async def test_unified_gateway_default():
    # Create gateways
    voicevox_gateway = VoicevoxGateway(base_url=VOICEVOX_URL, debug=True)
    sbv2_gateway = StyleBertVits2Gateway(base_url=SBV2_URL, debug=True)
    openai_gateway = OpenAIGateway(api_key=OPENAI_API_KEY, debug=True)

    # Unified gateway
    unified_gateway = UnifiedGateway(debug=True)
    unified_gateway.add_gateway("voicevox", voicevox_gateway, default_speaker="46", default=True)
    unified_gateway.add_gateway("sbv2", sbv2_gateway)
    unified_gateway.add_gateway("openai", openai_gateway, languages=["en-US", "zh-CN"], default_speaker="alloy")

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello")) == voicevox_gateway

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="voicevox")) == voicevox_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="sbv2")) == sbv2_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="openai")) == openai_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="dummy")) is None

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", language="ja-JP")) == voicevox_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", language="en-US")) == openai_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", language="zh-CN")) == openai_gateway

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="sbv2", language="en-US")) == sbv2_gateway



@pytest.mark.asyncio
async def test_voicevox_unified(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert wave_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "wav")


@pytest.mark.asyncio
async def test_voicevox_unified_wav(random_text, wave_checker, audio_transcriber):
    req = {
        "text": random_text,
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
        "audio_format": "mp3"
    }
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    audio_data = resp.content
    assert mp3_checker(audio_data)
    assert "音声合成" in audio_transcriber(audio_data, "mp3")


# SDK mode tests (direct tts method call)
@pytest.mark.asyncio
async def test_unified_gateway_tts_sdk(random_text, wave_checker, audio_transcriber):
    voicevox_gateway = VoicevoxGateway(base_url=VOICEVOX_URL, cache_dir=None, debug=True)

    unified_gateway = UnifiedGateway(debug=True)
    unified_gateway.add_gateway("voicevox", voicevox_gateway, default_speaker="46", default=True)

    try:
        response = await unified_gateway.tts(UnifiedTTSRequest(text=random_text))
        assert wave_checker(response.audio_data)
        assert "音声合成" in audio_transcriber(response.audio_data, "wav")
    finally:
        await unified_gateway.shutdown()


@pytest.mark.asyncio
async def test_voicevox_gateway_tts_sdk(random_text, wave_checker, audio_transcriber):
    voicevox_gateway = VoicevoxGateway(base_url=VOICEVOX_URL, cache_dir=None, debug=True)

    try:
        response = await voicevox_gateway.tts(UnifiedTTSRequest(text=random_text, speaker="46"))
        assert wave_checker(response.audio_data)
        assert "音声合成" in audio_transcriber(response.audio_data, "wav")
    finally:
        await voicevox_gateway.shutdown()


@pytest.mark.asyncio
async def test_voicevox_gateway_tts_sdk_mp3(random_text, mp3_checker, audio_transcriber):
    voicevox_gateway = VoicevoxGateway(base_url=VOICEVOX_URL, cache_dir=None, debug=True)

    try:
        response = await voicevox_gateway.tts(UnifiedTTSRequest(text=random_text, speaker="46", audio_format="mp3"))
        assert mp3_checker(response.audio_data)
        assert "音声合成" in audio_transcriber(response.audio_data, "mp3")
    finally:
        await voicevox_gateway.shutdown()
