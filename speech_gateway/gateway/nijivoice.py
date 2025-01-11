from typing import Dict
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..performance_recorder import SQLitePerformanceRecorder
from ..source.nijivoice import NijiVoiceStreamSource


class NijiVoiceGateway(SpeechGateway):
    def __init__(self, *, stream_source: NijiVoiceStreamSource = None, api_key: str = None, speeds: Dict[str, float] = None, base_url: str = None, prefix: str = None, debug = False):
        self.stream_source: NijiVoiceStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=NijiVoiceStreamSource(
                    api_key=api_key,
                    base_url=base_url or "https://api.nijivoice.com",
                    cache_storage=FileCacheStorage(cache_dir="nijivoice_cache"),
                    format_converters={},
                    performance_recorder=SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
        self.speeds = speeds or {}
        self.prefix = prefix

    def register_endpoint(self, router: APIRouter):
        @router.post("/api/platform/v1/voice-actors/{voice_actor_id}/generate-voice")
        async def generate_voice_handler(voice_actor_id: str, request: Request, x_audio_format: str = None):
            request_json = await request.json()

            if x_audio_format:
                if x_audio_format in ["mp3", "wav"]:
                    request_json["format"] = x_audio_format
                else:
                    # Set wave to convert to other format later
                    request_json["format"] = "wav"
            else:
                x_audio_format = request_json.get("format", "mp3")

            gateway_base_url = f"{request.base_url.scheme}://{request.base_url.netloc}{self.prefix}"
            resp_json = await self.stream_source.generate_voice(
                voice_actor_id,
                request_json,
                gateway_base_url,
                x_audio_format
            )

            return JSONResponse(resp_json)

        @router.get("/api/platform/v1/voice-actors/{voice_actor_id}/get-voice")
        async def get_voice_handler(voice_actor_id: str, x_audio_format: str, url: str = None, download: str = None, cache_key: str = None):
            nijivoice_resp = await self.stream_source.fetch_stream(
                voice_actor_id=voice_actor_id,
                url=url,
                download=download,
                cache_key=cache_key,
                audio_format=x_audio_format
            )
            return StreamingResponse(nijivoice_resp, media_type=f"audio/{x_audio_format}")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        gateway_base_url = f"{request.base_url.scheme}://{request.base_url.netloc}{self.prefix}"

        payload = {
            "script": tts_request.text,
            "speed": str(self.speeds.get(tts_request.speaker, "1.0")),
            "format": x_audio_format if x_audio_format == "mp3" else "wav"
        }

        resp_json = await self.stream_source.generate_voice(tts_request.speaker, payload, gateway_base_url, x_audio_format, overwrite_download_urls=False)

        nijivoice_resp = await self.stream_source.fetch_stream(
            voice_actor_id=tts_request.speaker,
            url=resp_json["generatedVoice"]["audioFileUrl"],
            download=False,
            cache_key=self.stream_source.get_cache_key(x_audio_format, tts_request.speaker, payload),
            audio_format=x_audio_format
        )

        return StreamingResponse(nijivoice_resp, media_type=f"audio/{x_audio_format}")
