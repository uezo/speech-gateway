from abc import ABC, abstractmethod
import logging
from time import time
from typing import AsyncIterator, Any, Dict
import httpx
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder

logger = logging.getLogger(__name__)


class StreamSourceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class StreamSource(ABC):
    def __init__(self,
        *,
        base_url: str,
        cache_storage: CacheStorage = None,
        format_converters: Dict[str, FormatConverter] = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        self.base_url = base_url
        self.cache_storage = cache_storage
        self.format_converters = format_converters
        self.http_client = httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections
            )
        )
        self.performance_recorder = performance_recorder
        self.debug = debug

    @abstractmethod
    def get_cache_key(self, audio_format: str, **kwargs) -> str:
        pass

    @abstractmethod
    def parse_text(self, **kwargs) -> str:
        pass

    def get_converter(self, audio_format: str) -> FormatConverter:
        if self.format_converters:
            return self.format_converters.get(audio_format)

    @abstractmethod
    def make_stream_request(self, **kwargs) -> dict:
        pass

    async def fetch_stream_raw(self, http_request: Dict[str, Any]) -> AsyncIterator[bytes]:
        try:
            async with self.http_client.stream(**http_request) as audio_resp:
                if audio_resp.status_code != 200:
                    raise StreamSourceError(f"Stream from voice service failed: {audio_resp.status_code}")

                async for chunk in audio_resp.aiter_bytes(1024):
                    yield chunk

        except httpx.RequestError as ex:
            raise StreamSourceError(f"HTTP request failed: {ex}") from ex

    async def fetch_stream(self, audio_format: str, **kwargs) -> AsyncIterator[bytes]:
        start_time = time()
        cache_key = self.get_cache_key(audio_format, **kwargs)
        use_cache = self.cache_storage and await self.cache_storage.has_cache(cache_key)

        if use_cache:
            if self.debug:
                logger.info(f"[cache]: {cache_key}")
            # Get cache stream
            stream = self.cache_storage.fetch_cache_stream(cache_key)

        else:
            # Get stream from TTS service
            if self.debug:
                logger.info(f"[generate]: {cache_key}")
            http_request = self.make_stream_request(**kwargs)

            if self.debug:
                logger.info(f"Request to speech service: {http_request}")

            stream = self.fetch_stream_raw(http_request)

            # Convert format
            converter = self.get_converter(audio_format)
            if converter:
                stream = converter.convert(stream)

            # Write cache
            if self.cache_storage:
                stream = self.cache_storage.write_cache(stream, cache_key)

        # Response time
        if self.performance_recorder:
            stream = self.record_time(
                stream,
                cache_key=cache_key,
                text=self.parse_text(**kwargs),
                audio_format=audio_format,
                cached=use_cache,
                start_time=start_time
            )

        return stream

    async def record_time(
        self,
        input_stream: AsyncIterator[bytes],
        *,
        cache_key: str,
        text: str,
        audio_format: str,
        cached: bool,
        start_time: float
    ) -> AsyncIterator[bytes]:
        async for chunk in input_stream:
            yield chunk

        self.performance_recorder.record(
            process_id=cache_key, source=self.__class__.__name__, text=text,
            audio_format=audio_format, cached=cached, elapsed=time() - start_time
        )

    async def close(self):
        await self.http_client.aclose()
