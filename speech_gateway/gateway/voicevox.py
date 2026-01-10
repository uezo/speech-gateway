from typing import Dict
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..converter.mp3 import MP3Converter
from ..performance_recorder import PerformanceRecorder, SQLitePerformanceRecorder
from ..source.voicevox import VoicevoxStreamSource


class VoicevoxGateway(SpeechGateway):
    def __init__(self, *, stream_source: VoicevoxStreamSource = None, base_url: str = None, cache_dir: str = None, performance_recorder: PerformanceRecorder = None, style_mapper: Dict[str, Dict[str, str]] = None, debug = False):
        self.stream_source: VoicevoxStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=VoicevoxStreamSource(
                    base_url=base_url or "http://127.0.0.1:50021",
                    cache_storage=FileCacheStorage(cache_dir=cache_dir or "voicevox_cache"),
                    format_converters={"mp3": MP3Converter(bitrate="64k")},
                    performance_recorder=performance_recorder or SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
        self.style_mapper = style_mapper or {}

    def register_endpoint(self, router: APIRouter):
        @router.post("/synthesis")
        async def synthesis_handler(speaker: str, request: Request):
            stream_resp = await self.stream_source.fetch_stream(
                audio_format="wav",
                speaker=speaker,
                audio_query=await request.json(),
            )
            return StreamingResponse(stream_resp, media_type=f"audio/wav")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest):
        speaker = tts_request.speaker

        # Apply style
        if tts_request.style is not None and (styles_for_speaker := self.style_mapper.get(tts_request.speaker)):
            for k, v in styles_for_speaker.items():
                if k.lower() == tts_request.style.lower():
                    speaker = v
                    break

        audio_query = await self.stream_source.get_audio_query(speaker, tts_request.text)

        if tts_request.speed:
            audio_query["speedScale"] = tts_request.speed

        stream_resp = await self.stream_source.fetch_stream(
            audio_format=tts_request.audio_format,
            speaker=speaker,
            audio_query=audio_query,
        )
        return StreamingResponse(stream_resp, media_type=f"audio/{tts_request.audio_format}")
