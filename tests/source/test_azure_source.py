import pytest
import os
from speech_gateway.source.azure import AzureStreamSource

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")


@pytest.fixture
def source():
    # Create an instance of Azure Speech
    return AzureStreamSource(api_key=AZURE_API_KEY, region=AZURE_REGION)

@pytest.mark.asyncio
async def test_get_cache_key(source):
    cache_key = source.get_cache_key("mp3", b"dummy")
    assert cache_key.endswith(".mp3")

    cache_key = source.get_cache_key("wav", b"dummy")
    assert cache_key.endswith(".wav")

@pytest.mark.asyncio
async def test_parse_text(source):
    text = source.parse_text(encoded_ssml=b"dummy")
    assert text == "dummy"

@pytest.mark.asyncio
async def test_make_stream_request(source):
    # Test make_stream_request method
    request = source.make_stream_request(encoded_ssml=b"dummy", azure_audio_format="dummy_mp3")
    assert request["method"] == "POST"
    assert request["url"] == f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    assert request["headers"]["X-Microsoft-OutputFormat"] == "dummy_mp3"
    assert request["headers"]["Content-Type"] == "application/ssml+xml"
    assert request["headers"]["Ocp-Apim-Subscription-Key"] == source.api_key
    assert request["data"] == b"dummy"

@pytest.mark.asyncio
async def test_fetch_stream_raw(source):
    # Test fetch_stream_raw with a real request (ensure server is running locally)
    ssml_text = f"<speak version='1.0' xml:lang='ja-JP'><voice xml:lang='ja-JP' name='zh-CN-XiaoyuMultilingualNeural'>こんにちは。これは音声合成のテストです。</voice></speak>"
    http_request = source.make_stream_request(ssml_text.encode("utf-8"), "riff-16khz-16bit-mono-pcm")

    try:
        # Replace this part with a live test against the actual service
        async for chunk in source.fetch_stream_raw(http_request):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream_raw failed: {e}")

@pytest.mark.asyncio
async def test_fetch_stream(source):
    # Test fetch_stream method with conversion and caching
    ssml_text = f"<speak version='1.0' xml:lang='ja-JP'><voice xml:lang='ja-JP' name='zh-CN-XiaoyuMultilingualNeural'>こんにちは。これは音声合成のテストです。</voice></speak>"
    audio_format = "mp3"

    try:
        async for chunk in await source.fetch_stream(audio_format, azure_audio_format="audio-16khz-32kbitrate-mono-mp3", encoded_ssml=ssml_text.encode("utf-8")):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream failed: {e}")
