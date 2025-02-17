from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from . import SpeechGateway, UnifiedTTSRequest
from ..cache.file import FileCacheStorage
from ..performance_recorder import PerformanceRecorder, SQLitePerformanceRecorder
from ..source.azure import AzureStreamSource


class AzureGateway(SpeechGateway):
    def __init__(self, *, stream_source: AzureStreamSource = None, api_key: str = None, region: str = None, base_url: str = None, language: str = "ja-JP", cache_dir: str = None, performance_recorder: PerformanceRecorder = None, debug = False):
        self.stream_source: AzureStreamSource = None
        if stream_source:
            super().__init__(stream_source=stream_source, debug=debug)
        else:
            super().__init__(
                stream_source=AzureStreamSource(
                    api_key=api_key,
                    region=region,
                    base_url=base_url or "https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                    cache_storage=FileCacheStorage(cache_dir=cache_dir or "azure_cache"),
                    format_converters={},
                    performance_recorder=performance_recorder or SQLitePerformanceRecorder(),
                    debug=debug
                ),
                debug=debug
            )
        self.default_language = language

    def register_endpoint(self, router: APIRouter):
        @router.post("/cognitiveservices/v1")
        async def synthesis_handler(request: Request, x_audio_format: str = None):
            if x_audio_format == "wav":
                azure_audio_format = "riff-16khz-16bit-mono-pcm"
            elif x_audio_format == "mp3":
                azure_audio_format = "audio-16khz-32kbitrate-mono-mp3"
            else:
                azure_audio_format = request.headers["X-Microsoft-OutputFormat"]
                if "pcm" in azure_audio_format:
                    x_audio_format = "wav"
                else:
                    x_audio_format = "mp3"

            stream_resp = await self.stream_source.fetch_stream(
                encoded_ssml=await request.body(),
                azure_audio_format=azure_audio_format,
                audio_format=x_audio_format
            )
            return StreamingResponse(stream_resp, media_type=f"audio/{x_audio_format}")

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        if x_audio_format == "wav":
            azure_audio_format = "riff-16khz-16bit-mono-pcm"
        elif x_audio_format == "mp3":
            azure_audio_format = "audio-16khz-32kbitrate-mono-mp3"

        ssml_text = f"<speak version='1.0' xml:lang='{tts_request.language or self.default_language}'><voice xml:lang='{tts_request.language or self.default_language}' name='{tts_request.speaker}'>{tts_request.text}</voice></speak>"

        stream_resp = await self.stream_source.fetch_stream(
            encoded_ssml=ssml_text.encode("utf-8"),
            azure_audio_format=azure_audio_format,
            audio_format=x_audio_format
        )
        return StreamingResponse(stream_resp, media_type=f"audio/{x_audio_format}")
