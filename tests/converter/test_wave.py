import pytest
import wave
import io
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

    with open(input_file, "rb") as f:
        output = await wave_converter.convert(f.read())
        # Assert that the output is not empty (indicating conversion occurred)
        assert output != b""

    with wave.open(io.BytesIO(output), 'rb') as wf:
        assert wf.getframerate() == 16000
        assert wf.getsampwidth() == 2

@pytest.mark.asyncio
async def test_wave_conversion_custom_params(wave_converter_custom):
    input_file = "tests/data/test.wav"

    with open(input_file, "rb") as f:
        output = await wave_converter_custom.convert(f.read())
        # Assert that the output is not empty (indicating conversion occurred)
        assert output != b""

    with wave.open(io.BytesIO(output), 'rb') as wf:
        assert wf.getframerate() == 8000
        assert wf.getsampwidth() == 1


@pytest.mark.asyncio
async def test_wave_conversion_error_handling(wave_converter):
    with pytest.raises(FormatConverterError) as exc_info:
        output = await wave_converter.convert(b"invalid data")
        # Assert that the output is not empty (indicating conversion occurred)
        assert output != b""


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
