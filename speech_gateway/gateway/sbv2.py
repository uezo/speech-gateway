from typing import Dict, Any
from . import SpeechGateway, UnifiedTTSRequest
from ..performance_recorder import PerformanceRecorder
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class StyleBertVits2Gateway(SpeechGateway):
    def __init__(
        self,
        *,
        base_url: str,
        style_mapper: dict = None,
        cache_dir: str = "sbv2_cache",
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
            original_tts_method="GET",
            original_tts_path="/voice",
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
        if tts_request.extra_data:
            for k, v in tts_request.extra_data.items():
                if v is not None:
                    query_params[k] = v

        return {
            "method": self.original_tts_method,
            "url": self.base_url + self.original_tts_path,
            "params": query_params
        }

    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        tts_request = UnifiedTTSRequest(
            text=params.get("text"),
            speaker=f"{params.get('model_id', '0')}-{params.get('speaker_id', '0')}",
            audio_format="wav",
        )

        if style := params.get("style"):
            tts_request.style = style
        if speed := params.get("speed"):
            tts_request.speed = speed

        return tts_request
