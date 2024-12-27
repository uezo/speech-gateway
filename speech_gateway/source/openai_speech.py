from . import StreamSource
from ..cache import CacheStorage
from ..cache.file import FileCacheStorage
from ..performance_recorder import PerformanceRecorder


class OpenAIStreamSource(StreamSource):
    def __init__(self,
        *,
        api_key: str = None,
        base_url: str = "https://api.openai.com/v1",
        cache_storage: CacheStorage = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        super().__init__(
            base_url=base_url,
            cache_storage=cache_storage or FileCacheStorage(cache_dir="openai_cache"),
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.base_url = base_url
        self.api_key = api_key

    def get_cache_key(self, audio_format: str, request_json: dict, **kwargs) -> str:
        audio_format = request_json.get("response_format", "wav")
        return f"{hash(str(request_json))}.{audio_format}"

    def get_converter(self, audio_format: str):
        return None

    def parse_text(self, request_json: dict, **kwargs) -> str:
        return request_json.get("input")

    def make_stream_request(self, request_json: dict, **kwargs):
        return {
            "method": "POST",
            "url": self.base_url + "/audio/speech",
            "headers": {"Authorization": f"Bearer {self.api_key}"},
            "json": request_json
        }
