import urllib.parse
import httpx
from . import StreamSource, StreamSourceError


class VoicevoxStreamSource(StreamSource):
    def get_cache_key(self, audio_format: str, speaker: str, audio_query: dict, **kwargs) -> str:
        return f"{speaker}_{hash(str(audio_query))}.{audio_format or 'wav'}"

    def parse_text(self, audio_query: dict, **kwargs) -> str:
        return audio_query.get("kana")

    def make_stream_request(self, speaker: str, audio_query: dict, **kwargs):
        return {
            "method": "POST",
            "url": self.base_url + "/synthesis",
            "params": {"speaker": speaker},
            "json": audio_query
        }

    async def get_audio_query(self, speaker: str, text: str, **kwargs):
        try:
            url = f"{self.base_url}/audio_query"

            response = await self.http_client.post(url, params={"speaker": speaker, "text": text})
            response.raise_for_status()

            return response.json()

        except httpx.RequestError as ex:
            raise StreamSourceError(f"HTTP request failed: {ex}") from ex
