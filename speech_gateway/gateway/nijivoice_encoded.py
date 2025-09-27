import base64
import io
import json
from typing import Dict
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, Response
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..performance_recorder import PerformanceRecorder, SQLitePerformanceRecorder
from ..source.nijivoice_encoded import NijiVoiceEncodedStreamSource


class NijiVoiceEncodedGateway(SpeechGateway):
    def __init__(self, *, stream_source: NijiVoiceEncodedStreamSource = None, api_key: str = None, speeds: Dict[str, float] = None, base_url: str = None, cache_dir: str = None, performance_recorder: PerformanceRecorder = None, debug = False):
        self.stream_source: NijiVoiceEncodedStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=NijiVoiceEncodedStreamSource(
                    api_key=api_key,
                    base_url=base_url or "https://api.nijivoice.com",
                    cache_storage=FileCacheStorage(cache_dir=cache_dir or "nijivoice_encoded_cache"),
                    format_converters={},
                    performance_recorder=performance_recorder or SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
        self.speeds = speeds or {}

    def register_endpoint(self, router: APIRouter):
        @router.post("/api/platform/v1/voice-actors/{voice_actor_id}/generate-encoded-voice")
        async def get_voice_handler(voice_actor_id: str, request: Request, x_audio_format: str = None):
            request_json = await request.json()

            if x_audio_format:
                if x_audio_format in ["mp3", "wav"]:
                    request_json["format"] = x_audio_format
                else:
                    # Set wave to convert to other format later
                    request_json["format"] = "wav"
            else:
                x_audio_format = request_json.get("format", "mp3")

            stream_resp = await self.stream_source.fetch_stream(
                voice_actor_id=voice_actor_id,
                audio_format=x_audio_format,
                request_json=request_json,
            )

            json_bytes = b""
            async for chunk in stream_resp:
                json_bytes += chunk

            return Response(content=json_bytes, media_type=f"application/json")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        request_json = {
            "script": tts_request.text,
            "speed": str(tts_request.speed) if tts_request.speed else str(self.speeds.get(tts_request.speaker, "1.0")),
            "format": x_audio_format if x_audio_format == "mp3" else "wav"
        }

        stream_resp = await self.stream_source.fetch_stream(
            voice_actor_id=tts_request.speaker,
            audio_format=x_audio_format,
            request_json=request_json,
        )

        json_bytes = b""
        async for chunk in stream_resp:
            json_bytes += chunk
        response_json = json.loads(json_bytes)
        base64_audio = response_json["generatedVoice"]["base64Audio"]
        audio_bytes = base64.b64decode(base64_audio)

        return StreamingResponse(io.BytesIO(audio_bytes), media_type=f"audio/{x_audio_format}")
