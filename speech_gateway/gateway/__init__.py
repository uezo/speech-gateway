from abc import ABC, abstractmethod
import hashlib
import logging
from time import time
from typing import Any, Dict
from uuid import uuid4
import httpx
from fastapi import Request, APIRouter
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from ..cache import CacheStorage, FileCacheStorage
from ..converter import FormatConverter, MP3Converter
from ..performance_recorder import PerformanceRecorder, SQLitePerformanceRecorder

logger = logging.getLogger(__name__)


class UnifiedTTSRequest(BaseModel):
    text: str = Field(..., description="The text to be synthesized into speech.", example="hello")
    speaker: str = Field(
        None, 
        description="The unique identifier for the voice in each speech service. "
                    "For Style-Bert-VITS2, specify as `{model_id}-{speaker_id}`. "
                    "If omitted, the default speaker of the speech service will be used.",
        example="888753761"
    )
    style: str = Field(
        None, 
        description="A predefined set of voice styles that includes `neutral`, `joy`, `angry`, `sorrow`, `fun`, and `surprised`. "
                    "These styles act as presets and must be mapped appropriately to the corresponding style identifiers in each speech service. "
                    "If omitted, no style will be applied.",
        example="neutral"
    )
    speed: float = Field(
        None,
        description="The speed of synthesized speech, where 1.0 is normal speed. "
                    "Values greater than 1.0 increase the speed (e.g., 1.5 is 50% faster), "
                    "and values less than 1.0 decrease the speed (e.g., 0.5 is 50% slower). "
                    "The acceptable range depends on each speech service.",
        example=1.0
    )
    service_name: str = Field(
        None, 
        description="The name of the service as specified in `add_gateway`. "
                    "If omitted, the default gateway will be used.",
        example="aivisspeech",
    )
    language: str = Field(
        None,
        description="The language. The corresponding text-to-speech service will be used. "
                    "Specify the language code in ISO639-1 format combined with the country code using a hyphen."
                    "If omitted, the default gateway will be used.",
        example="en-US",
    )
    audio_format: str = Field(
        "wav",
        description="The audio format of the synthesized speech (e.g., 'wav', 'mp3').",
        example="wav",
    )
    extra_data: Dict[str, Any] = Field(
        None,
        description="Additional service-specific data that can be passed to the TTS service. "
                    "The structure and supported keys depend on each speech service.",
        example={"pitch": 1.0, "volume": 1.0},
    )


class SpeechGateway(ABC):
    HOP_BY_HOP_HEADERS = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    def __init__(
        self,
        *,
        base_url: str = None,
        original_tts_path: str = None,
        original_tts_method: str = None,
        cache_dir: str = None,
        cache_storage: CacheStorage = None,
        format_converters: Dict[str, FormatConverter] = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        follow_redirects: bool = False,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        self.base_url = base_url
        self.original_tts_path = original_tts_path
        self.original_tts_method = original_tts_method
        if cache_storage:
            self.cache_storage = cache_storage
        elif cache_dir:
            self.cache_storage = FileCacheStorage(cache_dir=cache_dir)
        else:
            self.cache_storage = None
        self.format_converters = format_converters or {"mp3": MP3Converter()}
        self.performance_recorder = performance_recorder or SQLitePerformanceRecorder()
        self.http_client = httpx.AsyncClient(
            follow_redirects=follow_redirects,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections
            )
        )
        self.debug = debug

    def filter_headers(self, headers: httpx.Headers) -> dict:
        filtered = {}
        for k, v in headers.items():
            if k.lower() not in self.HOP_BY_HOP_HEADERS:
                filtered[k] = v
        return filtered

    def get_cache_key(self, tts_request: UnifiedTTSRequest) -> str:
        json_str = tts_request.model_dump_json()
        hash_value = hashlib.md5(json_str.encode()).hexdigest()
        return f"{hash_value}.{tts_request.audio_format}"

    @abstractmethod
    async def from_tts_request(self, tts_request: UnifiedTTSRequest) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        pass

    async def parse_audio_data(self, body: bytes, headers: dict) -> bytes:
        return body

    def get_converter(self, audio_format: str) -> FormatConverter:
        if self.format_converters:
            return self.format_converters.get(audio_format)

    async def passthrough_handler(self, request: Request, path: str):
        start_time = time()

        url = self.base_url if "?" in self.base_url else f"{self.base_url}/{path}"
        if request.query_params:
            url += f"?{request.query_params}"

        headers = dict(request.headers)
        headers.pop("host", None)
        body = await request.body()

        is_tts = request.method.lower() == self.original_tts_method.lower() and f"/{path}" == self.original_tts_path

        if is_tts:
            tts_request = await self.to_tts_request(
                body=body,
                headers=headers,
                params=dict(request.query_params)
            )
            cache_key = self.get_cache_key(tts_request)
            if cache_resp := await self.get_cache_response(cache_key):
                self.performance_recorder.record(
                    process_id=cache_key, source=self.__class__.__name__, text=tts_request.text,
                    audio_format=tts_request.audio_format, cached=1, elapsed=time() - start_time
                )
                return cache_resp

        r = await self.http_client.request(
            request.method,
            url,
            headers=headers,
            content=body
        )

        resp_headers = self.filter_headers(r.headers)

        if is_tts:
            if self.cache_storage:
                audio_data = await self.parse_audio_data(r.content, headers=resp_headers)
                await self.cache_storage.save_cache(data=audio_data, cache_key=cache_key)
            self.performance_recorder.record(
                process_id=cache_key, source=self.__class__.__name__, text=tts_request.text,
                audio_format=tts_request.audio_format, cached=0, elapsed=time() - start_time
            )
        else:
            self.performance_recorder.record(
                process_id=str(uuid4()), source=self.__class__.__name__, text=f"Proxy:[{request.method.upper()}] {url}",
                audio_format="N/A", cached=0, elapsed=time() - start_time
            )

        if self.debug:
            logger.info(f"Proxy: {request.method} /{path} -> {r.status_code}")

        return Response(content=r.content, status_code=r.status_code, headers=resp_headers)

    async def get_cache_response(self, cache_key: str) -> Response:
        if self.cache_storage:
            if cache := await self.cache_storage.get_cache(cache_key):
                if cache.path:
                    cache_resp = FileResponse(path=cache.path)
                elif cache.url:
                    _resp = await self.http_client.get(cache.url)
                    cache_resp = Response(content=_resp.content, media_type=_resp.headers.get("content-type"))
                else:
                    cache_resp = Response(content=cache.data, media_type=cache.mime_type)
                return cache_resp

        return None

    async def unified_tts_handler(self, tts_request: UnifiedTTSRequest):
        start_time = time()
        cache_key = self.get_cache_key(tts_request)

        if cache_resp := await self.get_cache_response(cache_key):
            self.performance_recorder.record(
                process_id=cache_key, source=self.__class__.__name__, text=tts_request.text,
                audio_format=tts_request.audio_format, cached=1, elapsed=time() - start_time
            )
            return cache_resp

        httpx_response = await self.http_client.request(
            **await self.from_tts_request(tts_request)
        )
        httpx_response.raise_for_status()
        audio_data = await self.parse_audio_data(
            body=httpx_response.content,
            headers=dict(httpx_response.headers)
        )

        if converter := self.get_converter(tts_request.audio_format):
            audio_data = await converter.convert(audio_data)

        if self.cache_storage:
            await self.cache_storage.save_cache(data=audio_data, cache_key=cache_key)

        self.performance_recorder.record(
            process_id=cache_key, source=self.__class__.__name__, text=tts_request.text,
            audio_format=tts_request.audio_format, cached=0, elapsed=time() - start_time
        )

        return Response(content=audio_data, media_type=f"audio/{tts_request.audio_format}")

    def get_router(self) -> APIRouter:
        router = APIRouter()
        router.add_api_route(
            "/{path:path}",
            self.passthrough_handler,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
            include_in_schema=False
        )
        return router

    async def shutdown(self):
        await self.http_client.aclose()
