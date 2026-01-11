from typing import Dict, Any
from . import SpeechGateway, UnifiedTTSRequest
from ..performance_recorder import PerformanceRecorder
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class VoicevoxGateway(SpeechGateway):
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:50021",
        style_mapper: dict = None,
        cache_dir: str = "voicevox_cache",
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
            base_url=base_url,
            original_tts_method="POST",
            original_tts_path="/synthesis",
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
        self.style_mapper = style_mapper or {}

    async def from_tts_request(self, tts_request: UnifiedTTSRequest) -> Dict[str, Any]:
        speaker = tts_request.speaker

        # Apply style
        if tts_request.style is not None and (styles_for_speaker := self.style_mapper.get(tts_request.speaker)):
            for k, v in styles_for_speaker.items():
                if k.lower() == tts_request.style.lower():
                    speaker = v
                    break

        response = await self.http_client.post(
            url=f"{self.base_url}/audio_query",
            params={"speaker": speaker, "text": tts_request.text}
        )
        response.raise_for_status()
        audio_query = response.json()

        if tts_request.speed:
            audio_query["speedScale"] = tts_request.speed

        return {
            "method": self.original_tts_method,
            "url": self.base_url + self.original_tts_path,
            "params": {"speaker": speaker},
            "json": audio_query
        }

    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        tts_request = UnifiedTTSRequest(
            text=params["speaker"] + "_" + body.decode("utf-8"),  # For cache key and performance log
            audio_format="wav",
        )
        return tts_request
