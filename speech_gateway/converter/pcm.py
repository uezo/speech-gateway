import io
import wave
import soundfile as sf
import numpy as np


def convert_float32bit_to_int16bit(input_data: bytes) -> bytes:
    data, samplerate = sf.read(io.BytesIO(input_data))
    pcm16_data = (data * 32767).astype(np.int16)
    channels = pcm16_data.shape[1] if pcm16_data.ndim > 1 else 1

    wav_bytes_io = io.BytesIO()
    with wave.open(wav_bytes_io, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(pcm16_data.tobytes())

    wav_bytes = wav_bytes_io.getvalue()
    return wav_bytes
