from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..converter.mp3 import MP3Converter
from ..performance_recorder import SQLitePerformanceRecorder
from ..source.voicevox import VoicevoxStreamSource


class VoicevoxGateway(SpeechGateway):
    def __init__(self, *, stream_source: VoicevoxStreamSource = None, base_url: str = None, debug = False):
        self.stream_source: VoicevoxStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=VoicevoxStreamSource(
                    base_url=base_url or "http://127.0.0.1:50021",
                    cache_storage=FileCacheStorage(cache_dir="voicevox_cache"),
                    format_converters={"mp3": MP3Converter(bitrate="64k")},
                    performance_recorder=SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )

    def register_endpoint(self, router: APIRouter):
        @router.post("/synthesis")
        async def synthesis_handler(speaker: str, request: Request, x_audio_format: str = "wav"):
            audio_format = "mp3" if x_audio_format == "mp3" else "wav"
            stream_resp = await self.stream_source.fetch_stream(
                audio_format=audio_format,
                speaker=speaker,
                audio_query=await request.json(),
            )
            return StreamingResponse(stream_resp, media_type=f"audio/{audio_format}")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        audio_query = await self.stream_source.get_audio_query(tts_request.speaker, tts_request.text)
        stream_resp = await self.stream_source.fetch_stream(
            audio_format=x_audio_format,
            speaker=tts_request.speaker,
            audio_query=audio_query,
        )
        return StreamingResponse(stream_resp, media_type=f"audio/{x_audio_format}")
