from typing import Dict, Any
from . import SpeechGateway, UnifiedTTSRequest
from ..performance_recorder import PerformanceRecorder
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class AzureGateway(SpeechGateway):
    def __init__(
        self,
        *,
        api_key: str = None,
        region: str = None,
        base_url: str = None,
        language: str = "ja-JP",
        cache_dir: str = "azure_cache",
        cache_storage: CacheStorage = None,
        format_converters: Dict[str, FormatConverter] = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        follow_redirects: bool = False,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        super().__init__(
            base_url=(base_url or "https://{region}.tts.speech.microsoft.com").format(region=region),
            original_tts_method="POST",
            original_tts_path="/cognitiveservices/v1",
            cache_dir=cache_dir,
            cache_storage=cache_storage,
            format_converters=format_converters,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            follow_redirects=follow_redirects,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.api_key = api_key
        self.default_language = language

    async def from_tts_request(self, tts_request: UnifiedTTSRequest) -> Dict[str, Any]:
        # Speed
        if tts_request.speed:
            speed_percentage = (tts_request.speed - 1.0) * 100
        else:
            speed_percentage = 0

        # Build SSML
        if tts_request.extra_data and tts_request.extra_data.get("ssml"):
            ssml_text = tts_request.extra_data.get("ssml")
        else:
            ssml_text = f"<speak version='1.0' xml:lang='{tts_request.language or self.default_language}'><voice xml:lang='{tts_request.language or self.default_language}' name='{tts_request.speaker}'><prosody rate='{speed_percentage:+.2f}%'>{tts_request.text}</prosody></voice></speak>"

        # Audio format
        if tts_request.audio_format == "wav":
            azure_audio_format = "riff-16khz-16bit-mono-pcm"
        elif tts_request.audio_format == "mp3":
            azure_audio_format = "audio-16khz-32kbitrate-mono-mp3"
        else:
            azure_audio_format = tts_request.audio_format

        return {
            "method": self.original_tts_method,
            "url": self.base_url + self.original_tts_path,
            "headers": {
                "X-Microsoft-OutputFormat": azure_audio_format,
                "Content-Type": "application/ssml+xml",
                "Ocp-Apim-Subscription-Key": self.api_key,
            },
            "data": ssml_text.encode("utf-8")
        }

    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        tts_request = UnifiedTTSRequest(
            text=body.decode("utf-8"),  # For cache key and performance log
            audio_format=headers.get("x-microsoft-outputformat"),
        )
        return tts_request
