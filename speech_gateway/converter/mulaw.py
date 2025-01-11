import audioop
import io
import struct
from typing import AsyncIterator
import wave
from . import FormatConverter, FormatConverterError


class MuLawConverter(FormatConverter):
    def __init__(self, rate: int = 8000, include_header: bool = False, to_linear16: callable = None):
        self.rate = rate
        self.include_header = include_header
        self.to_linear16 = to_linear16

    def create_au_header(self, data_size: int, sample_rate: int, channels: int) -> bytes:
        magic_number = b".snd"  # Magic number
        header_size = 24        # Fixed header size (24 bytes for standard .au header)
        encoding = 1            # Mu-Law encoding
        reserved = 0            # Reserved field, must be 0

        # Create header
        header = struct.pack(
            ">4sIIIIII",    # Big-endian: 4-char string, 6 unsigned integers
            magic_number,   # Magic number
            header_size,    # Header size
            data_size,      # Data size
            encoding,       # Encoding format
            sample_rate,    # Sample rate
            channels,       # Number of channels
            reserved        # Reserved field
        )
        return header

    async def convert(self, input_stream: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        try:
            # Load whole wave data
            wav_data = b""
            async for chunk in input_stream:
                wav_data += chunk

            if self.to_linear16:
                wav_data = self.to_linear16(wav_data)

            # Parse wave info
            with wave.open(io.BytesIO(wav_data), "rb") as wf:
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes   = wf.getnframes()
                raw_frames = wf.readframes(nframes)

            # Convert channel
            if nchannels > 1:
                mono_frames = audioop.tomono(raw_frames, sampwidth, 0.5, 0.5)
            else:
                mono_frames = raw_frames

            # Convert sample rate
            if framerate != self.rate:
                converted_frames, _ = audioop.ratecv(
                    mono_frames,
                    sampwidth,
                    1,
                    framerate,
                    self.rate,
                    None
                )
            else:
                converted_frames = mono_frames

            # Convert format
            mulaw_data = audioop.lin2ulaw(converted_frames, sampwidth)

            if self.include_header:
                # Create .au header
                header = self.create_au_header(len(mulaw_data), self.rate, 1)
                mulaw_data = header + mulaw_data

            # Return whole data at once
            yield mulaw_data

        except Exception as ex:
            raise FormatConverterError(f"Error during Mu-Law conversion: {str(ex)}")
