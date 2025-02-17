import pytest
import os
from speech_gateway.source.nijivoice_encoded import NijiVoiceEncodedStreamSource

BASE_URL = "https://api.nijivoice.com"
GATEWAY_BASE_URL = "http://127.0.0.1:8000/nijivoice"
NIJIVOICE_API_KEY = os.getenv("NIJIVOICE_API_KEY")
VOICE_ACTOR_ID = "a192db5f-bd8b-4fc7-bc08-af5ca5957c12"
PAYLOAD = {
    "script": "こんにちは。これはテストです。",
    "speed": "1.0",
    "emotionalLevel": "0.1",
    "soundDuration": "0.1",
    "format": "mp3",
}


@pytest.fixture
def source():
    # Create an instance of NijiVoiceEncodedStreamSource
    return NijiVoiceEncodedStreamSource(base_url=BASE_URL, api_key=NIJIVOICE_API_KEY, debug=True)

@pytest.mark.asyncio
async def test_get_cache_key(source):
    # Test get_cache_key method
    cache_key = source.get_cache_key("mp3", VOICE_ACTOR_ID, PAYLOAD)
    assert cache_key.endswith(".mp3.json")
    assert VOICE_ACTOR_ID in cache_key

    cache_key = source.get_cache_key("wav", VOICE_ACTOR_ID, PAYLOAD)
    assert cache_key.endswith(".wav.json")
    assert VOICE_ACTOR_ID in cache_key

@pytest.mark.asyncio
async def test_parse_text(source):
    # Test parse_text method
    text = source.parse_text(request_json=PAYLOAD)
    assert text == PAYLOAD["script"]

@pytest.mark.asyncio
async def test_make_stream_request(source):
    # Test make_stream_request method
    request = source.make_stream_request(VOICE_ACTOR_ID, PAYLOAD)
    assert request["method"] == "POST"
    assert request["url"] == f"{BASE_URL}/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-encoded-voice"
    assert request["headers"]["x-api-key"] == NIJIVOICE_API_KEY
    assert request["json"] == PAYLOAD

@pytest.mark.asyncio
async def test_fetch_stream_raw(source):
    # Test fetch_stream_raw with a real request (ensure server is running locally)
    http_request = source.make_stream_request(VOICE_ACTOR_ID, PAYLOAD)

    try:
        # Replace this part with a live test against the actual service
        async for chunk in source.fetch_stream_raw(http_request):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream_raw failed: {e}")

@pytest.mark.asyncio
async def test_fetch_stream(source):
    # Test fetch_stream method with conversion and caching
    try:
        async for chunk in await source.fetch_stream(
            audio_format="mp3",
            voice_actor_id=VOICE_ACTOR_ID,
            request_json=PAYLOAD,
        ):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream failed: {e}")
