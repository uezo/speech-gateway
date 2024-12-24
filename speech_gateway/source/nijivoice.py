from time import time
import urllib.parse
import httpx
from . import StreamSource, StreamSourceError
from ..cache import CacheStorage
from ..cache.file import FileCacheStorage
from ..performance_recorder import PerformanceRecorder


class NijiVoiceStreamSource(StreamSource):
    def __init__(self,
        *,
        api_key: str = None,
        base_url: str = "https://api.nijivoice.com",
        cache_storage: CacheStorage = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 10.0,
        performance_recorder: PerformanceRecorder = None,
        debug: bool = False
    ):
        super().__init__(
            base_url=base_url,
            cache_storage=cache_storage or FileCacheStorage(cache_dir="nijivoice_cache"),
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            timeout=timeout,
            performance_recorder=performance_recorder,
            debug=debug
        )
        self.base_url = base_url
        self.api_key = api_key

    def get_cache_key(self, audio_format: str, voice_actor_id: str = None, payload: dict = None, cache_key: str = None, **kwargs) -> str:
        if cache_key:
            return cache_key

        return f"{voice_actor_id}_{hash(str(payload))}.{'wav' if audio_format == 'wav' else 'mp3'}"

    def parse_text(self, **kwargs) -> str:
        return None

    def get_converter(self, audio_format: str):
        return None

    def make_stream_request(self, url: str, **kwargs):
        return {
            "method": "GET",
            "url": url,
        }

    async def generate_voice(self, voice_actor_id: str, payload: dict, gateway_base_url: str):
        start_time = time()
        audio_format = payload.get("format", "mp3")
        cache_key = self.get_cache_key(audio_format, voice_actor_id, payload)
        use_cache = self.cache_storage and await self.cache_storage.has_cache(cache_key)

        # Return cache info if cached
        if use_cache:
            gateway_voice_url = f"{gateway_base_url}/api/platform/v1/voice-actors/{voice_actor_id}/get-voice?cache_key={cache_key}&x_audio_format={audio_format}"
            data = {"generatedVoice": {
                "audioFileUrl": gateway_voice_url,
                "audioFileDownloadUrl": gateway_voice_url + "&download=true"
            }}

        else:
            try:
                # Generate voice
                url = f"{self.base_url}/api/platform/v1/voice-actors/{voice_actor_id}/generate-voice"
                headers = {
                    "x-api-key": self.api_key,
                    "content-type": "application/json"
                }
                url_resp = await self.http_client.post(url, headers=headers, json=payload)
                if url_resp.status_code != 200:
                    raise StreamSourceError(f"NijiVoice generate voice failed: {url_resp.status_code}")

                # Get voice URL
                data = url_resp.json()
                audio_file_url = data.get("generatedVoice", {}).get("audioFileUrl")
                encoded_audio_file_url = urllib.parse.quote(audio_file_url, safe='')

                # Overwrite URLs
                gateway_voice_url = (
                    f"{gateway_base_url}/api/platform/v1/voice-actors/{voice_actor_id}/get-voice"
                    f"?url={encoded_audio_file_url}&cache_key={cache_key}&x_audio_format={audio_format}"
                )
                data["generatedVoice"]["audioFileUrl"] = gateway_voice_url
                data["generatedVoice"]["audioFileDownloadUrl"] = gateway_voice_url + "&download=true"

            except httpx.RequestError as ex:
                raise StreamSourceError(f"HTTP request failed: {ex}") from ex

        # Performance record
        if self.performance_recorder:
            self.performance_recorder.record(
                process_id=cache_key, source=self.__class__.__name__, text=payload.get("script"),
                audio_format=audio_format, cached=use_cache, elapsed=time() - start_time
            )

        return data
