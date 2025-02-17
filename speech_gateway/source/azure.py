from . import StreamSource
from typing import Dict
from ..cache import CacheStorage
from ..cache.file import FileCacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class AzureStreamSource(StreamSource):
    def __init__(self,
        *,
        api_key: str = None,
        region: str = None,
        base_url: str = "https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
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
            cache_storage=cache_storage or FileCacheStorage(cache_dir="azure_cache"),
            format_converters=format_converters,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.api_key = api_key
        self.region = region

    def get_cache_key(self, audio_format: str, encoded_ssml: bytes, **kwargs) -> str:
        return f"{hash(encoded_ssml)}.{audio_format or 'wav'}"

    def parse_text(self, encoded_ssml: bytes, **kwargs) -> str:
        return encoded_ssml.decode("utf-8")

    def make_stream_request(self, encoded_ssml: bytes, azure_audio_format: str, **kwargs):
        return {
            "method": "POST",
            "url": self.base_url.format(region=self.region),
            "headers": {
                "X-Microsoft-OutputFormat": azure_audio_format,
                "Content-Type": "application/ssml+xml",
                "Ocp-Apim-Subscription-Key": self.api_key
            },
            "data": encoded_ssml
        }
