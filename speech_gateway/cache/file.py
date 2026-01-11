from pathlib import Path
from typing import AsyncIterator, Union
import aiofiles
from . import Cache, CacheStorage, CacheStorageError


class FileCacheStorage(CacheStorage):
    def __init__(self, cache_dir: str = "voice_cache"):
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)

    async def has_cache(self, cache_key: str) -> bool:
        file_path = self.cache_dir / cache_key
        if not file_path.exists():
            return False

        if file_path.stat().st_size == 0:
            await self.delete_cache(cache_key)
            return False

        return True

    async def get_cache(self, cache_key: str) -> Union[Cache, None]:
        file_path = self.cache_dir / cache_key
        if not file_path.exists():
            return None
        return Cache(cache_key=cache_key, path=file_path)

    async def save_cache(self, data: bytes, cache_key: str):
        file_path = self.cache_dir / cache_key
        try:
            async with aiofiles.open(file_path, "wb") as file:
                await file.write(data)

        except Exception as ex:
            # Clean up partial file if it was created
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            raise CacheStorageError(f"Error during file save operation: {str(ex)}")

    async def delete_cache(self, cache_key: str) -> None:
        file_path = self.cache_dir / cache_key
        try:
            if file_path.exists():
                file_path.unlink()

        except Exception as ex:
            raise CacheStorageError(f"Error deleting cache file {file_path}: {str(ex)}")

    async def clear_all_cache(self) -> None:
        try:
            for file_path in self.cache_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()

        except Exception as ex:
            raise CacheStorageError(f"Error clearing cache directory {self.cache_dir}: {str(ex)}")
