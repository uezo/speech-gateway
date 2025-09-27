from pathlib import Path
from typing import AsyncIterator
import aiofiles
from . import CacheStorage, CacheStorageError


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

    async def fetch_cache_stream(self, cache_key: str) -> AsyncIterator[bytes]:
        try:
            file_path = self.cache_dir / cache_key
            async with aiofiles.open(file_path, mode="rb") as file:
                while chunk := await file.read(1024):
                    yield chunk

        except Exception as ex:
            raise IOError(f"Error reading file {file_path}: {str(ex)}")

    async def write_cache(self, input_stream: AsyncIterator[bytes], cache_key: str) -> AsyncIterator[bytes]:
        file_path = self.cache_dir / cache_key
        try:
            async with aiofiles.open(file_path, "wb") as file:
                async for chunk in input_stream:
                    await file.write(chunk)
                    await file.flush()
                    yield chunk

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
