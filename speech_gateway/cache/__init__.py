from abc import ABC, abstractmethod
from typing import AsyncIterator, Any, Union


class Cache:
    def __init__(self, cache_key: str, path: str = None, url: str = None, data: Any = None, mime_type: str = None):
        self.cache_key = cache_key
        self.path = path
        self.url = url
        self.data = data
        self.mime_type = mime_type


class CacheStorage(ABC):
    @abstractmethod
    async def has_cache(self, cache_key: str) -> bool:
        pass

    @abstractmethod
    async def get_cache(self, cache_key: str) -> Union[Cache, None]:
        pass

    @abstractmethod
    async def save_cache(self, data: bytes, cache_key: str):
        pass


class CacheStorageError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


from .file import FileCacheStorage
