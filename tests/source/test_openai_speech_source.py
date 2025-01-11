import pytest
import os
from speech_gateway.source.openai_speech import OpenAIStreamSource

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@pytest.fixture
def source():
    # Create an instance of OpenAIStreamSource
    return OpenAIStreamSource(api_key=OPENAI_API_KEY)

@pytest.mark.asyncio
async def test_get_cache_key(source):
    # Test get_cache_key method
    request_json = {
        "model": "tts-1",
        "voice": "alloy",
        "input": "こんにちは。これはテストです。",
        "speed": 1.0,
        "response_format": "wav"
    }
    cache_key = source.get_cache_key("mp3", request_json)
    assert cache_key.endswith(".mp3")

    cache_key = source.get_cache_key("wav", request_json)
    assert cache_key.endswith(".wav")

@pytest.mark.asyncio
async def test_parse_text(source):
    # Test parse_text method
    request_json = {
        "model": "tts-1",
        "voice": "alloy",
        "input": "こんにちは。これはテストです。",
        "speed": 1.0,
        "response_format": "wav"
    }
    text = source.parse_text(request_json)
    assert text == "こんにちは。これはテストです。"

@pytest.mark.asyncio
async def test_make_stream_request(source):
    # Test make_stream_request method
    request_json = {
        "model": "tts-1",
        "voice": "alloy",
        "input": "こんにちは。これはテストです。",
        "speed": 1.0,
        "response_format": "wav"
    }
    request = source.make_stream_request(request_json)
    assert request["method"] == "POST"
    assert request["url"] == "https://api.openai.com/v1/audio/speech"
    assert request["json"] == request_json

@pytest.mark.asyncio
async def test_fetch_stream_raw(source):
    # Test fetch_stream_raw with a real request (ensure server is running locally)
    request_json = {
        "model": "tts-1",
        "voice": "alloy",
        "input": "こんにちは。これはテストです。",
        "speed": 1.0,
        "response_format": "wav"
    }
    http_request = source.make_stream_request(request_json)

    try:
        async for chunk in source.fetch_stream_raw(http_request):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream_raw failed: {e}")

@pytest.mark.asyncio
async def test_fetch_stream(source):
    # Test fetch_stream method with conversion and caching
    request_json = {
        "model": "tts-1",
        "voice": "alloy",
        "input": "こんにちは。これはテストです。",
        "speed": 1.0,
        "response_format": "wav"
    }

    audio_format = "wav"

    try:
        async for chunk in await source.fetch_stream(audio_format, request_json=request_json):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream failed: {e}")
