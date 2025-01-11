from . import StreamSource
from typing import Dict
from ..cache import CacheStorage
from ..cache.file import FileCacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class OpenAIStreamSource(StreamSource):
    def __init__(self,
        *,
        api_key: str = None,
        base_url: str = "https://api.openai.com/v1",
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
            cache_storage=cache_storage or FileCacheStorage(cache_dir="openai_cache"),
            format_converters=format_converters,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.base_url = base_url
        self.api_key = api_key

    def get_cache_key(self, audio_format: str, request_json: dict, **kwargs) -> str:
        if not audio_format:
            audio_format = request_json.get("response_format", "mp3")
        return f"{hash(str(request_json))}.{audio_format}"

    def parse_text(self, request_json: dict, **kwargs) -> str:
        return request_json.get("input")

    def make_stream_request(self, request_json: dict, **kwargs):
        return {
            "method": "POST",
            "url": self.base_url + "/audio/speech",
            "headers": {"Authorization": f"Bearer {self.api_key}"},
            "json": request_json
        }
