import pytest
from typing import AsyncIterator
from speech_gateway.converter import MP3Converter, FormatConverterError

@pytest.fixture
def mp3_converter():
    # Create an instance of MP3Converter for testing
    return MP3Converter()

@pytest.mark.asyncio
async def test_mp3_conversion(mp3_converter, mp3_checker):
    # Test the convert method using a real WAV file
    input_file = "tests/data/test.wav"

    with open(input_file, "rb") as f:
        output = await mp3_converter.convert(f.read())
        # Assert that the output is not empty (indicating conversion occurred)
        assert output != b""
        assert mp3_checker(output)

@pytest.mark.asyncio
async def test_mp3_conversion_error_handling(mp3_converter):
    # Test error handling in the convert method with invalid input

    with pytest.raises(FormatConverterError):
        output = await mp3_converter.convert(b"invalid data")
        # Assert that the output is not empty (indicating conversion occurred)
        assert output != b""
