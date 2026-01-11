from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Dict, Any
from . import SpeechGateway, UnifiedTTSRequest
from ..performance_recorder import PerformanceRecorder
from ..cache import CacheStorage
from ..converter import FormatConverter
from ..performance_recorder import PerformanceRecorder


class CoefontGateway(SpeechGateway):
    def __init__(
        self,
        *,
        access_key: str = None,
        access_secret: str = None,
        base_url: str = None,
        cache_dir: str = "coefont_cache",
        cache_storage: CacheStorage = None,
        format_converters: Dict[str, FormatConverter] = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        follow_redirects: bool = False,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        super().__init__(
            base_url=base_url or "https://api.coefont.cloud/v2",
            original_tts_method="POST",
            original_tts_path="/text2speech",
            cache_dir=cache_dir,
            cache_storage=cache_storage,
            format_converters=format_converters,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            follow_redirects=follow_redirects,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.access_key = access_key
        self.access_secret = access_secret
        self.http_client.follow_redirects = True

    async def from_tts_request(self, tts_request: UnifiedTTSRequest) -> Dict[str, Any]:
        request_json = {
            "text": tts_request.text,
            "coefont": tts_request.speaker,
            "format": tts_request.audio_format
        }
        if tts_request.speed:
            request_json["speed"] = tts_request.speed

        date = str(int(datetime.now(tz=timezone.utc).timestamp()))
        data = json.dumps(request_json)

        signature = hmac.new(
            key=bytes(self.access_secret, "utf-8"),
            msg=(date+data).encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        return {
            "method": "POST",
            "url": self.base_url + "/text2speech",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": self.access_key,
                "X-Coefont-Date": date,
                "X-Coefont-Content": signature
            },
            "data": data
        }

    async def to_tts_request(self, body: bytes, headers: dict, params: dict) -> UnifiedTTSRequest:
        request_json: dict = json.loads(body.decode("utf-8"))

        tts_request = UnifiedTTSRequest(
            text=request_json.get("text"),
            speaker=request_json.get("coefont"),
            speed=request_json.get("speed", 1.0),
            audio_format=request_json.get("format", "wav")
        )

        return tts_request
