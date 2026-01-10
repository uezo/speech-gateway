from typing import Dict
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..converter.mp3 import MP3Converter
from ..performance_recorder import PerformanceRecorder, SQLitePerformanceRecorder
from ..source.sbv2 import StyleBertVits2StreamSource


class StyleBertVits2Gateway(SpeechGateway):
    def __init__(self, *, stream_source: StyleBertVits2StreamSource = None, base_url: str = None, cache_dir: str = None, performance_recorder: PerformanceRecorder = None, style_mapper: Dict[str, Dict[str, str]] = None, debug = False):
        self.stream_source: StyleBertVits2StreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=StyleBertVits2StreamSource(
                    base_url=base_url or "http://127.0.0.1:5000",
                    cache_storage=FileCacheStorage(cache_dir=cache_dir or "sbv2_cache"),
                    format_converters={"mp3": MP3Converter(bitrate="64k")},
                    performance_recorder=performance_recorder or SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
        self.style_mapper = style_mapper or {}

    def register_endpoint(self, router: APIRouter):
        @router.get("/voice")
        async def get_voice_handler(request: Request):
            query_params = dict(request.query_params)
            filtered_params = {
                k: v for k, v in query_params.items() if v is not None
            }

            stream_resp = await self.stream_source.fetch_stream(
                audio_format="wav",
                query_params=filtered_params,
            )
            return StreamingResponse(stream_resp, media_type=f"audio/wav")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest):
        # Basic params
        model_id, speaker_id = tts_request.speaker.split("-")
        query_params = {
            "text": tts_request.text,
            "model_id": model_id,
            "speaker_id": speaker_id
        }

        if tts_request.speed:
            query_params["length"] = 1 / tts_request.speed

        # Apply style
        if tts_request.style is not None and (styles_for_speaker := self.style_mapper.get(tts_request.speaker)):
            for k, v in styles_for_speaker.items():
                if k.lower() == tts_request.style.lower():
                    query_params["style"] = v
                    break

        # Additional params
        for k, v in dict(request.query_params).items():
            if v is not None:
                query_params[k] = v

        stream_resp = await self.stream_source.fetch_stream(
            audio_format=tts_request.audio_format,
            query_params=query_params,
        )

        return StreamingResponse(stream_resp, media_type=f"audio/{tts_request.audio_format}")
