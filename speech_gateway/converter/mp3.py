import asyncio
from typing import AsyncIterator
from . import FormatConverter, FormatConverterError


class MP3Converter(FormatConverter):
    def __init__(self, ffmpeg_path: str = "ffmpeg", bitrate: str = "64k", output_chunksize: int = 1024):
        self.ffmpeg_path = ffmpeg_path
        self.bitrate = bitrate
        self.output_chunksize = output_chunksize

    async def convert(self, input_stream: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
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

            async def feed_ffmpeg_stdin():
                try:
                    async for chunk in input_stream:
                        ffmpeg_proc.stdin.write(chunk)
                        await ffmpeg_proc.stdin.drain()
                    ffmpeg_proc.stdin.close()

                except Exception as ex:
                    ffmpeg_proc.stdin.close()
                    raise FormatConverterError(f"Error feeding data to ffmpeg: {str(ex)}")

            asyncio.create_task(feed_ffmpeg_stdin())

            while True:
                chunk = await ffmpeg_proc.stdout.read(self.output_chunksize)
                if not chunk:
                    break
                yield chunk

            await ffmpeg_proc.wait()

            if ffmpeg_proc.returncode != 0:
                stderr = await ffmpeg_proc.stderr.read()
                raise FormatConverterError(f"FFmpeg conversion error: {stderr.decode('utf-8')}")

        except Exception as ex:
            raise FormatConverterError(f"Error during MP3 conversion: {str(ex)}")
