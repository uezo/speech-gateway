from abc import ABC, abstractmethod
import logging
from fastapi import Request, APIRouter
from fastapi.responses import Response
import httpx
from ..source import StreamSource

logger = logging.getLogger(__name__)


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
        stream_source: StreamSource,
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
    def register_endpoint(self, router: APIRouter, stream_source: StreamSource):
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

    def get_router(self) -> APIRouter:
        router = APIRouter()
        self.register_endpoint(router, self.stream_source)
        router.add_api_route(
            "/{path:path}",
            self.passthrough_handler,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
            include_in_schema=False
        )

        return router

    async def shutdown(self):
        await self.stream_source.close()
