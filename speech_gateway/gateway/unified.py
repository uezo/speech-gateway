from typing import Dict, List
from fastapi import HTTPException
from fastapi import Request, APIRouter
from . import SpeechGateway, UnifiedTTSRequest


class UnifiedGateway(SpeechGateway):
    def __init__(self, *, default_gateway: SpeechGateway = None, default_language: str = "ja-JP", debug = False):
        super().__init__(stream_source=None, debug=debug)
        self.service_map: Dict[str, SpeechGateway] = {}
        self.language_map: Dict[str, SpeechGateway] = {}
        self.default_speakers: Dict[SpeechGateway, str] = {}
        self.default_gateway: SpeechGateway = default_gateway
        self.default_language = default_language

    def add_gateway(self, service_name: str, gateway: SpeechGateway, *, languages: List[str] = None, default_speaker: str = None, default: bool = False):
        self.service_map[service_name] = gateway
        if languages:
            for lang in languages:
                self.language_map[lang] = gateway
        if default:
            self.default_gateway = gateway
            self.language_map[self.default_language] = gateway
        self.default_speakers[gateway] = default_speaker

    def get_gateway(self, tts_request: UnifiedTTSRequest):
        if tts_request.service_name:
            return self.service_map.get(tts_request.service_name)
        elif tts_request.language:
            return self.language_map.get(tts_request.language)
        elif self.default_gateway:
            return self.default_gateway
        return None

    def get_router(self) -> APIRouter:
        router = APIRouter()
        self.register_endpoint(router)
        return router

    def register_endpoint(self, router: APIRouter):
        @router.post("/tts")
        async def post_tts(request: Request, tts_request: UnifiedTTSRequest, x_audio_format: str = "wav"):
            gateway = self.get_gateway(tts_request)

            if not gateway:
                raise HTTPException(status_code=404, detail="No gateway found.")
            
            if not tts_request.speaker:
                tts_request.speaker = self.default_speakers.get(gateway)

            return await gateway.unified_tts_handler(request, tts_request, x_audio_format)

    async def shutdown(self):
        pass
