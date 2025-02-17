from typing import Dict
from . import StreamSource
from ..cache import CacheStorage
from ..cache.file import FileCacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class NijiVoiceEncodedStreamSource(StreamSource):
    def __init__(self,
        *,
        api_key: str = None,
        base_url: str = "https://api.nijivoice.com",
        cache_storage: CacheStorage = None,
        format_converters: Dict[str, FormatConverter] = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        super().__init__(
            base_url=base_url,
            cache_storage=cache_storage or FileCacheStorage(cache_dir="nijivoice_encoded_cache"),
            format_converters=format_converters,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.base_url = base_url
        self.api_key = api_key

    def get_cache_key(self, audio_format: str, voice_actor_id: str, request_json: dict, **kwargs) -> str:
        if not audio_format:
            audio_format = request_json.get("format", "mp3")
        return f"{voice_actor_id}_{hash(str(request_json))}.{audio_format}.json"

    def parse_text(self, request_json: dict, **kwargs) -> str:
        return request_json.get("script")

    def make_stream_request(self, voice_actor_id: str, request_json: dict, **kwargs):
        return {
            "method": "POST",
            "url": self.base_url + f"/api/platform/v1/voice-actors/{voice_actor_id}/generate-encoded-voice",
            "headers": {"x-api-key": self.api_key},
            "json": request_json
        }
