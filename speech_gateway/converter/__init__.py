from abc import ABC, abstractmethod
from typing import AsyncIterator


class FormatConverter(ABC):
    @abstractmethod
    async def convert(self, input_stream: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        pass


class FormatConverterError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


from .mp3 import MP3Converter
