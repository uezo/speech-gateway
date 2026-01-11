import json
from typing import Dict, Any
from . import SpeechGateway, UnifiedTTSRequest
from ..performance_recorder import PerformanceRecorder
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class OpenAIGateway(SpeechGateway):
    def __init__(
        self,
        *,
        api_key: str = None,
        model: str = "tts-1",
        instructions: str = None,
        base_url: str = None,
        cache_dir: str = "openai_cache",
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
            base_url=base_url or "https://api.openai.com/v1",
            original_tts_method="POST",
            original_tts_path="/audio/speech",
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
        self.model = model
        self.instructions = instructions

    async def from_tts_request(self, tts_request: UnifiedTTSRequest) -> Dict[str, Any]:
        if "azure" in self.base_url:
            url = self.base_url
            headers = {"api-key": self.api_key}
        else:
            url = self.base_url + self.original_tts_path
            headers = {"Authorization": f"Bearer {self.api_key}"}

        request_json = {
            "method": self.original_tts_method,
            "url": url,
            "headers": headers,
            "json": {
                "model": self.model,
                "voice": tts_request.speaker,
                "input": tts_request.text,
                "speed": tts_request.speed or 1.0,
                "response_format": tts_request.audio_format
            }
        }
        if self.instructions:
            request_json["json"]["instructions"] = self.instructions
        
        return request_json

    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        request_json: dict = json.loads(body.decode("utf-8"))

        tts_request = UnifiedTTSRequest(
            text=request_json.get("input"),
            speaker=request_json.get("voice"),
            speed=request_json.get("speed", 1.0),
            audio_format=request_json.get("response_format", "wav"),
        )

        return tts_request
