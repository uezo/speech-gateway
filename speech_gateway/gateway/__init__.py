from abc import ABC, abstractmethod
import logging
from fastapi import Request, APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
import httpx
from ..source import StreamSource

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
        stream_source: StreamSource = None,
        debug: bool = False
    ):
        self.stream_source = stream_source
        self.debug = debug

    def filter_headers(self, headers: httpx.Headers) -> dict:
        filtered = {}
        for k, v in headers.items():
            if k.lower() not in self.HOP_BY_HOP_HEADERS:
                filtered[k] = v
        return filtered

    @abstractmethod
    def register_endpoint(self, router: APIRouter):
        pass

    async def passthrough_handler(self, request: Request, path: str):
        url = f"{self.stream_source.base_url}/{path}"
        if request.query_params:
            url += f"?{request.query_params}"

        headers = dict(request.headers)
        headers.pop("host", None)
        body = await request.body()

        r = await self.stream_source.http_client.request(
            request.method,
            url,
            headers=headers,
            content=body
        )

        resp_headers = self.filter_headers(r.headers)

        if self.debug:
            logger.info(f"Proxy: {request.method} /{path} -> {r.status_code}")

        return Response(content=r.content, status_code=r.status_code, headers=resp_headers)

    async def unified_tts_handler(self, request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
        raise HTTPException(status_code=400, detail=f"This speech service doesn't support unified interface for now: {self.__class__.__name__}")

    def get_router(self) -> APIRouter:
        router = APIRouter()
        self.register_endpoint(router)
        router.add_api_route(
            "/{path:path}",
            self.passthrough_handler,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
            include_in_schema=False
        )

        return router

    async def shutdown(self):
        await self.stream_source.close()
