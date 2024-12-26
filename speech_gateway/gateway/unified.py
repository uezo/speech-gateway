from typing import Dict
from fastapi import HTTPException
from fastapi import Request, APIRouter
from . import SpeechGateway, UnifiedTTSRequest


class UnifiedGateway(SpeechGateway):
    def __init__(self, *, default_gateway: SpeechGateway = None, debug = False):
        super().__init__(stream_source=None, debug=debug)
        self.service_map: Dict[str, SpeechGateway] = {}
        self.default_gateway: SpeechGateway = default_gateway

    def add_gateway(self, service_name: str, gateway: SpeechGateway, default: bool = False):
        self.service_map[service_name] = gateway
        if default:
            self.default_gateway = gateway

    def get_gateway(self, service_name: str = None) -> SpeechGateway:
        if service_name:
            return self.service_map.get(service_name)
        elif self.default_gateway:
            return self.default_gateway

    def get_router(self) -> APIRouter:
        router = APIRouter()
        self.register_endpoint(router)
        return router

    def register_endpoint(self, router: APIRouter):
        @router.post("/tts")
        async def post_tts(request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
            gateway = self.get_gateway(tts_request.service_name)

            if not gateway:
                raise HTTPException(status_code=404, detail="No gateway found.")

            return await gateway.unified_tts_handler(request, tts_request, x_audio_format)

    async def shutdown(self):
        pass
