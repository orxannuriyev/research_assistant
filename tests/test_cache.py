from __future__ import annotations

from src.config import Settings
from src.models import CacheEntry
from src.services.cache import CacheService, _make_key
from src.storage.cache_store import FilesystemCache, InMemoryCache
from ai.schemas import Source


def _entry() -> CacheEntry:
    return CacheEntry(
        source="wikipedia",
        query="What is photosynthesis?",
        sources=[
            Source(
                title="Photosynthesis",
                url="https://example.test/photosynthesis",
                snippet="A biological process.",
                origin="wikipedia",
            )
        ],
    )


def test_cache_key_normalizes_source_and_query() -> None:
    assert _make_key("WIKIPEDIA", "  What   Is Photosynthesis? ") == _make_key(
        "wikipedia", "what is photosynthesis?"
    )


def test_memory_cache_respects_ttl() -> None:
    settings = Settings(cache_backend="memory", cache_ttl_seconds=1)
    cache = CacheService(InMemoryCache(), settings)
    cache.set("wikipedia", "Q", _entry())
    assert cache.get("WIKIPEDIA", " q ") is not None


def test_disabled_cache_bypasses_reads_and_writes() -> None:
    settings = Settings(cache_backend="memory")
    cache = CacheService(InMemoryCache(), settings, enabled=False)
    cache.set("wikipedia", "Q", _entry())
    assert cache.get("wikipedia", "Q") is None


def test_filesystem_cache_round_trips(tmp_path) -> None:
    backend = FilesystemCache(str(tmp_path))
    backend.set("abc", _entry())
    restored = backend.get("abc")
    assert restored is not None
    assert restored.sources[0].title == "Photosynthesis"
