from abc import ABC, abstractmethod


class FormatConverter(ABC):
    @abstractmethod
    async def convert(self, input_bytes: bytes) -> bytes:
        pass


class FormatConverterError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


from .mp3 import MP3Converter
