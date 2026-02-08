import json
import struct
from typing import Dict, Any
from . import SpeechGateway, UnifiedTTSRequest
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class AivisCloudGateway(SpeechGateway):
    def __init__(
        self,
        *,
        api_key: str = None,
        base_url: str = None,
        output_sampling_rate: int = 8000,
        style_mapper: dict = None,
        cache_dir: str = "aivis_cache",
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
            base_url=base_url or "https://api.aivis-project.com/v1",
            original_tts_method="POST",
            original_tts_path="/tts/synthesize",
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
        self.output_sampling_rate = output_sampling_rate
        self.style_mapper = style_mapper or {}

    async def from_tts_request(self, tts_request: UnifiedTTSRequest) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        request_json = {
            "model_uuid": tts_request.speaker,
            "text": tts_request.text,
            "output_format": tts_request.audio_format,
            "output_sampling_rate": self.output_sampling_rate,
            "output_audio_channels": "mono",
            "use_ssml": False,
        }

        if tts_request.speed:
            request_json["speaking_rate"] = tts_request.speed

        # Apply style
        if tts_request.style is not None and (styles_for_speaker := self.style_mapper.get(tts_request.speaker)):
            for k, v in styles_for_speaker.items():
                if k.lower() == tts_request.style.lower():
                    request_json["style_name"] = v
                    break

        # Additional data
        if tts_request.extra_data:
            for k, v in tts_request.extra_data.items():
                if v is not None:
                    request_json[k] = v

        return {
            "method": self.original_tts_method,
            "headers": headers,
            "url": self.base_url + self.original_tts_path,
            "json": request_json
        }

    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        request_json: dict = json.loads(body.decode("utf-8"))

        tts_request = UnifiedTTSRequest(
            text=request_json.get("text"),
            speaker=request_json.get("model_uuid"),
            audio_format=request_json.get("output_format", "wav")
        )

        if style := request_json.get("style_id"):
            tts_request.style = style
        if style := request_json.get("style_name"):
            tts_request.style = style
        if speed := request_json.get("speaking_rate"):
            tts_request.speed = speed

        return tts_request
