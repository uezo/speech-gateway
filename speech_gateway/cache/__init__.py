from abc import ABC, abstractmethod
from typing import AsyncIterator


class CacheStorage(ABC):
    @abstractmethod
    async def has_cache(self, cache_key: str) -> bool:
        pass

    @abstractmethod
    async def fetch_cache_stream(self, cache_key: str) -> AsyncIterator[bytes]:
        pass

    @abstractmethod
    async def write_cache(self, input_stream: AsyncIterator[bytes], cache_key: str) -> AsyncIterator[bytes]:
        pass


class CacheStorageError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


from .file import FileCacheStorage
