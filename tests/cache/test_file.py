import pytest
from speech_gateway.cache import FileCacheStorage


@pytest.fixture
def temp_cache_dir(tmp_path):
    # Create a temporary cache directory for testing
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def file_cache_storage(temp_cache_dir):
    # Create a FileCacheStorage instance using the temporary directory
    return FileCacheStorage(cache_dir=str(temp_cache_dir))


@pytest.mark.asyncio
async def test_has_cache(file_cache_storage, temp_cache_dir):
    # Test has_cache method
    cache_key = "test_file"
    file_path = temp_cache_dir / cache_key

    # Case 1: File does not exist
    assert not await file_cache_storage.has_cache(cache_key)

    # Case 2: File exists and has content
    file_path.write_text("test content")
    assert await file_cache_storage.has_cache(cache_key)

    # Case 3: File exists but is empty
    file_path.write_text("")
    assert not await file_cache_storage.has_cache(cache_key)
    assert not file_path.exists()  # Should be deleted


@pytest.mark.asyncio
async def test_get_cache(file_cache_storage, temp_cache_dir):
    # Test get_cache method
    cache_key = "test_file"
    file_path = temp_cache_dir / cache_key
    content = b"This is test content."
    file_path.write_bytes(content)

    result = await file_cache_storage.get_cache(cache_key)

    assert result.path == file_path
    assert file_path.read_bytes() == content


@pytest.mark.asyncio
async def test_save_cache(file_cache_storage, temp_cache_dir):
    # Test save_cache method
    cache_key = "test_file"
    file_path = temp_cache_dir / cache_key

    await file_cache_storage.save_cache(b"Part 1 Part 2", cache_key)

    assert file_path.exists()
    assert file_path.read_bytes() == b"Part 1 Part 2"


@pytest.mark.asyncio
async def test_delete_cache(file_cache_storage, temp_cache_dir):
    # Test delete_cache method
    cache_key = "test_file"
    file_path = temp_cache_dir / cache_key
    file_path.write_text("test content")

    await file_cache_storage.delete_cache(cache_key)
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_clear_all_cache(file_cache_storage, temp_cache_dir):
    # Test clear_all_cache method
    (temp_cache_dir / "file1").write_text("content1")
    (temp_cache_dir / "file2").write_text("content2")

    await file_cache_storage.clear_all_cache()

    assert len(list(temp_cache_dir.iterdir())) == 0
