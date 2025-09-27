from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..performance_recorder import PerformanceRecorder, SQLitePerformanceRecorder
from ..source.openai_speech import OpenAIStreamSource


class OpenAIGateway(SpeechGateway):
    def __init__(self, *, stream_source: OpenAIStreamSource = None, api_key: str = None, model: str = "tts-1", speed: float = 1.0, instructions: str = None, base_url: str = None, cache_dir: str = None, performance_recorder: PerformanceRecorder = None, debug = False):
        self.stream_source: OpenAIStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=OpenAIStreamSource(
                    api_key=api_key,
                    base_url=base_url or "https://api.openai.com/v1",
                    cache_storage=FileCacheStorage(cache_dir=cache_dir or "openai_cache"),
                    format_converters={},
                    performance_recorder=performance_recorder or SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
            self.model = model
            self.speed = speed
            self.instructions = instructions

    def register_endpoint(self, router: APIRouter):
        @router.post("/audio/speech")
        async def synthesis_handler(request: Request, x_audio_format: str = None):
            request_json = await request.json()

            if x_audio_format:
                if x_audio_format in ["mp3", "opus", "aac", "flac", "wav", "pcm"]:
                    request_json["response_format"] = x_audio_format
                else:
                    # Set wave to convert to other format later
                    request_json["response_format"] = "wav"
            else:
                x_audio_format = request_json.get("response_format", "mp3")

            stream_resp = await self.stream_source.fetch_stream(
                request_json=request_json,
                audio_format=x_audio_format
            )
            return StreamingResponse(stream_resp, media_type=f"audio/{x_audio_format}")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        request_json = {
            "model": self.model,
            "voice": tts_request.speaker,
            "input": tts_request.text,
            "speed": tts_request.speed or self.speed,
            "instructions": self.instructions,
            "response_format": x_audio_format
        }

        stream_resp = await self.stream_source.fetch_stream(
            audio_format=x_audio_format,
            request_json=request_json,
        )
        return StreamingResponse(stream_resp, media_type=f"audio/{x_audio_format}")
