from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway
from ..cache.file import FileCacheStorage
from ..converter.mp3 import MP3Converter
from ..performance_recorder import SQLitePerformanceRecorder
from ..source.sbv2 import StyleBertVits2StreamSource


class StyleBertVits2Gateway(SpeechGateway):
    def __init__(self, *, stream_source: StyleBertVits2StreamSource = None, base_url: str = None, debug = False):
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=StyleBertVits2StreamSource(
                    base_url=base_url or "http://127.0.0.1:5000",
                    cache_storage=FileCacheStorage(cache_dir="sbv2_cache"),
                    format_converters={"mp3": MP3Converter(bitrate="64k")},
                    performance_recorder=SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )

    def register_endpoint(self, router: APIRouter, stream_source: StyleBertVits2StreamSource):
        @router.get("/voice")
        async def get_voice_handler(request: Request):
            query_params = dict(request.query_params)
            filtered_params = {
                k: v for k, v in query_params.items() if v is not None and k not in {"x_audio_format"}
            }
            audio_format = query_params.get("x_audio_format", "wav")

            stream_resp = await stream_source.fetch_stream(
                audio_format=audio_format,
                query_params=filtered_params,
            )
            return StreamingResponse(stream_resp, media_type=f"audio/{audio_format}")
