from . import StreamSource


class VoicevoxStreamSource(StreamSource):
    def get_cache_key(self, audio_format: str, speaker: str, audio_query: dict, **kwargs) -> str:
        return f"{speaker}_{hash(str(audio_query))}.{'mp3' if audio_format == 'mp3' else 'wav'}"

    def parse_text(self, audio_query: dict, **kwargs) -> str:
        return audio_query.get("kana")

    def make_stream_request(self, speaker: str, audio_query: dict, **kwargs):
        return {
            "method": "POST",
            "url": self.base_url + "/synthesis",
            "params": {"speaker": speaker},
            "json": audio_query
        }
