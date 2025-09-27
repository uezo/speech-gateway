import pytest
import os
import wave
import io
from typing import AsyncIterator
from speech_gateway.converter.wave import WaveConverter, FormatConverterError


@pytest.fixture
def wave_converter():
    return WaveConverter()


@pytest.fixture
def wave_converter_custom():
    return WaveConverter(output_sample_rate=8000, output_sample_width=1)


@pytest.mark.asyncio
async def test_wave_conversion(wave_converter):
    input_file = "tests/data/test.wav"

    async def input_stream() -> AsyncIterator[bytes]:
        with open(input_file, "rb") as f:
            while chunk := f.read(1024):
                yield chunk

    output = b""
    try:
        async for chunk in wave_converter.convert(input_stream()):
            output += chunk
    except FormatConverterError as e:
        pytest.fail(f"Wave conversion failed with error: {e}")

    assert output != b""

    with wave.open(io.BytesIO(output), 'rb') as wf:
        assert wf.getframerate() == 16000
        assert wf.getsampwidth() == 2


@pytest.mark.asyncio
async def test_wave_conversion_custom_params(wave_converter_custom):
    input_file = "tests/data/test.wav"

    async def input_stream() -> AsyncIterator[bytes]:
        with open(input_file, "rb") as f:
            while chunk := f.read(1024):
                yield chunk

    output = b""
    try:
        async for chunk in wave_converter_custom.convert(input_stream()):
            output += chunk
    except FormatConverterError as e:
        pytest.fail(f"Wave conversion failed with error: {e}")

    assert output != b""

    with wave.open(io.BytesIO(output), 'rb') as wf:
        assert wf.getframerate() == 8000
        assert wf.getsampwidth() == 1


@pytest.mark.asyncio
async def test_wave_conversion_error_handling(wave_converter):
    async def input_stream() -> AsyncIterator[bytes]:
        yield b"Invalid wave data"

    with pytest.raises(FormatConverterError) as exc_info:
        async for _ in wave_converter.convert(input_stream()):
            pass

    assert "Error during Mu-Law conversion" in str(exc_info.value)


@pytest.mark.asyncio
async def test_convert_wave_bytes():
    converter = WaveConverter(output_sample_rate=8000, output_sample_width=1)

    input_io = io.BytesIO()
    with wave.open(input_io, 'wb') as wf:
        wf.setframerate(16000)
        wf.setsampwidth(2)
        wf.setnchannels(1)
        wf.writeframes(b'\x00\x00' * 1000)

    input_bytes = input_io.getvalue()
    output_bytes = converter.convert_wave_bytes(input_bytes, 8000, 1)

    assert output_bytes != b""

    with wave.open(io.BytesIO(output_bytes), 'rb') as wf:
        assert wf.getframerate() == 8000
        assert wf.getsampwidth() == 1
        assert wf.getnchannels() == 1
