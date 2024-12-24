from . import StreamSource


class StyleBertVits2StreamSource(StreamSource):
    def get_cache_key(self, audio_format: str, query_params: dict, **kwargs) -> str:
        return f"{hash(str(query_params))}.{'mp3' if audio_format == 'mp3' else 'wav'}"

    def parse_text(self, query_params: dict, **kwargs) -> str:
        return query_params.get("text")

    def make_stream_request(self, query_params: dict, **kwargs):
        return {
            "method": "GET",
            "url": self.base_url + "/voice",
            "params": query_params,
        }
