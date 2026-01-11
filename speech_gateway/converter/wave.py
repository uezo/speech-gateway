import audioop
import io
import wave
from . import FormatConverter, FormatConverterError


class WaveConverter(FormatConverter):
    def __init__(self, output_sample_rate: int = 16000, output_sample_width: int = 2):
        self.output_sample_rate = output_sample_rate
        self.output_sample_width = output_sample_width

    def convert_wave_bytes(self, input_bytes, output_sample_rate, output_sample_width):
        input_io = io.BytesIO(input_bytes)
        with wave.open(input_io, 'rb') as wf:
            input_sample_rate = wf.getframerate()
            input_sample_width = wf.getsampwidth()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
        
        # Convert sample rate
        if input_sample_rate != output_sample_rate:
            frames, _ = audioop.ratecv(frames, input_sample_width, channels, input_sample_rate, output_sample_rate, None)
        
        # Convert sample width
        if input_sample_width != output_sample_width:
            # 16 -> 8
            if input_sample_width == 2 and output_sample_width == 1:
                frames = audioop.lin2lin(frames, 2, 1)
                frames = audioop.bias(frames, 1, 128)
            # 8 -> 16
            elif input_sample_width == 1 and output_sample_width == 2:
                frames = audioop.bias(frames, 1, -128)
                frames = audioop.lin2lin(frames, 1, 2)
            else:
                frames = audioop.lin2lin(frames, input_sample_width, output_sample_width)
        
        output_io = io.BytesIO()
        with wave.open(output_io, "wb") as wf_out:
            wf_out.setframerate(output_sample_rate)
            wf_out.setsampwidth(output_sample_width)
            wf_out.setnchannels(channels)
            wf_out.writeframes(frames)

        return output_io.getvalue()

    async def convert(self, input_bytes: bytes) -> bytes:
        try:
            return self.convert_wave_bytes(input_bytes, self.output_sample_rate, self.output_sample_width)

        except Exception as ex:
            raise FormatConverterError(f"Error during Wave conversion: {str(ex)}")
