import pytest
import httpx
from speech_gateway.source.nijivoice import NijiVoiceStreamSource
from speech_gateway.source import StreamSourceError

BASE_URL = "https://api.nijivoice.com"
GATEWAY_BASE_URL = "http://127.0.0.1:8000/nijivoice"
API_KEY = "your_api_key"
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
    # Create an instance of NijiVoiceStreamSource
    return NijiVoiceStreamSource(base_url=BASE_URL, api_key=API_KEY, debug=True)

@pytest.mark.asyncio
async def test_get_cache_key(source):
    # Test get_cache_key method
    cache_key = source.get_cache_key("mp3", VOICE_ACTOR_ID, PAYLOAD)
    assert cache_key.endswith(".mp3")
    assert VOICE_ACTOR_ID in cache_key

    cache_key = source.get_cache_key("wav", VOICE_ACTOR_ID, PAYLOAD)
    assert cache_key.endswith(".wav")
    assert VOICE_ACTOR_ID in cache_key

@pytest.mark.asyncio
async def test_parse_text(source):
    # Test parse_text method
    text = source.parse_text(payload=PAYLOAD)
    assert text is None  # Since parse_text returns None in the current implementation

@pytest.mark.asyncio
async def test_make_stream_request(source):
    # Test make_stream_request method
    url = f"{BASE_URL}/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice"
    request = source.make_stream_request(url=url)
    assert request["method"] == "GET"
    assert request["url"] == url

@pytest.mark.asyncio
async def test_generate_voice_cached(source):
    # Test generate_voice method with cache
    cache_key = source.get_cache_key("mp3", VOICE_ACTOR_ID, PAYLOAD)

    # Create a dummy async generator for cached data
    async def dummy_cache_data():
        yield b"cached data"

    # Write a dummy cache
    async for _ in source.cache_storage.write_cache(dummy_cache_data(), cache_key):
        pass  # Consume the generator to simulate writing cache

    # Call generate_voice and verify it uses cache
    response = await source.generate_voice(VOICE_ACTOR_ID, PAYLOAD, GATEWAY_BASE_URL)
    assert "generatedVoice" in response
    assert response["generatedVoice"]["audioFileUrl"].startswith(GATEWAY_BASE_URL)

@pytest.mark.asyncio
async def test_generate_voice_fresh(source):
    # Test generate_voice method without cache (actual API call)
    try:
        response = await source.generate_voice(VOICE_ACTOR_ID, PAYLOAD, GATEWAY_BASE_URL)
        assert "generatedVoice" in response
        assert response["generatedVoice"]["audioFileUrl"].startswith(GATEWAY_BASE_URL)
    except Exception as e:
        pytest.fail(f"generate_voice failed: {e}")

@pytest.mark.asyncio
async def test_generate_voice_error(source):
    # Test generate_voice method with invalid payload
    invalid_payload = PAYLOAD.copy()
    invalid_payload["script"] = ""  # Invalid script

    with pytest.raises(StreamSourceError):
        await source.generate_voice(VOICE_ACTOR_ID, invalid_payload, GATEWAY_BASE_URL)

@pytest.mark.asyncio
async def test_fetch_stream_raw(source):
    # Test fetch_stream_raw method (actual API call)
    url_resp = httpx.post(
        f"{GATEWAY_BASE_URL}/api/platform/v1/voice-actors/{VOICE_ACTOR_ID}/generate-voice",
        json={"script": "こんにちは。これはテストです。", "speed": "1.0"}
    )

    assert url_resp.status_code == 200
    url = url_resp.json()["generatedVoice"]["audioFileUrl"]
    assert GATEWAY_BASE_URL in url

    http_request = {
        "method": "GET",
        "url": url,
    }

    try:
        async for chunk in source.fetch_stream_raw(http_request):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream_raw failed: {e}")

@pytest.mark.asyncio
async def test_fetch_stream(source):
    # Test fetch_stream method with a full pipeline
    try:
        async for chunk in await source.fetch_stream(
            audio_format="mp3",
            voice_actor_id=VOICE_ACTOR_ID,
            payload=PAYLOAD,
            gateway_base_url=GATEWAY_BASE_URL,
        ):
            print(chunk)
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream failed: {e}")
