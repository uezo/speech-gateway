import pytest
from speech_gateway.source.sbv2 import StyleBertVits2StreamSource

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture
def source():
    # Create an instance of StyleBertVits2StreamSource
    return StyleBertVits2StreamSource(base_url=BASE_URL)

@pytest.mark.asyncio
async def test_get_cache_key(source):
    # Test get_cache_key method
    query_params = {"text": "こんにちは。これはテストです。", "voice": "test"}
    cache_key = source.get_cache_key("mp3", query_params)
    assert cache_key.endswith(".mp3")

    cache_key = source.get_cache_key("wav", query_params)
    assert cache_key.endswith(".wav")

@pytest.mark.asyncio
async def test_parse_text(source):
    # Test parse_text method
    query_params = {"text": "こんにちは。これはテストです。", "voice": "test"}
    text = source.parse_text(query_params)
    assert text == "こんにちは。これはテストです。"

@pytest.mark.asyncio
async def test_make_stream_request(source):
    # Test make_stream_request method
    query_params = {"text": "こんにちは。これはテストです。", "voice": "test"}
    request = source.make_stream_request(query_params)
    assert request["method"] == "GET"
    assert request["url"] == f"{BASE_URL}/voice"
    assert request["params"] == query_params

@pytest.mark.asyncio
async def test_fetch_stream_raw(source):
    # Test fetch_stream_raw with a real request (ensure server is running locally)
    query_params = {"text": "こんにちは。これはテストです。", "voice": "test"}
    http_request = source.make_stream_request(query_params)

    try:
        # Replace this part with a live test against the actual service
        async for chunk in source.fetch_stream_raw(http_request):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream_raw failed: {e}")

@pytest.mark.asyncio
async def test_fetch_stream(source):
    # Test fetch_stream method with conversion and caching
    query_params = {"text": "こんにちは。", "voice": "test"}
    audio_format = "mp3"

    try:
        async for chunk in await source.fetch_stream(audio_format, query_params=query_params):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream failed: {e}")
