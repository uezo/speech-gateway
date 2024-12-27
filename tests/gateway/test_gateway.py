import pytest
import httpx


@pytest.mark.asyncio
async def test_unified_gateway_default():
    req = {"text": "こんにちは。これは統合インターフェイスのテストです。", "speaker": "46"}
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    assert len(resp.content) > 10000

@pytest.mark.asyncio
async def test_unified_gateway_voicevox():
    req = {"text": "こんにちは。これはボイスボックスのテストです。", "speaker": "46", "service_name": "voicevox"}
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    assert len(resp.content) > 10000

@pytest.mark.asyncio
async def test_unified_gateway_sbv2():
    req = {"text": "こんにちは。これはスタイルバートヴィッツ2のテストです。", "speaker": "0-0", "service_name": "sbv2"}
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    assert len(resp.content) > 10000

@pytest.mark.asyncio
async def test_unified_gateway_nijivoice():
    req = {"text": "こんにちは。これはにじボイスのテストです。", "speaker": "a192db5f-bd8b-4fc7-bc08-af5ca5957c12", "service_name": "nijivoice"}
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    assert len(resp.content) > 10000

@pytest.mark.asyncio
async def test_unified_gateway_openai():
    req = {"text": "こんにちは。これはOpenAIのテストです。", "speaker": "alloy", "service_name": "openai"}
    resp = httpx.post("http://127.0.0.1:8000/tts", json=req)
    assert len(resp.content) > 10000
