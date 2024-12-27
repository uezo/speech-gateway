import pytest
import os
from speech_gateway.source.voicevox import VoicevoxStreamSource

VOICEVOX_URL = os.getenv("VOICEVOX_URL")
SPEAKER = "2"

@pytest.fixture
def source():
    # Create an instance of VoicevoxStreamSource
    return VoicevoxStreamSource(base_url=VOICEVOX_URL)

@pytest.fixture
def audio_query():
    # Provide the audio_query data
    return {
        "accent_phrases": [
            {
                "moras": [
                    {"text": "コ", "consonant": "k", "consonant_length": 0, "vowel": "o", "vowel_length": 0, "pitch": 0},
                    {"text": "ン", "consonant": None, "consonant_length": None, "vowel": "N", "vowel_length": 0, "pitch": 0},
                    {"text": "ニ", "consonant": "n", "consonant_length": 0, "vowel": "i", "vowel_length": 0, "pitch": 0},
                    {"text": "チ", "consonant": "ch", "consonant_length": 0, "vowel": "i", "vowel_length": 0, "pitch": 0},
                    {"text": "ワ", "consonant": "w", "consonant_length": 0, "vowel": "a", "vowel_length": 0, "pitch": 0},
                    {"text": ".", "consonant": None, "consonant_length": None, "vowel": "pau", "vowel_length": 0, "pitch": 0}
                ],
                "accent": 5,
                "pause_mora": None,
                "is_interrogative": False
            },
            {
                "moras": [
                    {"text": "コ", "consonant": "k", "consonant_length": 0, "vowel": "o", "vowel_length": 0, "pitch": 0},
                    {"text": "レ", "consonant": "r", "consonant_length": 0, "vowel": "e", "vowel_length": 0, "pitch": 0},
                    {"text": "ワ", "consonant": "w", "consonant_length": 0, "vowel": "a", "vowel_length": 0, "pitch": 0},
                    {"text": "テ", "consonant": "t", "consonant_length": 0, "vowel": "e", "vowel_length": 0, "pitch": 0},
                    {"text": "ス", "consonant": "s", "consonant_length": 0, "vowel": "u", "vowel_length": 0, "pitch": 0},
                    {"text": "ト", "consonant": "t", "consonant_length": 0, "vowel": "o", "vowel_length": 0, "pitch": 0},
                    {"text": "デ", "consonant": "d", "consonant_length": 0, "vowel": "e", "vowel_length": 0, "pitch": 0},
                    {"text": "ス", "consonant": "s", "consonant_length": 0, "vowel": "u", "vowel_length": 0, "pitch": 0},
                    {"text": ".", "consonant": None, "consonant_length": None, "vowel": "pau", "vowel_length": 0, "pitch": 0}
                ],
                "accent": 4,
                "pause_mora": None,
                "is_interrogative": False
            }
        ],
        "speedScale": 1,
        "intonationScale": 1,
        "tempoDynamicsScale": 1,
        "pitchScale": 0,
        "volumeScale": 1,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1,
        "pauseLength": None,
        "pauseLengthScale": 1,
        "outputSamplingRate": 44100,
        "outputStereo": False,
        "kana": "こんにちは。これはテストです。"
    }

@pytest.mark.asyncio
async def test_get_cache_key(source, audio_query):
    # Test get_cache_key method
    cache_key = source.get_cache_key("mp3", SPEAKER, audio_query)
    assert cache_key.endswith(".mp3")
    assert SPEAKER in cache_key

    cache_key = source.get_cache_key("wav", SPEAKER, audio_query)
    assert cache_key.endswith(".wav")
    assert SPEAKER in cache_key

@pytest.mark.asyncio
async def test_parse_text(source, audio_query):
    # Test parse_text method
    text = source.parse_text(audio_query)
    assert text == "こんにちは。これはテストです。"

@pytest.mark.asyncio
async def test_make_stream_request(source, audio_query):
    # Test make_stream_request method
    request = source.make_stream_request(SPEAKER, audio_query)
    assert request["method"] == "POST"
    assert request["url"] == f"{VOICEVOX_URL}/synthesis"
    assert request["params"] == {"speaker": SPEAKER}
    assert request["json"] == audio_query

@pytest.mark.asyncio
async def test_fetch_stream_raw(source, audio_query):
    # Test fetch_stream_raw with a real request (ensure server is running locally)
    http_request = source.make_stream_request(SPEAKER, audio_query)

    try:
        async for chunk in source.fetch_stream_raw(http_request):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream_raw failed: {e}")

@pytest.mark.asyncio
async def test_fetch_stream(source, audio_query):
    # Test fetch_stream method with conversion and caching
    audio_format = "mp3"

    try:
        async for chunk in await source.fetch_stream(audio_format, speaker=SPEAKER, audio_query=audio_query):
            assert isinstance(chunk, bytes)
    except Exception as e:
        pytest.fail(f"fetch_stream failed: {e}")
