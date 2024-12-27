import pytest
import os
from typing import AsyncIterator
from speech_gateway.converter import MP3Converter, FormatConverterError

@pytest.fixture
def mp3_converter():
    # Create an instance of MP3Converter for testing
    return MP3Converter()

@pytest.mark.asyncio
async def test_mp3_conversion(mp3_converter):
    # Test the convert method using a real WAV file
    input_file = "tests/data/test.wav"

    async def input_stream() -> AsyncIterator[bytes]:
        with open(input_file, "rb") as f:
            while chunk := f.read(1024):
                yield chunk

    output = b""
    try:
        async for chunk in mp3_converter.convert(input_stream()):
            output += chunk
    except FormatConverterError as e:
        pytest.fail(f"MP3 conversion failed with error: {e}")

    # Assert that the output is not empty (indicating conversion occurred)
    assert output != b""

@pytest.mark.asyncio
async def test_mp3_conversion_error_handling(mp3_converter):
    # Test error handling in the convert method with invalid input

    async def input_stream() -> AsyncIterator[bytes]:
        yield b"Invalid input data"

    with pytest.raises(FormatConverterError):
        async for _ in mp3_converter.convert(input_stream()):
            pass
