from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from . import SpeechGateway
from ..cache.file import FileCacheStorage
from ..performance_recorder import SQLitePerformanceRecorder
from ..source.nijivoice import NijiVoiceStreamSource


class NijiVoiceGateway(SpeechGateway):
    def __init__(self, *, stream_source: NijiVoiceStreamSource = None, api_key: str = None, base_url: str = None, prefix: str = None, debug = False):
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=NijiVoiceStreamSource(
                    api_key=api_key,
                    base_url=base_url or "https://api.nijivoice.com",
                    cache_storage=FileCacheStorage(cache_dir="nijivoice_cache"),
                    performance_recorder=SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
        self.prefix = prefix

    def register_endpoint(self, router: APIRouter, stream_source: NijiVoiceStreamSource):
        @router.post("/api/platform/v1/voice-actors/{voice_actor_id}/generate-voice")
        async def generate_voice_handler(voice_actor_id: str, request: Request):
            gateway_base_url = f"{request.base_url.scheme}://{request.base_url.netloc}{self.prefix}"

            resp_json = await stream_source.generate_voice(
                voice_actor_id,
                await request.json(),
                gateway_base_url
            )

            return JSONResponse(resp_json)

        @router.get("/api/platform/v1/voice-actors/{voice_actor_id}/get-voice")
        async def get_voice_handler(voice_actor_id: str, x_audio_format: str, url: str = None, download: str = None, cache_key: str = None):
            nijivoice_resp = await stream_source.fetch_stream(
                voice_actor_id=voice_actor_id,
                url=url,
                download=download,
                cache_key=cache_key,
                audio_format=x_audio_format
            )
            return StreamingResponse(nijivoice_resp, media_type=f"audio/{x_audio_format}")
