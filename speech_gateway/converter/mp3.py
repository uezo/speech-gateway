import asyncio
from . import FormatConverter, FormatConverterError


class MP3Converter(FormatConverter):
    def __init__(self, ffmpeg_path: str = "ffmpeg", bitrate: str = "64k", output_chunksize: int = 1024):
        self.ffmpeg_path = ffmpeg_path
        self.bitrate = bitrate
        self.output_chunksize = output_chunksize

    async def convert(self, input_bytes: bytes) -> bytes:
        try:
            ffmpeg_proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path,
                "-y",
                "-i", "-",  # Read from stdin
                "-f", "mp3",
                "-b:a", self.bitrate,
                "-",  # Write to stdout
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await ffmpeg_proc.communicate(input=input_bytes)

            if ffmpeg_proc.returncode != 0:
                raise FormatConverterError(f"FFmpeg conversion error: {stderr.decode('utf-8')}")

            return stdout

        except FormatConverterError:
            raise
        except Exception as ex:
            raise FormatConverterError(f"Error during MP3 conversion: {str(ex)}")
