"""Cache storage backends for the Research Assistant.

Architecture (OOP requirement)
-------------------------------
CacheBackend  — abstract base class
  ├── FilesystemCache  — persists entries as JSON files
  └── InMemoryCache    — keeps entries in a dict (good for tests)

Both classes are thread-safe for the asyncio event loop because:
  • FilesystemCache uses atomic write (temp-file + rename).
  • InMemoryCache is a plain dict — only one coroutine runs at a time.
"""

from __future__ import annotations

import abc
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from src.models import CacheEntry

logger = logging.getLogger(__name__)


class CacheBackend(abc.ABC):
    """Abstract base — defines the contract every cache must satisfy."""

    @abc.abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Return the cached entry for *key*, or None if missing / expired."""
        ...

    @abc.abstractmethod
    def set(self, key: str, entry: CacheEntry) -> None:
        """Store *entry* under *key*."""
        ...

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Remove the entry for *key* (no-op if absent)."""
        ...

    @abc.abstractmethod
    def clear(self) -> None:
        """Remove all entries."""
        ...


class FilesystemCache(CacheBackend):
    """Stores each cache entry as a JSON file under *cache_dir*.

    File name = ``<key>.json`` (key is assumed to be a safe filename, e.g.
    a hex digest produced by CacheService).
    """

    def __init__(self, cache_dir: str = ".cache") -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        logger.debug("FilesystemCache initialised at %s", self._dir.resolve())

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> Optional[CacheEntry]:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entry = CacheEntry.from_dict(data)
        except Exception as exc:
            logger.warning("Cache read error for key=%s: %s", key, exc)
            return None

        if entry.is_expired():
            logger.debug("Cache HIT but EXPIRED for key=%s", key)
            self.delete(key)
            return None

        logger.debug("Cache HIT for key=%s", key)
        return entry

    def set(self, key: str, entry: CacheEntry) -> None:
        path = self._path(key)
        # Atomic write: write to temp file then rename.
        try:
            fd, tmp = tempfile.mkstemp(dir=self._dir, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(entry.to_dict(), fh, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            logger.debug("Cache SET for key=%s", key)
        except Exception as exc:
            logger.error("Cache write error for key=%s: %s", key, exc)

    def delete(self, key: str) -> None:
        path = self._path(key)
        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Cache delete error for key=%s: %s", key, exc)

    def clear(self) -> None:
        for p in self._dir.glob("*.json"):
            try:
                p.unlink()
            except Exception:
                pass
        logger.debug("FilesystemCache cleared")


class InMemoryCache(CacheBackend):
    """Keeps all entries in a plain dict — fast, no I/O, lost on restart.

    Ideal for tests and --no-cache runs.
    """

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[CacheEntry]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry

    def set(self, key: str, entry: CacheEntry) -> None:
        self._store[key] = entry

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
