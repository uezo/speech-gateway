from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..performance_recorder import SQLitePerformanceRecorder
from ..source.openai_speech import OpenAIStreamSource


class OpenAIGateway(SpeechGateway):
    def __init__(self, *, stream_source: OpenAIStreamSource = None, api_key: str = None, model: str = "tts-1", speed: float = 1.0, base_url: str = None, debug = False):
        self.stream_source: OpenAIStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=OpenAIStreamSource(
                    api_key=api_key,
                    base_url=base_url or "https://api.openai.com/v1",
                    cache_storage=FileCacheStorage(cache_dir="openai_cache"),
                    performance_recorder=SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
            self.model = model
            self.speed = speed

    def register_endpoint(self, router: APIRouter):
        @router.post("/audio/speech")
        async def synthesis_handler(request: Request, x_audio_format: str = None):
            request_json = await request.json()

            if x_audio_format:
                audio_format = x_audio_format
            elif request_json.get("response_format"):
                audio_format = request_json["response_format"]
            else:
                audio_format = "wav"
            request_json["response_format"] = audio_format

            # NOTE: audio_format and request_json["response_format"] are always same here
            stream_resp = await self.stream_source.fetch_stream(
                audio_format=audio_format,
                request_json=request_json
            )
            return StreamingResponse(stream_resp, media_type=f"audio/{audio_format}")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        request_json = {
            "model": self.model,
            "voice": tts_request.speaker,
            "input": tts_request.text,
            "speed": self.speed,
            "response_format": x_audio_format
        }

        stream_resp = await self.stream_source.fetch_stream(
            audio_format=x_audio_format,
            request_json=request_json,
        )
        return StreamingResponse(stream_resp, media_type=f"audio/{x_audio_format}")
