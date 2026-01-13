from typing import Dict, List
import httpx
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from . import SpeechGateway, UnifiedTTSRequest, UnifiedTTSResponse
from ..performance_recorder import PerformanceRecorder


class DummyPerformanceRecorder(PerformanceRecorder):
    def record(
        self,
        *,
        process_id: str,
        source: str = None,
        text: str = None,
        audio_format: str = None,
        cached: int = 0,
        elapsed: float = None,
    ):
        pass

    def close(self):
        pass


class UnifiedGateway(SpeechGateway):
    def __init__(
        self,
        *,
        api_key: str = None,
        default_gateway: SpeechGateway = None,
        default_language: str = "ja-JP",
        debug = False
    ):
        super().__init__(performance_recorder=DummyPerformanceRecorder(), debug=debug)
        self.api_key = api_key
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

    async def tts(self, tts_request: UnifiedTTSRequest) -> UnifiedTTSResponse:
        gateway = self.get_gateway(tts_request)
        if not gateway:
            raise Exception("No gateways found.")

        if not tts_request.speaker:
            tts_request.speaker = self.default_speakers.get(gateway)

        return await gateway.tts(tts_request)

    def api_key_auth(self, credentials: HTTPAuthorizationCredentials):
        if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key",
            )
        return credentials.credentials

    def get_router(self) -> APIRouter:
        router = APIRouter()
        self.register_endpoint(router)
        return router

    def register_endpoint(self, router: APIRouter):
        bearer_scheme = HTTPBearer(auto_error=False)

        @router.post("/tts")
        async def post_tts(
            tts_request: UnifiedTTSRequest,
            credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
        ):
            if self.api_key:
                self.api_key_auth(credentials)

            gateway = self.get_gateway(tts_request)

            if not gateway:
                raise HTTPException(status_code=404, detail="No gateway found.")
            
            if not tts_request.speaker:
                tts_request.speaker = self.default_speakers.get(gateway)

            return await gateway.unified_tts_handler(tts_request)

        @router.delete("/cache")
        async def delete_cache(
            service_name: str,
            credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
        ):
            if self.api_key:
                self.api_key_auth(credentials)

            if gateway := self.service_map.get(service_name):
                await gateway.cache_storage.clear_all_cache()
                return JSONResponse(content={"result": f"Cache cleard for {service_name}"})
            else:
                return JSONResponse(content={"error": f"Gateway not found: {service_name}"}, status_code=404)

    def from_tts_request(self, tts_request: UnifiedTTSRequest) -> httpx.Request:
        pass

    def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        pass

    async def shutdown(self):
        for _, gw in self.service_map.items():
            try:
                await gw.shutdown()
            except:
                pass
